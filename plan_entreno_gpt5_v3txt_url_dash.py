import os
import json
import requests
from datetime import datetime
from openai import OpenAI
from twilio.rest import Client as TwilioClient
from auto_refresh import ensure_valid_token
from dotenv import load_dotenv
load_dotenv()


# ======================================
# CONFIGURACIÓN (VARIABLES DE ENTORNO)
# ======================================

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]

WHATSAPP_FROM = os.environ["WHATSAPP_FROM"]
WHATSAPP_TO = os.environ["WHATSAPP_TO"]

client = OpenAI(api_key=OPENAI_API_KEY)
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

# ======================================
# DATOS DEL ATLETA
# ======================================

ATHLETE_PROFILE = """
Objetivo:
- Media Maratón de Córdoba (29/11/2026)
- Sub 2 horas

Peso actual: 90 kg
Peso objetivo: 82 kg

Días de entrenamiento:
Lunes, Miércoles, Viernes, Domingo

LTHR: 168 ppm

Zonas:
Z1 <143
Z2 143-150
Z3 151-158
Z4 160-166
Z5 >166
"""


# ======================================
# STRAVA API
# ======================================

def get_recent_activities(n=20):
    tokens = ensure_valid_token()
    access_token = tokens["access_token"]

    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": n}

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise Exception(f"Error Strava API: {r.status_code}")

    return r.json()


# ======================================
# SIMPLIFICAR ACTIVIDAD
# ======================================

def simplify_activity(a):
    distance_km = a["distance"] / 1000
    time_min = a["moving_time"] / 60

    pace = time_min / distance_km if distance_km > 0 else 0

    return {
        "date": a["start_date_local"][:10],
        "type": a["type"],
        "distance_km": round(distance_km, 2),
        "duration_min": round(time_min, 1),
        "pace_min_km": round(pace, 2),
        "avg_hr": a.get("average_heartrate"),
        "max_hr": a.get("max_heartrate"),
        "elevation": a.get("total_elevation_gain", 0)
    }


# ======================================
# INTENSIDAD
# ======================================

def intensity_factor(hr):
    if hr is None:
        return 0.70
    if hr < 143:
        return 0.65
    elif hr <= 150:
        return 0.75
    elif hr <= 158:
        return 0.85
    elif hr <= 166:
        return 0.95
    else:
        return 1.05


# ======================================
# CARGA ENTRENAMIENTO
# ======================================

def training_load(a):
    return round(a["duration_min"] * intensity_factor(a["avg_hr"]))


# ======================================
# CTL / ATL / TSB
# ======================================

def calculate_form(activities):
    loads = [training_load(a) for a in activities]

    if not loads:
        return {"ATL": 0, "CTL": 0, "TSB": 0}

    atl = sum(loads[-7:]) / min(7, len(loads))
    ctl = sum(loads) / len(loads)
    tsb = ctl - atl

    return {
        "ATL": round(atl, 1),
        "CTL": round(ctl, 1),
        "TSB": round(tsb, 1)
    }


# ======================================
# RESUMEN GENERAL
# ======================================

def build_summary(activities):
    km = sum(a["distance_km"] for a in activities)
    time = sum(a["duration_min"] for a in activities)
    elev = sum(a["elevation"] for a in activities)

    hr_values = [a["avg_hr"] for a in activities if a["avg_hr"]]

    form = calculate_form(activities)

    return {
        "km_total": round(km, 1),
        "time_total_min": round(time, 1),
        "elevation_total": round(elev, 0),
        "avg_hr_global": round(sum(hr_values)/len(hr_values), 1) if hr_values else None,
        "ATL": form["ATL"],
        "CTL": form["CTL"],
        "TSB": form["TSB"]
    }


# ======================================
# PROMPT
# ======================================

def build_prompt(activities, summary):
    return f"""
{ATHLETE_PROFILE}

ENTRENAMIENTOS:
{json.dumps(activities, ensure_ascii=False, indent=2)}

INDICADORES:
{json.dumps(summary, ensure_ascii=False, indent=2)}

Interpretar:
- ATL = fatiga aguda
- CTL = carga crónica
- TSB = frescura

Tareas:

1. Estado actual del atleta
2. Riesgo de sobrecarga o lesión
3. Ritmo realista para sub 2h
4. Entreno de mañana
5. Plan de 7 días (4 sesiones)
6. Recomendaciones de recuperación y peso

Restricciones:
- No inventar datos
- Ser técnico
- Ser conciso
- Formato WhatsApp
"""


# ======================================
# OPENAI
# ======================================

def get_plan(prompt):
    resp = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "system",
                "content": """
Eres un entrenador de élite especializado en running,
fisiología del esfuerzo, TrainingPeaks y planificación de medias maratones.

Analizas carga, fatiga y rendimiento con precisión.

No seas genérico.
Justifica cada recomendación.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return resp.choices[0].message.content


# ======================================
# WHATSAPP
# ======================================

def send_whatsapp(text):
    max_len = 1500

    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    for i, part in enumerate(parts, 1):
        twilio_client.messages.create(
            body=f"Parte {i}\n\n{part}",
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
# ======================================
# SUBIR JSON A GITHUB
# ======================================

import base64

def upload_to_github(filepath, repo, branch, token):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"

    with open(filepath, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode("utf-8")

    # Obtener SHA si el archivo ya existe
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": "update dashboard data",
        "content": encoded,
        "branch": branch
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers={"Authorization": f"token {token}"}, json=data)

    if r.status_code not in [200, 201]:
        raise Exception(f"Error subiendo a GitHub: {r.text}")


# ======================================
# MAIN
# ======================================

def main():
    print("Obteniendo datos de Strava...")

    raw = get_recent_activities(20)

    activities = [
        simplify_activity(a)
        for a in raw
        if a.get("type") == "Run"
    ]

    print("Calculando métricas...")

    summary = build_summary(activities)

    print("Generando plan IA...")

    prompt = build_prompt(activities, summary)

    plan = get_plan(prompt)

    # ======================================
    # GUARDAR JSON PARA EL DASHBOARD
    # ======================================

    dashboard_data = {
        "activities": activities,
        "summary": summary,
        "plan": plan,
        "generated_at": datetime.now().isoformat()
    }

    with open("dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    # ======================================
    # SUBIR A GITHUB
    # ======================================

    upload_to_github(
        filepath="dashboard_data.json",
        repo=os.environ["REPO_NAME"],
        branch=os.environ["REPO_BRANCH"],
        token=os.environ["GH_TOKEN"]

    )

    # ======================================
    # ENVIAR WHATSAPP
    # ======================================

    print(plan)
    print("Enviando WhatsApp...")

    send_whatsapp(plan)

    # Enviar link del dashboard
    twilio_client.messages.create(
        body="📊 Dashboard actualizado:\nhttps://winuker.github.io/dashboard-run",
        from_=WHATSAPP_FROM,
        to=WHATSAPP_TO
    )

    print("✔ Listo")



if __name__ == "__main__":
    main()
