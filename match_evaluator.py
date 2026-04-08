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
        prompt = f"""Compara el siguiente CV con la descripción de la oferta de trabajo. Evalúa qué tan bien se ajustan las habilidades y experiencia. Responde ÚNICA Y ESTRICTAMENTE con un JSON válido sin bloques de código Markdown ni texto adicional. El JSON debe tener exactamente dos claves: match_score (un número entero del 0 al 100) y justificacion (un string de máximo 2 líneas explicando por qué se dio ese puntaje).

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
