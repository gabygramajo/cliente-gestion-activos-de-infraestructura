import os
import requests
from dotenv import load_dotenv

# Cargar el archivo .env
load_dotenv()

# Leer la variable del entorno
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("❌ ERROR: No se encontró 'WEBHOOK_URL' en el archivo .env")

def enviar_mensaje(mensaje):
    """
    Envía un mensaje al Webhook de n8n y devuelve la respuesta JSON.
    """
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "mensaje": mensaje
    }

    response = requests.post(WEBHOOK_URL, json=data, headers=headers)

    # Mostrar el estado HTTP
    print(f"\n➡️ Código de respuesta HTTP: {response.status_code}")

    try:
        # Intentamos convertir la respuesta a JSON
        respuesta_json = response.json()
        print("\n✅ Respuesta JSON recibida del servidor:")
        print(respuesta_json)

        # Acceder a los datos específicos
        if "data" in respuesta_json:
            print("\n📩 Mensaje del Agente:")
            print(respuesta_json["data"])
        else:
            print("\n⚠️ No se encontró el campo 'data' en la respuesta")

    except Exception as e:
        print("\n❌ Error al interpretar la respuesta como JSON:")
        print(response.text)
        print(e)


if __name__ == "__main__":
    print("=== Cliente Python para Webhook de n8n ===")

    while True:
        mensaje = input("\n💬 Ingresá tu mensaje (o escribe 'salir' para terminar): ")

        if mensaje.lower() == "salir":
            print("\n👋 Saliendo del programa...")
            break

        enviar_mensaje(mensaje)