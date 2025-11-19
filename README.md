# 🤖 Agente Inteligente para Gestión de Activos de Infraestructura

## 📋 Descripción del Proyecto

Sistema inteligente que permite consultar información sobre los activos de infraestructura de una empresa utilizando lenguaje natural, combinando base de datos, automatización con n8n e inteligencia artificial con un agente smart conectado a Python.


---

## 🛠️  Arquitectura y Stack Tecnológico

Implementa un flujo de datos que desacopla la lógica del negocio de la consulta de datos, orquestado por n8n.

![Arquitectura del proyecto](https://i.postimg.cc/8PtmpN12/Flujo-general.png)

---

## 🔄 Flujo general del Proyecto

1.  👤 **Usuario:** Escribe una petición en lenguaje natural en una consola de Python.

2.  🐍 **Python:** Envía esta petición a un Webhook de n8n vía HTTP REST.

3.  🌐 **n8n:** Recibe la petición y utiliza el nodo de **Gemini** (AI Agent) para interpretar la solicitud.

4.  🤖 **IA (Gemini):** Analiza la petición y la transforma en una consulta SQL dinámica y estructurada.

5.  🌐 **n8n:** Ejecuta la consulta SQL en la base de datos (Supabase).

6.  🗄️ **Base de Datos:** Devuelve los datos a n8n.

7.  🌐 **n8n:** Procesa la respuesta y ejecuta la acción solicitada por el usuario:
    * Devolver una respuesta simple a la consola.
    * Generar un archivo **Excel/CSV**.
    * Enviar un reporte por **Email**.
    * Guardar el archivo en **Google Drive**.

---

## 🗄️ Base de Datos

Modelo relacional optimizado para consultas empresariales sobre infraestructura. Incluye tablas de:

- Activo
- Categoria
- Importancia
- Confidencialidad
- Empleado
- Puesto
- Mantenimiento
- AsignacionActivo
  
📌 Diseño normalizado → permite consultas complejas interpretadas por la IA.

![Base](https://i.postimg.cc/wT0Qqg6P/Data-Base.png)

---

## 🔄 Flujo n8n

El flujo está compuesto por:
- ✔ Webhook (entrada desde Python)
- ✔ AI Agent (Gemini) para generar SQL
- ✔ PostgreSQL Query
- ✔ Convert to Excel (XLSX)
- ✔ Gmail (API) para envío automático
- ✔ Google Drive Upload
- ✔ Respond to Webhook (retorno a Python)
  
![FlujoN8N](https://i.postimg.cc/Pr2QXTXG/Flujo-de-n8n.png)

---

## 🚀 Cómo Empezar

### 1. Clonar el Repositorio

```bash
git clone [URL-DEL-REPOSITORIO]
```

### 2. Crear .env

Incluir:

```bash
WEBHOOK_PRODUCTION= url_del_webhook_de_n8n
WEBHOOK_USER= usuario
WEBHOOK_PASS= password
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar

```bash
python main.py
```

---

## ✨ Ejemplos de Consultas

El sistema es capaz de interpretar una variedad de solicitudes en lenguaje natural, como:

1. 📋 **Consulta normal (texto):** Mostrame un listado de los primeros 10 empleados.
2. ✅ **Generar Excel:** Generá un Excel con los nombres de los empleados y sus puestos.
3. 📧 **Enviar reporte por Gmail:**  Quiero que mandes un mail con los datos de todas las marcas y modelos de notebooks, junto al legajo y nombre del responsable a cargo. 📬 Correo: xxx@yyy.com
4. 📁 **Subir reporte a Google Drive:** Guardar en Google Drive una planilla con la base de conocimientos de cada servicio.
