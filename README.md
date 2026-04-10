# 🚀 AutoJob Matcher & CV Tailor 🤖💼

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Scraping-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-Powered-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![DocxTpl](https://img.shields.io/badge/DocxTpl-Templating-orange?style=for-the-badge)

¡Bienvenido a **AutoJob Matcher & CV Tailor**! Una herramienta automatizada impulsada por Inteligencia Artificial (Google Gemini) y Web Scraping (Playwright) diseñada para revolucionar tu búsqueda de empleo. 

---

## 🌟 ¿Qué hace este repositorio?

Este proyecto automatiza el tedioso proceso de buscar ofertas de trabajo, evaluar si tu perfil encaja y adaptar tu Hoja de Vida (CV) para cada vacante específica. 

En resumen, el sistema:
1. **Lee tu CV base** en formato PDF.
2. **Analiza tu perfil** con IA para descubrir los cargos ideales para ti.
3. **Busca ofertas reales** en portales de empleo (ej. Computrabajo).
4. **Evalúa el "Match"** entre tu CV y la descripción de la oferta.
5. **Adapta tu CV** (resumen, habilidades y experiencia) para que resalte exactamente lo que la empresa busca.
6. **Te envía un correo electrónico** con la oferta recomendada y tu nueva Hoja de Vida en PDF lista para enviar. 🚀

---

## ⚙️ Arquitectura y Flujo de Trabajo

El sistema está compuesto por 6 módulos principales que interactúan de forma secuencial:

1. 📄 **`main.py` (Orquestador):** Es el cerebro de la operación. Coordina la lectura del PDF (`mi_hv.pdf`), llama a los demás módulos y gestiona el flujo de datos.
2. 🧠 **`profile_analyzer.py`:** Utiliza **Gemini AI** para leer tu CV y extraer una lista de *cargos recomendados* y *palabras clave* de tus habilidades.
3. 🕷️ **`scraper.py`:** Utiliza **Playwright** para navegar automáticamente por Computrabajo, buscar los cargos recomendados y extraer los detalles de las ofertas (título, empresa, descripción, URL).
4. ⚖️ **`match_evaluator.py`:** Compara tu CV original con la descripción de la oferta usando IA. Devuelve un **Score de Match (0-100)**. Solo las ofertas con un score `>= 65` pasan a la siguiente fase.
5. ✍️ **`cv_tailor.py`:** Si hay un buen match, la IA reescribe tu resumen profesional y aptitudes clave para alinearlos con la vacante. Luego, inyecta estos datos en una plantilla de Word (`plantilla_hv.docx`) y la convierte a un nuevo PDF en la carpeta `salidas/`.
6. 📧 **`email_notifier.py`:** Toma la oferta exitosa y el PDF generado, y te envía un correo electrónico con todos los detalles y el archivo adjunto para que apliques de inmediato.

---

## 📥 Instalación y Requisitos

Sigue estos pasos para clonar e instalar el proyecto en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/busqueda-empleo-automatizada.git
cd busqueda-empleo-automatizada
```

### 2. Crear un entorno virtual (Recomendado)
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias
Asegúrate de tener instalado Python 3.8 o superior.
```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores para Playwright
```bash
playwright install chromium
```

---

## 🛠️ Configuración

Antes de ejecutar el script, necesitas configurar tus variables de entorno y tus archivos base.

### 1. Variables de Entorno (`.env`)
Crea un archivo llamado `.env` en la raíz del proyecto y configura las siguientes variables:

```env
# API Key de Google Gemini (Obligatorio)
GEMINI_API_KEY=tu_api_key_de_gemini_aqui

# Configuración de Correo (Para notificaciones)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SPM_EMAIL=tu_correo_remitente@gmail.com
SPM_PASSWORD=tu_contraseña_de_aplicacion_gmail
PERSONAL_EMAIL=tu_correo_destino@gmail.com
```
*(Nota: Si usas Gmail, asegúrate de generar una **Contraseña de Aplicación** en la configuración de seguridad de tu cuenta de Google).*

### 2. Archivos Base Requeridos
Debes colocar los siguientes archivos en la raíz del proyecto:
* 📄 **`mi_hv.pdf`**: Tu Hoja de Vida original en formato PDF. De aquí la IA extraerá tu información base.
* 📝 **`plantilla_hv.docx`**: Una plantilla de Microsoft Word. El sistema buscará y reemplazará las siguientes etiquetas en el documento:
  * `{{ RESUMEN_PROFESIONAL }}`
  * `{{ APTITUDES_CLAVE }}` (Se reemplazará por una lista de viñetas)
  * `{{ EXP_SPARK_TEAM }}` (O la experiencia específica que hayas configurado en `cv_tailor.py`)

#### 💡 Guía para crear tu `plantilla_hv.docx`
Para asegurar que el sistema reemplace correctamente los datos en tu plantilla, sigue estas recomendaciones:
1. **Ubicación de los marcadores:** Puedes colocar las etiquetas `{{ ... }}` en cualquier parte del documento: en el texto principal, dentro de **cuadros de texto**, **formas** (como barras laterales de color), **encabezados** o **pies de página**. El sistema está diseñado para encontrarlos en cualquier estructura.
2. **Evita el formato dividido:** Word a veces divide el texto internamente si cambias el formato (negrita, color, fuente) a la mitad de una etiqueta, o si el corrector ortográfico la marca. Para evitar que la etiqueta se rompa:
   * Escribe la etiqueta completa (ej. `{{ RESUMEN_PROFESIONAL }}`) en el Bloc de notas.
   * Cópiala y pégala en tu documento de Word usando la opción **"Conservar solo texto"**.
   * Aplica el formato (tamaño, color, fuente) seleccionando **toda la etiqueta junta**, incluyendo las llaves `{{ }}`.
3. **Espacio para el contenido:** Ten en cuenta que el texto generado por la IA puede ser más largo o más corto que la etiqueta. Asegúrate de que los cuadros de texto o las tablas tengan configurado el ajuste automático de tamaño para que el texto no se corte.

---

## 🎯 Salida Esperada

Para ejecutar el programa, simplemente corre:

```bash
python main.py
```

### ¿Qué verás en la consola?
1. El sistema te informará qué cargos ideales encontró para ti.
2. Verás el progreso del bot navegando y extrayendo ofertas.
3. Se mostrará el **Score** de cada oferta evaluada.
4. Al final, verás una tabla resumen con las ofertas recomendadas (Score >= 65).

### ¿Qué obtendrás al final?
* 📁 **Carpeta `salidas/`**: Se generarán archivos PDF con nombres como `HV_Adaptada_NombreEmpresa.pdf`. Estos son tus CVs personalizados para cada vacante.
* 📬 **Bandeja de entrada**: Recibirás un correo electrónico por cada oferta exitosa con:
  * El título de la vacante y la empresa.
  * El enlace directo para aplicar.
  * El Score de compatibilidad.
  * **Tu CV adaptado en PDF adjunto.**

¡Listo! Ahora puedes aplicar a las mejores ofertas con un CV hecho a la medida en tiempo récord. 🎉
