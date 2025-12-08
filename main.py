# ------------------------------
# Importaciones del sistema
# ------------------------------
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
from prettytable import PrettyTable
from colorama import Fore, Style, init

init(autoreset=True)
MAX_WIDTH = 45

# ------------------------------
# Cargar variables de entorno
# ------------------------------
load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_PRODUCTION")
WEBHOOK_USER = os.getenv("WEBHOOK_USER")
WEBHOOK_PASS = os.getenv("WEBHOOK_PASS")

auth = None
# Si el webhook tiene autenticación básica
if WEBHOOK_USER and WEBHOOK_PASS:
    auth = HTTPBasicAuth(WEBHOOK_USER, WEBHOOK_PASS)


# ---------------------------------------------------------
# 🔧 LIMPIEZA DE TEXTO Y PARSEO DE JSON
# ---------------------------------------------------------
def limpiar_y_parsear_json(texto):
    """
    Intenta detectar y extraer un JSON válido desde un texto.
    Limpia bloques json ... 
    y busca estructuras JSON dentro del texto.
    """
    
    if not isinstance(texto, str):
        return None
    
    # Eliminamos marcas Markdown
    texto = texto.replace("json", "").replace("", "").strip()

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


# ==========================================================
#  🎨 INTERFAZ VISUAL
# ==========================================================
def mostrar_banner():
    """Muestra el encabezado visual del sistema"""
    
    print("\n")
    print("╔══════════════════════════════════════════════════════╗")
    print("║      🤖  SIRA — Agente Inteligente de Activos        ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    
    print("📌 Bienvenido a INFRAQUERY")
    print("Nuestra querida asistente inteligente SIRA, les ayudara con sus consultas \n sobre la gestion de los activos de tu Infraestructura.\n")
    print("Podras realizar: ")
    print("💬  Consultas conversacionales (texto)")
    print("📊  Generar reportes Excel")
    print("📧  Enviar reportes por Gmail")
    print("📁  Guardar reportes en Google Drive\n")
    print("Tambien al escribrir 'salir' o 'exit' en la terminal podras finalizar la interaccion con el sistema.")


# ==========================================================
# 📁 PROCESAR ARCHIVOS BINARIOS (XLSX)
# ==========================================================
def manejar_excel(resp):
    """
    Guarda el archivo Excel descargado, lo muestra en consola con pandas
    y retorna None.
    """

    download_dir = Path.home() / "Downloads"
    download_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filepath = download_dir / f"reporte_{timestamp}.xlsx"

    try:
        # Guardamos el archivo en disco
        with open(filepath, "wb") as f:
            f.write(resp.content)

        print("\n✅ Archivo Excel descargado correctamente:")
        print(f"📁 {filepath}\n")

        try:
            df = pd.read_excel(io.BytesIO(resp.content))
            mostrar_preview_excel(df)

        except Exception as e:
            print("⚠ El archivo se descargó, pero no se pudo mostrar en consola.")
            print("  Motivo:", e)

    except Exception as e:
        print("❌ Error al guardar el archivo:", e)


# ==========================================================
# 💻 VISTA PREVIA EXCEL
# ==========================================================
def truncar(valor):
    valor = str(valor)
    return valor if len(valor) <= MAX_WIDTH else valor[:MAX_WIDTH - 3] + "..."

def mostrar_preview_excel(df):
    """
    Muestra los primeros 10 datos de un DataFrame en forma de tabla bonita con PrettyTable.
    Se usa únicamente para vista previa en consola.
    """
    tabla = PrettyTable()

    # Encabezados
    tabla.field_names = df.columns.tolist()

    # Filas truncadas
    for _, row in df.head(10).iterrows():
        fila_truncada = [truncar(v) for v in row.tolist()]
        tabla.add_row(fila_truncada)

    tabla.align = "l"
    tabla.hrules = 1

    print(Fore.GREEN + Style.BRIGHT + "📊 Vista previa del archivo:\n")
    print(tabla)

# ==========================================================
# 🧠 MOSTRAR MENSAJE DE JSON DEL AGENTE
# ==========================================================
def mostrar_json_formateado(data):
    """
    Muestra un JSON estructurado devuelto por SIRA de forma agradable.
    """

    mensaje = data.get("mensaje") or data.get("message")

    if mensaje:
        print("\n🤖", mensaje.replace("*", ""), "\n")

    # Mostrar enlace a Drive si existe
    if data.get("webViewLink"):
        print("🔗 Archivo subido a Drive:", data["webViewLink"])
        print("\n")

    # Mostrar tabla si existe
    if isinstance(data.get("data"), list):
        df = pd.json_normalize(data["data"])
        print(df.head(10).to_string(index=False))

    return


# ==========================================================
# 🔄 PROCESAR RESPUESTA DEL SERVIDOR
# ==========================================================
def procesar_respuesta(resp):
    """
    Analiza la respuesta HTTP del webhook.
    Puede ser:
    - Archivo Excel binario
    - JSON estructurado
    - Texto conversacional
    """

    content_type = resp.headers.get("Content-Type", "")
    raw_text = resp.text.strip()

    # 1) CASO: Archivo Excel
    if "application/vnd.openxmlformats" in content_type:
        return manejar_excel(resp)

    # 2) CASO: JSON puro
    if "application/json" in content_type:
        try:
            data = resp.json()
            return mostrar_json_formateado(data)
        except:
            pass

    # 3) CASO: Texto → intentar extraer JSON
    posible_json = limpiar_y_parsear_json(raw_text)
    if posible_json:
        return mostrar_json_formateado(posible_json)

    # 4) CASO: Texto plano (fallback)
    print("\n💬 Respuesta del servidor:")
    print(raw_text)

    # Detectar acciones ejecutadas
    if "gmail" in raw_text.lower():
        print("📧 El correo fue enviado correctamente.")
    if "drive" in raw_text.lower():
        print("☁ Archivo subido a Drive.")

    return


# ==========================================================
#  📡 ENVIAR MENSAJE A n8n
# ==========================================================
def enviar_mensaje(texto_usuario):
    """
    Envía la consulta del usuario al webhook y procesa la respuesta.
    """

    print("\n⌛ Procesando tu solicitud...")

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


# ==========================================================
# ▶ FUNCIÓN PRINCIPAL DEL AGENTE
# ==========================================================

def iniciar():

    mostrar_banner()

    while True:
        consulta = input("\n💬 Escribí tu consulta (o 'salir'): ").strip()

        if consulta.lower() in ("salir", "exit"):
            print("\n¡Gracias por usar SIRA 🤖!")
            print("👋 Hasta la próxima...\n")
            break
        
        if len(consulta) < 2:
            print("⚠ Escribí una consulta válida.")
            continue
        
        enviar_mensaje(consulta)

# ==========================================================
# 🚀 EJECUCIÓN
# ==========================================================

if __name__ == "__main__":
    iniciar()
