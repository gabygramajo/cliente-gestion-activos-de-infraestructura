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


# ---------------------------------------------------------
# 🔹 INTERFAZ DEL MENÚ ESTÉTICA
# ---------------------------------------------------------

def mostrar_menu():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║      💻  InfraQuery — Agente Inteligente de Activos        ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    print("📌 Seleccioná una opción:")
    print("1️⃣  Consulta normal (texto)")
    print("2️⃣  Generar Excel (guardar de manera local)")
    print("3️⃣  Enviar reporte por Gmail")
    print("4️⃣  Subir reporte a Google Drive")
    print("5️⃣  Salir")

# ---------------------------------------------------------------------------
# 🔹 FUNCIÓN PRINCIPAL DE ENVÍO de consulta a n8n y mostrado de resultados
# ---------------------------------------------------------------------------

def enviar_mensaje(mensaje, action="query_only", destino=None):
   
    data = {"action": action, "message": mensaje}
    if destino:
        data["destination"] = destino

    headers = {"Content-Type": "application/json"}

    print("\n🤖 Procesando tu solicitud...\n")
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


    # ---------------------------------------------------------
    # 🔹 1) CONSULTA NORMAL
    # ---------------------------------------------------------
    
    if action == "query_only":
        try:
            res_json = response.json()

            print(f"🤖 {res_json["mensaje"]}")
            df = pd.json_normalize(res_json["data"])
            print(df.to_string(index=False))
                
        except Exception:
            print("⚠ Respuesta no JSON:\n", response.text)


    # ---------------------------------------------------------
    # 🔹 2) DESCARGA DE EXCEL
    # ---------------------------------------------------------
    
    elif action == "query_csv":
        
        if "application/vnd.openxmlformats" in content_type:
            download_dir = Path.home() / "Downloads"
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = download_dir / f"reporte_{timestamp}.xlsx"

            try:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"\n✅ Archivo guardado en: ")
                print(f"📁 {filename}")
                
                df = pd.read_excel(io.BytesIO(response.content))
                print("\n📊 Vista previa del reporte:\n")
                print(df.head(10).to_string(index=False))
                
            except Exception as e:
                print("❌ Error al guardar o leer el archivo:", e)
        else:
            print("⚠ Tipo de contenido inesperado:", content_type)


    # ---------------------------------------------------------
    # 🔹 3) GMAIL
    # ---------------------------------------------------------
    
    elif action == "query_gmail":
        print("\n📧 Reporte enviado por Gmail con éxito.")
        try:
            data = response.json()
            print("📬 Verificá tu bandeja de entrada.")
        except Exception:
            print(response.text)
            
    # ---------------------------------------------------------
    # 🔹 4) GOOGLE DRIVE
    # ---------------------------------------------------------
    
    elif action == "query_drive":
        print("\n☁ Reporte subido a Google Drive con éxito.")
        
        try:
            drive_data = response.json()
            name = drive_data.get("name", "reporte.xlsx")
            link = drive_data.get("webViewLink", "")
                
            print(f"📁 Nombre del archivo: {name}")
            if link:
                print(f"🔗 Enlace para abrirlo: {link}")
                
        except Exception:
            print("⚠ No se pudo interpretar la respuesta del Drive.")
            print(response.text)

    else:
        print("\n⚠ Acción desconocida.")
        print(response.text)


# ---------------------------------------------------------
# 🔹 MENÚ PRINCIPAL
# ---------------------------------------------------------

def iniciar_aplicacion():

    while True:
        mostrar_menu()
        opcion = input("\n👉 Elegí una opción (1-5): ").strip()
        
        if opcion == "5":
            print("\n👋 ¡Gracias por usar el Agente Inteligente!")
            print("👋 Saliendo...\n")
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
        
# ---------------------------------------------------------
# 🔹 EJECUCIÓN
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        iniciar_aplicacion()
    except KeyboardInterrupt:
        print("\n\n👋 Programa finalizado por el usuario.")
