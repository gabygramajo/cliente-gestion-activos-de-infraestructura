import os
import io
import json
import re
import pandas as pd
import requests
from pathlib import Path
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_PRODUCTION")
WEBHOOK_USER = os.getenv("WEBHOOK_USER")
WEBHOOK_PASS = os.getenv("WEBHOOK_PASS")

auth = None
if WEBHOOK_USER and WEBHOOK_PASS:
    auth = HTTPBasicAuth(WEBHOOK_USER, WEBHOOK_PASS)


# ---------------------------------------------------------
#  Limpia texto ↔ intenta extraer JSON
# ---------------------------------------------------------
def extraer_json(texto):
    if not isinstance(texto, str):
        return None

    texto = texto.replace("```json", "").replace("```", "").strip()

    # Intento directo
    try:
        return json.loads(texto)
    except:
        pass

    # Buscar bloque JSON dentro del texto
    match = re.search(r"\{[\s\S]*\}", texto)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    return None


# ---------------------------------------------------------
#  Interfaz estética
# ---------------------------------------------------------
def mostrar_banner():
    print("\n")
    print("╔════════════════════════════════════════╗")
    print("║     🧠 SIRA – Agente Inteligente       ║")
    print("╚════════════════════════════════════════╝\n")


# ---------------------------------------------------------
#  Manejo de respuestas de n8n
# ---------------------------------------------------------
def procesar_respuesta(resp):

    content_type = resp.headers.get("Content-Type", "")
    raw_text = resp.text.strip()

    # -----------------------------------
    # CASO EXCEL BINARIO
    # -----------------------------------
    if "application/vnd.openxmlformats" in content_type:

        download_dir = Path.home() / "Downloads"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filepath = download_dir / f"reporte_{timestamp}.xlsx"

        try:
            with open(filepath, "wb") as f:
                f.write(resp.content)

            print("\n✅ Archivo descargado correctamente:")
            print(f"📁 {filepath}\n")

            try:
                df = pd.read_excel(io.BytesIO(resp.content))
                print("📊 Vista previa:")
                print(df.head(10).to_string(index=False))
            except:
                print("⚠ No se pudo mostrar la vista previa del Excel.")

        except Exception as e:
            print(f"❌ Error al guardar el archivo: {e}")

        return

    # -----------------------------------
    # CASO JSON PURO
    # -----------------------------------
    if "application/json" in content_type:
        try:
            data = resp.json()
            return mostrar_mensaje_inteligente(data)
        except:
            pass

    # -----------------------------------
    # TEXTO → intentar JSON
    # -----------------------------------
    posible = extraer_json(raw_text)
    if posible:
        return mostrar_mensaje_inteligente(posible)

    # -----------------------------------
    # TEXTO SIMPLE (fallback)
    # -----------------------------------
    print("\n💬 Respuesta del servidor:")
    print(raw_text)

    # detección de acciones
    if "gmail" in raw_text.lower():
        print("📧 El correo fue enviado correctamente.")
    if "drive" in raw_text.lower():
        print("☁ Archivo subido a Drive.")

    return


# ---------------------------------------------------------
#  Mostrar JSON del agente de manera más linda
# ---------------------------------------------------------
def mostrar_mensaje_inteligente(data):

    mensaje = data.get("mensaje") or data.get("mensaje:") or None

    if mensaje:
        print("\n🤖", mensaje, "\n")

    # Si hay enlace a Drive
    if data.get("webViewLink"):
        print("🔗 Enlace Drive:", data["webViewLink"])

    # Si hay datos tipo tabla
    if isinstance(data.get("data"), list):
        df = pd.json_normalize(data["data"])
        print(df.to_string(index=False))

    return


# ---------------------------------------------------------
#  Enviar mensaje
# ---------------------------------------------------------
def enviar_mensaje(texto_usuario):

    print("\n🤖 Procesando tu solicitud...\n")

    try:
        resp = requests.post(
            WEBHOOK_URL,
            json={"message": texto_usuario},
            auth=auth,
            timeout=60
        )
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    procesar_respuesta(resp)


# ---------------------------------------------------------
#  LOOP PRINCIPAL DEL AGENTE
# ---------------------------------------------------------
def iniciar():

    mostrar_banner()

    while True:
        consulta = input("💬 Escribí tu consulta (o 'salir'): ").strip()

        if consulta.lower() == "salir":
            print("\n👋 ¡Gracias por usar el Agente Inteligente!")
            print("👋 Saliendo...\n")
            break

        enviar_mensaje(consulta)


if __name__ == "__main__":
    iniciar()
