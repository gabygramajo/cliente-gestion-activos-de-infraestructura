import os
import io
import json
import pandas as pd
import requests 
from pathlib import Path
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

WEBHOOK_PRODUCTION = os.getenv("WEBHOOK_PRODUCTION")
WEBHOOK_USER = os.getenv("WEBHOOK_USER")
WEBHOOK_PASS = os.getenv("WEBHOOK_PASS")

if not WEBHOOK_PRODUCTION:
    raise ValueError("❌ ERROR: No se encontró 'WEBHOOK_PRODUCTION' en el archivo .env")

auth = None
if WEBHOOK_USER and WEBHOOK_PASS:
    auth = HTTPBasicAuth(WEBHOOK_USER, WEBHOOK_PASS)

def enviar_mensaje(mensaje, action="query_only", destino=None):
    """
    Envía una consulta al flujo de n8n y muestra el resultado.
    """
    data = {"action": action, "message": mensaje}
    if destino:
        data["destination"] = destino

    headers = {"Content-Type": "application/json"}

    print("\n🤖 Procesando tu solicitud...")
    try:
        response = requests.post(WEBHOOK_PRODUCTION, json=data, headers=headers, auth=auth, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return

    #print(f"📡 Respuesta HTTP {response.status_code}")

    if response.status_code >= 400:
        print("❌ Error HTTP:", response.text)
        return

    content_type = response.headers.get("Content-Type", "")

    # 🔹 1) Consultas normales (texto o JSON)
    if action == "query_only":
        try:
            res_json = response.json()
            if isinstance(res_json, dict) and "result" in res_json:
                print("\n📋 Resultado:\n", res_json["result"])
            elif isinstance(res_json, list):
                df = pd.DataFrame(res_json)
                print("\n📊 Resultados:\n")
                print(df.to_string(index=False))
            else:
                print(json.dumps(res_json, indent=2, ensure_ascii=False))
        except Exception:
            print("⚠ Respuesta no JSON:\n", response.text)

    # 🔹 2) Descarga local del Excel
    elif action == "query_csv":
        if "application/vnd.openxmlformats" in content_type:
            download_dir = Path.home() / "Downloads"
            filename = download_dir / "reporte_activos.xlsx"
            try:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"\n✅ Archivo guardado en: {filename}")
                df = pd.read_excel(io.BytesIO(response.content))
                print("\n📊 Vista previa del reporte:\n")
                print(df.head(10).to_string(index=False))
            except Exception as e:
                print("❌ Error al guardar o leer el archivo:", e)
        else:
            print("⚠ Tipo de contenido inesperado:", content_type)

  # 🔹 3) Gmail
    elif action == "query_gmail":
        print("\n📧 Reporte enviado por Gmail con éxito.")
        try:
            data = response.json()
            msg_id = data.get("id")
            print("📬 Verificá tu bandeja de entrada.")
        except Exception:
            print(response.text)
            
# 🔹 4) Google Drive
    elif action == "query_drive":
        print("\n☁ Reporte subido a Google Drive con éxito.")
        try:
            drive_data = response.json()
            name = drive_data.get("name", "reporte.xlsx")
            link = drive_data.get("webViewLink", "")
            
            # Reemplazamos plantilla por fecha real si la trae
            if "{{" in name:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                name = f"reporte_{timestamp}.xlsx"
            print(f"📁 Nombre del archivo: {name}")
            if link:
                print(f"🔗 Enlace: {link}")
        except Exception:
            print("⚠ No se pudo interpretar la respuesta del Drive.")
            print(response.text)

    else:
        print("\n⚠ Acción desconocida.")
        print(response.text)

def menu():
    print("\n=== 💻 Agente de Activos - Cliente Python ===")
    print("1️⃣  Consulta normal (texto)")
    print("2️⃣  Generar Excel (guardar en Descargas)")
    print("3️⃣  Enviar por Gmail")
    print("4️⃣  Subir a Google Drive")
    print("5️⃣  Salir")

    while True:
        opcion = input("\n👉 Elegí una opción (1-5): ").strip()
        if opcion == "5":
            print("\n👋 Saliendo...")
            break

        mensaje = input("💬 Escribí tu consulta: ").strip()
        if not mensaje:
            print("⚠ Ingresá una consulta válida.")
            continue

        if opcion == "1":
            enviar_mensaje(mensaje, "query_only")
        elif opcion == "2":
            enviar_mensaje(mensaje, "query_csv")
        elif opcion == "3":
            destino = input("📧 Ingresá el correo destino: ").strip()
            if not destino:
                print("⚠ Correo destino requerido.")
                continue
            enviar_mensaje(mensaje, "query_gmail", destino)
        elif opcion == "4":
            enviar_mensaje(mensaje, "query_drive")
        else:
            print("⚠ Opción inválida")
        
if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n👋 Programa finalizado por el usuario.")
