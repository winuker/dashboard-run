# Dashboard PRO – Strava + IA + WhatsApp

Este proyecto genera un análisis diario de entrenamientos usando:

- Strava API
- OpenAI GPT‑5.5
- Twilio WhatsApp
- GitHub Actions
- Dashboard web estático

## 🚀 Funcionalidad

### 1. Refrescar análisis
Actualiza:
- Actividades recientes
- Métricas ATL / CTL / TSB
- Resumen semanal
- Plan generado por IA

### 2. Refrescar + WhatsApp
Hace lo mismo que el refresco normal, pero además:
- Envía el plan por WhatsApp
- Registra el estado del envío
- Actualiza el contador diario de mensajes

### 3. Dashboard web
Muestra:
- Gráficas de ritmo, distancia y carga
- Métricas clave
- Plan IA
- Estado del envío por WhatsApp
- Contador de mensajes enviados hoy

## ⚙️ Archivos importantes

| Archivo | Función |
|--------|---------|
| `plan_entreno_gpt5_v2.py` | Script principal |
| `dashboard_data.json` | Datos del dashboard |
| `refresh.yml` | Workflow GitHub Actions |
| `index.html` | Dashboard |
| `dashboard.js` | Lógica del dashboard |
| `style.css` | Estilos Apple Fitness |

## 🔐 Variables de entorno

Configurar en GitHub Secrets:

- `OPENAI_API_KEY`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`
- `TWILIO_SID`
- `TWILIO_TOKEN`
- `WHATSAPP_FROM`
- `WHATSAPP_TO`
- `GH_TOKEN`

## 📊 Contador de WhatsApp

El script mantiene un contador diario en:

