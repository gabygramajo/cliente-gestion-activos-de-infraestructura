# ==========================================================
# 📦 IMPORTACIONES
# ==========================================================
import os                                         # para variables de entorno y rutas
import io                                         # para manejar bytes en memoria
import json                                       # para parsear JSON
import re                                         # para expresiones regulares
import time                                       # para animaciones y temporizaciones
import threading                                  # para animaciones paralelas simples
from datetime import datetime                     # para timestamps en nombres de archivos
from pathlib import Path                           # para rutas multiplataforma
import requests                                   # para hacer POST al webhook
import pandas as pd                                # para leer Excel y manipular dataframes
from dotenv import load_dotenv                     # para cargar variables de entorno

# librería principal de UI en consola
from rich import print as rprint                    # print con soporte rich
from rich.console import Console                    # console para control avanzado
from rich.panel import Panel                        # paneles tipo tarjeta
from rich.table import Table                        # tablas estilizadas
from rich.spinner import Spinner                    # spinner animado
from rich.prompt import Confirm                     # pedir sí/no interactivo
from rich.progress import Progress, SpinnerColumn, TextColumn  # progreso
from rich.markdown import Markdown                  # para mostrar bloques tipo markdown
from rich.syntax import Syntax                      # para colorear JSON y código
from rich.align import Align                        # para centrar/alinear textos
from rich.text import Text                          # texto con estilo
from rich.box import ROUNDED                        # estilo de borde de tablas


# ==========================================================
#  CONFIGURACIÓN INICIAL
# ==========================================================

console = Console()                                 # objeto console para toda la UI
MAX_WIDTH = 45                                      # ancho máximo para truncar textos
load_dotenv()                                       # carga variables definidas en archivo .env

# obtener webhook y autenticación de variables de entorno
WEBHOOK_URL = os.getenv("WEBHOOK_PRODUCTION")       
WEBHOOK_USER = os.getenv("WEBHOOK_USER")            
WEBHOOK_PASS = os.getenv("WEBHOOK_PASS")            

# auth para requests si existe usuario y pass
auth = (WEBHOOK_USER, WEBHOOK_PASS) if WEBHOOK_USER and WEBHOOK_PASS else None


# ==========================================================
# 🔧 UTILIDADES: LIMPIEZA Y PARSEO DE DATOS
# ==========================================================
def limpiar_y_parsear_json(texto):                    
    """
    Intenta extraer un JSON válido desde un texto, manejando texto mezclado con explicación.
    """
        
    if not isinstance(texto, str):                    
        return None                                    
    # quitar etiquetas comunes y caracteres no deseados
    texto_limpio = texto.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto_limpio)               
    except Exception:
        pass                                          
    # buscar bloque JSON con regex { ... }
    match = re.search(r"\{[\s\S]*\}", texto_limpio)    # patrón que captura el primer objeto JSON
    if match:                                          # si hay coincidencia
        try:
            return json.loads(match.group(0))          # intentar parsear ese bloque encontrado
        except Exception:
            return None                                
    return None 


# ==========================================================
# 🎨 INTERFAZ VISUAL Y UX
# ==========================================================
def mostrar_banner():                           
    """
    Muestra un banner estático elegante con información resumida del sistema.
    """
    
    title = Text("SIRA — Agente Inteligente de Activos", style="bold white on purple", justify="center")
    subtitle = Text("📌 Bienvenido a INFRAQUERY — Consultas en lenguaje natural · Reportes automáticos", style="italic", justify="center")
    
    # construir panel con markdown de features principales
    features = """
    - 💬 Consultas conversacionales (lenguaje natural)
    - 📊 Generación automática de reportes Excel
    - 📧 Envío de informes por Gmail
    - 📁 Copia de seguridad en Google Drive
    """
    # mostrar panel principal y un panel secundario con features
    console.print(Panel.fit(title, border_style="bright_magenta"))
    console.print(Align.center(Markdown(subtitle.plain)))
    console.print(Panel.fit(Markdown(features), title="[bold]Funciones principales", border_style="cyan"))

# ------------------------------
# Efecto "typing" para respuesta de SIRA
# ------------------------------
def typing_effect(message, delay=0.02):              
    """
    Muestra el mensaje como si SIRA lo estuviera escribiendo.
    delay: segundos entre caracteres.
    """
    typed = ""                                             # variable acumuladora
    for ch in message:                                     # iterar cada caracter de la cadena
        typed += ch                                        # añadir caracter actual
        console.print(ch, end="", style="yellow bold")       # imprimir sin salto de línea con estilo
        time.sleep(delay)                                  # dormir un poquito para efecto typing
    console.print()                                   

# ------------------------------
# SPINNER WHILE REQUEST
# ------------------------------
class RequestSpinner:                                 
    """Context manager para mostrar un spinner mientras se ejecuta una función de bloqueo."""
    def __init__(self, text="Procesando..."):         # constructor con texto por defecto
        self.text = text                               # almacenar texto mostrado

    def __enter__(self):                              # entrar al contexto
        # iniciar Progress con SpinnerColumn y texto
        self.progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"))
        self.task = self.progress.add_task(self.text, start=False)
        self.progress.start()                          # comenzar animación
        return self

    def __exit__(self, exc_type, exc, tb):             # al salir del contexto
        self.progress.stop()                           # detener animación
                                      

# ==========================================================
# 📁 PROCESAR ARCHIVOS BINARIOS (XLSX)
# ==========================================================
def manejar_excel(resp):                              
    """
    Guarda el archivo Excel en Downloads y muestra una preview en consola.
    """
    
    # ruta a carpeta Downloads del usuario
    download_dir = Path.home() / "Downloads"           
    download_dir.mkdir(exist_ok=True)                  # crear la carpeta si no existe
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")     
    filepath = download_dir / f"reporte_{timestamp}.xlsx"       # ruta completa del archivo
    
    try:
        with open(filepath, "wb") as f:                # abrir archivo en modo binario
            f.write(resp.content)                    
        console.print(f"\n:[bold green]Archivo Excel descargado correctamente:[/bold green] 📁 [bold] {filepath}[/bold]\n")  # confirmar guardado
        
        # intentar leer y mostrar preview con pandas
        df = pd.read_excel(io.BytesIO(resp.content))  
        mostrar_preview_excel(df)                      
        
    except Exception as e:                              
        console.print(f"[red]❌ Error al guardar/leer el Excel:[/red] {e}")


# ==========================================================
# 💻 VISTA PREVIA EXCEL
# ==========================================================

def truncar(valor, width=MAX_WIDTH):                                                
    """
    Trunca cadenas largas para que la tabla no explote en consola.
    """                
    valor = "" if pd.isna(valor) else str(valor)                                     # asegurar que sea str (y manejar NaN de pandas)
    return valor if len(valor) <= width else valor[:width - 3] + "..."  # truncar y añadir "..."


def mostrar_preview_excel(df):                       
    """
    Muestra hasta 10 filas del dataframe como tabla Rich con truncado por celda.
    """
    # crear tabla Rich y asignar estilo
    table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)  # tabla con borde redondeado
    
    # agregar columnas con nombres de columnas del dataframe
    for col in df.columns.tolist():                              # iterar nombres de columnas
        table.add_column(str(col), overflow="fold")              # agregar columna al objeto Table
        
    # agregar filas truncadas (hasta 10)
    for _, row in df.head(10).iterrows():                       # iterar primeras 10 filas
        row_cells = [truncar(v) for v in row.tolist()]          # truncar cada celda para presentación
        table.add_row(*row_cells)                               # añadir fila a la tabla
    
    console.print(Panel(table, title="📊 Vista previa (primeras 10 filas)", border_style="green")) 

# ------------------------------
# MOSTRAR respuesta JSON (opcional)
# ------------------------------
def mostrar_json_opcional(response_json):
    """
    Pregunta al usuario si desea ver el JSON técnico.
    Si confirma, muestra JSON coloreado.
    """
    # preguntar con Confirm.ask (default False)
    want = Confirm.ask("\n¿Querés ver los detalles técnicos (JSON)?", default=False)
    if want:
        # serializar y colorear
        pretty = json.dumps(response_json, ensure_ascii=False, indent=2)
        syntax = Syntax(pretty, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="📦 JSON completo (detalles)"))


# ==========================================================
# 🧠 MOSTRAR RESPUESTA ESTRUCTURADA DEL AGENTE
# ==========================================================
def mostrar_json_formateado(data,  show_json_prompt=True):                   
    """
    Muestra un JSON estructurado devuelto por SIRA de forma agradable.
    """
    
    if data.get("mail") is not None:
        console.print("\n[bold green]📧 Correo enviado correctamente.[/bold green]")
        
    if data.get("webViewLink"):                           
        console.print(f"\n🔗 Archivo subido a Drive: [underline blue]{data['webViewLink']}[/underline blue]")
        
    # Obtener mensaje textual    
    mensaje = data.get("mensaje") or data.get("message") or "" 
    if mensaje:                                          
        typing_effect(f"\n🤖 SIRA: {mensaje}")                   
        
    # si el payload trae un array de "data", mostrar como tabla
    if isinstance(data.get("data"), list) and len(data.get("data")) > 0:
        try:
            df = pd.json_normalize(data["data"])          # normalizar JSON en dataframe
            mostrar_preview_excel(df)                    # reutilizar vista previa para mostrar tabla
        except Exception as e:
            console.print(f"[yellow]⚠ No se pudo mostrar data como tabla: {e}[/yellow]")
            
    # if show_json_prompt:
    #     mostrar_json_opcional(data)


# ==========================================================
# 🔄 PROCESAR RESPUESTA DEL SERVIDOR
# ==========================================================
def procesar_respuesta(resp):                           # decisión según content-type del response
    """
    Analiza la respuesta HTTP del webhoow y decide cómo presentarla (Excel, JSON o texto).
    """
    
    content_type = resp.headers.get("Content-Type", "")  # obtener header content-type
    raw_text = resp.text.strip()                         # obtener texto crudo
    
    # 1) CASO: Archivo Excel
    if "application/vnd.openxmlformats" in content_type or resp.headers.get("Content-Disposition", "").lower().startswith("attachment"):
        return manejar_excel(resp)                              

    # 2) CASO: JSON puro
    if "application/json" in content_type:
        try:
            data = resp.json()                           # parsear JSON directamente
            return mostrar_json_formateado(data)                # mostrar JSON formateado
        except Exception:
            pass
    
    # 3) CASO: Texto → intentar extraer JSON
    posible_json = limpiar_y_parsear_json(raw_text)     
    if posible_json:
        return mostrar_json_formateado(posible_json)          
        
     # 4) CASO: Texto plano (fallback)
    console.print(Panel(raw_text, title="💬 Respuesta del servidor (texto)", border_style="magenta"))
    lct = raw_text.lower()  
    
    # Detectar acciones ejecutadas
    if "gmail" in lct:
        console.print("📧 El correo fue enviado correctamente.")
    if "drive" in lct:
        console.print("☁ Archivo subido a Drive.")


# ==========================================================
#  📡 ENVIAR MENSAJE A n8n (WEBHOOK)
# ==========================================================
def enviar_mensaje(texto_usuario):                      
    """
    Envía la consulta al webhook (n8n) y procesa la respuesta.
    """
    # mostrar spinner/progreso mientras se espera la respuesta
    with RequestSpinner("[magenta]Procesando tu solicitud con SIRA...[/magenta]"):  # contexto con spinner
        try:
            resp = requests.post(                          # realizar petición POST
                WEBHOOK_URL,                               # URL del webhook
                json={"message": texto_usuario},           # payload con mensaje del usuario
                auth=auth,                                 # auth si aplicada
                timeout=60                                 # timeout razonable
            )
        except Exception as e:                              # manejar errores de conexión
            console.print(f"[red]❌ Error de conexión:[/red] {e}")
            return
    procesar_respuesta(resp)


# ==========================================================
# ▶ FUNCIÓN PRINCIPAL DEL AGENTE
# ==========================================================
def iniciar():                                         
    """
    Función principal que inicia la UI en consola y recibe las consultas del usuario.
    """
    mostrar_banner()                                  
    console.print("\n[dim] Escribí 'salir' o 'exit' para finalizar la sesión. [/dim]\n")
  
    while True:
        try:
            consulta = console.input("[bold cyan]💬 Tu consulta ('salir'o 'exit') > [/bold cyan]").strip()  
        except (KeyboardInterrupt, EOFError):           
            console.print("\n[red]\nInteracción finalizada por el usuario.[/red]")
            break
        
        if consulta.lower() in ("salir", "exit"):     
            console.print("\n[bold green]¡Gracias por usar SIRA! Hasta la próxima. 🤖[/bold green]\n")
            break
        
        if len(consulta) < 2:                         
            console.print("[yellow]⚠ Escribí una consulta válida.[/yellow]")
            continue
        
        # enviar mensaje y procesar resultado
        enviar_mensaje(consulta)                       
        console.print("\n[dim]----- Fin de la respuesta -----\n[/dim]")  


# ==========================================================
# 🚀 EJECUCIÓN
# ==========================================================
if __name__ == "__main__":                           
    if not WEBHOOK_URL:                                
        console.print("[red]ERROR:[/red] Variable WEBHOOK_PRODUCTION no configurada. Definila en .env antes de ejecutar.")  # instrucción
    else:
        iniciar()                                       
