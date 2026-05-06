import os
import json
from google import genai

class CVTailor:
    def __init__(self):
        self.client = genai.Client()
        self.model_id = "gemini-2.5-flash"
        
        # Asegurar que el directorio de salidas exista
        os.makedirs("salidas", exist_ok=True)

    def adaptar_cv(self, cv_base_text: str, job_description: str, empresa: str) -> str:
        prompt = (
            "Analiza el CV base y la oferta de trabajo. Devuelve un JSON con CUATRO claves: "
            "titulo_sugerido (Un título profesional sugerido para el CV, adaptado a la oferta), "
            "resumen_profesional (Reescribe el resumen profesional destacando la experiencia y tecnologías que hagan match exacto con la oferta. Máximo 2 párrafos. Tono profesional. SIN formato Markdown, texto plano. "
            "REGLAS ESTRICTAS PARA RESUMEN_PROFESIONAL: "
            "1. PROHIBIDA LA TERCERA PERSONA: NUNCA escribas 'Él es', 'Mauricio tiene', etc. "
            "2. PROHIBIDO INCLUIR EL NOMBRE: NUNCA menciones el nombre del candidato en el resumen. "
            "3. OBLIGATORIO PRIMERA PERSONA O NEUTRO: Escribe desde la perspectiva del candidato (ej. 'Soy un desarrollador...') o usa un tono profesional directo (ej. 'Desarrollador Full Stack con experiencia en...'). "
            "4. ESTILO: Mantén un tono maduro, técnico y directo al grano.), "
            "aptitudes_clave (Una lista de las mejores habilidades para la oferta, presentadas en viñetas o texto plano) y "
            "exp_spark_team (Reescribe brevemente las responsabilidades del rol en SPARK TEAM para alinearlas con la oferta de trabajo. Máximo 2 párrafos cortos). "
            "NO incluyas texto fuera del JSON.\n\n"
            f"--- CV ORIGINAL ---\n{cv_base_text}\n\n"
            f"--- OFERTA DE TRABAJO ---\n{job_description}"
        )

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
        )
        
        try:
            # Limpiar la respuesta por si Gemini incluye bloques de código markdown
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            datos_cv = json.loads(json_text.strip())
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de Gemini: {e}")
            print(f"Respuesta original: {response.text}")
            # Valores por defecto en caso de error
            datos_cv = {
                "titulo_sugerido": "Desarrollador de Software",
                "resumen_profesional": "Profesional con experiencia en el área, adaptando el perfil a los requerimientos de la oferta.",
                "aptitudes_clave": "Habilidades técnicas, Trabajo en equipo, Resolución de problemas",
                "exp_spark_team": "Experiencia en desarrollo y mantenimiento de aplicaciones, trabajando en equipo para lograr los objetivos del proyecto."
            }

        print(datos_cv)

        # Generar TXT
        txt_path = self._generar_txt(datos_cv, empresa)
        return txt_path

    def _generar_txt(self, json_data: dict, empresa: str) -> str:
        # Limpiar el nombre de la empresa para el archivo
        empresa_limpia = "".join(c if c.isalnum() else "_" for c in empresa)
        txt_path = os.path.join("salidas", f"Sugerencias_HV_{empresa_limpia}.txt")
        
        lista_aptitudes = json_data.get('aptitudes_clave', [])
        if isinstance(lista_aptitudes, str):
            lista_aptitudes = [apt.strip() for apt in lista_aptitudes.split(',')]
            
        aptitudes_str = "\n".join([f"- {apt}" if not apt.startswith("-") and not apt.startswith("•") else apt for apt in lista_aptitudes])

        contenido = f"SUGERENCIAS DE ADAPTACIÓN DE HOJA DE VIDA PARA: {empresa}\n"
        contenido += "=" * 60 + "\n\n"
        
        contenido += "TÍTULO SUGERIDO:\n"
        contenido += "-" * 20 + "\n"
        contenido += f"{json_data.get('titulo_sugerido', '')}\n\n"
        
        contenido += "RESUMEN PROFESIONAL:\n"
        contenido += "-" * 20 + "\n"
        contenido += f"{json_data.get('resumen_profesional', '')}\n\n"
        
        contenido += "APTITUDES CLAVE:\n"
        contenido += "-" * 20 + "\n"
        contenido += f"{aptitudes_str}\n\n"
        
        contenido += "EXPERIENCIA SPARK TEAM:\n"
        contenido += "-" * 20 + "\n"
        contenido += f"{json_data.get('exp_spark_team', '')}\n"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(contenido)
            
        return txt_path
