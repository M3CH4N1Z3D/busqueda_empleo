import os
from dotenv import load_dotenv
import google.generativeai as genai

class MatchEvaluator:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def evaluar_oferta(self, cv_text, job_description):
        prompt = f"""Actúa como un reclutador técnico estricto. Compara el siguiente CV con la descripción de la oferta de trabajo y evalúa qué tan bien se ajustan las habilidades y experiencia.

Reglas de evaluación CRÍTICAS:
1. Análisis de Seniority y Años de Experiencia: Identifica el nivel requerido en la oferta (Junior, Semi-Senior, Senior, Lead) y los años de experiencia exigidos. Compáralos estrictamente con el CV.
2. Penalización Severa: Si la oferta exige nivel 'Senior' o más de 4 años de experiencia en una tecnología, y el CV demuestra ser nivel Junior/Mid o tiene mucha menos experiencia, el match_score NUNCA debe superar el 50%, sin importar cuántas tecnologías coincidan.

Responde ÚNICA Y ESTRICTAMENTE con un JSON válido sin bloques de código Markdown ni texto adicional. El JSON debe tener exactamente dos claves:
- match_score: un número entero del 0 al 100.
- justificacion: un string de máximo 2 líneas explicando por qué se dio ese puntaje. Si hubo una penalización por falta de años de experiencia o seniority, debes mencionarlo explícitamente aquí.

CV:
{cv_text}

Descripción de la oferta:
{job_description}
"""
        response = self.model.generate_content(prompt)
        return response.text

if __name__ == '__main__':
    evaluator = MatchEvaluator()
    
    job_description = "Interpretar requerimientos, analizar documentación y desarrollar componentes nuevos o ajustar funcionalidades de un sistema desarrollado en Python con framework Django, debe comprender el ORM y conocer base de datos de manera básica. 1 año de experiencia."
    
    cv_text = "Desarrollador Backend con 2 años de experiencia. Sólidos conocimientos en Python y bases de datos relacionales (PostgreSQL, MySQL). Experiencia creando APIs REST con FastAPI y Flask. No tengo experiencia previa con Django."
    
    resultado = evaluator.evaluar_oferta(cv_text, job_description)
    print(resultado)
