import os
import json
import requests
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from twilio.rest import Client as TwilioClient
from auto_refresh import ensure_valid_token
from dotenv import load_dotenv
load_dotenv()

# ======================================
# CONTROL ENVÍO WHATSAPP
# ======================================

SEND_WHATSAPP = os.getenv("SEND_WHATSAPP", "false") == "true"

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
# SISTEMA DE LOGS
# ======================================

def write_log(message):
    Path("logs").mkdir(exist_ok=True)
    log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# ======================================
# CONTADOR DE MENSAJES WHATSAPP
# ======================================

def load_whatsapp_counter():
    try:
        with open("whatsapp_counter.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}

    today = datetime.now().strftime("%Y-%m-%d")

    if data["date"] != today:
        return {"date": today, "count": 0}

    return data


def save_whatsapp_counter(counter):
    with open("whatsapp_counter.json", "w", encoding="utf-8") as f:
        json.dump(counter, f, ensure_ascii=False, indent=2)

# ======================================
# DATOS DEL ATLETA
# ======================================

ATHLETE_PROFILE = """
Objetivo:
- Media Maratón de Córdoba (29/11/2026)
- Sub 2 horas

Peso actual: 90 kg
Peso objetivo: 79 kg

Días de entrenamiento:
Lunes, Miércoles, Jueves, Sábado

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
            {"role": "user", "content": prompt}
        ]
    )

    return resp.choices[0].message.content

# ======================================
# WHATSAPP
# ======================================

def send_whatsapp(text):
    from twilio.base.exceptions import TwilioRestException

    max_len = 1500
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    try:
        for i, part in enumerate(parts, 1):
            twilio_client.messages.create(
                from_=WHATSAPP_FROM,
                body=f"Parte {i}\n\n{part}",
                to=WHATSAPP_TO
            )
        return "sent"

    except TwilioRestException as e:
        write_log(f"TwilioRestException: {e}")
        print("TwilioRestException:", e)
        return "error"

    except Exception as e:
        write_log(f"Exception en send_whatsapp: {e}")
        print("Exception en send_whatsapp:", e)
        return "error"


# ======================================
# MAIN
# ======================================

def main():
    write_log("=== EJECUCIÓN INICIADA ===")
    write_log(f"SEND_WHATSAPP = {SEND_WHATSAPP}")

    print("Obteniendo datos de Strava...")
    write_log("Obteniendo datos de Strava")

    raw = get_recent_activities(20)

    activities = [
        simplify_activity(a)
        for a in raw
        if a.get("type") == "Run"
    ]

    print("Calculando métricas...")
    write_log("Calculando métricas")

    summary = build_summary(activities)

    print("Generando plan IA...")
    write_log("Generando plan IA")

    prompt = build_prompt(activities, summary)
    plan = get_plan(prompt)

    # ======================================
    # ENVIAR WHATSAPP (solo si está activado)
    # ======================================

    print(plan)

    if SEND_WHATSAPP:
        print("Enviando WhatsApp...")
        write_log("Enviando WhatsApp...")

        whatsapp_status = send_whatsapp(plan)
        print("Estado WhatsApp:", whatsapp_status)
        write_log(f"Estado WhatsApp: {whatsapp_status}")

        # Contador
        counter = load_whatsapp_counter()
        if whatsapp_status == "sent":
            counter["count"] += 1
            save_whatsapp_counter(counter)
            write_log(f"Contador actualizado: {counter['count']} mensajes hoy")
        else:
            write_log("Contador no incrementado (no enviado)")

    else:
        print("WhatsApp desactivado para esta ejecución.")
        write_log("WhatsApp desactivado")
        whatsapp_status = "disabled"
        counter = load_whatsapp_counter()

    # ======================================
    # GUARDAR JSON PARA EL DASHBOARD
    # ======================================

    dashboard_data = {
        "activities": activities,
        "summary": summary,
        "plan": plan,
        "generated_at": datetime.now().isoformat(),
        "whatsapp_status": whatsapp_status,
        "whatsapp_count_today": counter["count"]
    }

    with open("dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    write_log("dashboard_data.json actualizado")
    write_log("=== EJECUCIÓN FINALIZADA ===\n")

    print("dashboard_data.json actualizado correctamente.")
    print("✔ Listo")

if __name__ == "__main__":
    main()
