import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("❌ ERROR: No se encontró 'WEBHOOK_URL' en el archivo .env")

def enviar_mensaje(mensaje, action="query_only", destino=None):
    """
    Envía una solicitud al Webhook de n8n con acción definida.
    """
    data = {
        "action": action,        # query_only | query_csv | query_gmail | query_drive
        "message": mensaje
    }

    if destino:
        data["destination"] = destino

    headers = {"Content-Type": "application/json"}
    response = requests.post(WEBHOOK_URL, json=data, headers=headers)

    print(f"\n➡️   HTTP {response.status_code}")
    try:
        print("\n✅ Respuesta:")
        print(response.json())
    except Exception:
        print(response.text)


def menu():
    print("\n=== 💻 Agente de Activos - Cliente Python ===")
    print("1. Consulta normal (texto)")
    print("2. Generar CSV (descarga)")
    print("3. Enviar por Gmail")
    print("4. Subir a Google Drive")
    print("5. Salir")

    while True:
        opcion = input("\n👉 Elegí una opción (1-5): ").strip()
        if opcion == "5":
            print("\n👋 Saliendo...")
            break

        mensaje = input("💬 Escribí tu consulta: ")

        if opcion == "1":
            enviar_mensaje(mensaje, "query_only")
        elif opcion == "2":
            enviar_mensaje(mensaje, "query_csv")
        elif opcion == "3":
            destino = input("📧 Correo destino: ")
            enviar_mensaje(mensaje, "query_gmail", destino)
        elif opcion == "4":
            enviar_mensaje(mensaje, "query_drive")
        else:
            print("⚠️ Opción inválida")


if __name__ == "__main__":
    menu()
