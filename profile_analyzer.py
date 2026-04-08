import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Cargar variables de entorno
load_dotenv()

class ProfileAnalysisSchema(BaseModel):
    cargos_recomendados: list[str] = Field(
        description="Lista de 3 a 5 títulos de trabajo precisos ideales para el perfil.",
        min_length=3,
        max_length=5
    )
    palabras_clave: list[str] = Field(
        description="Lista de 5 a 7 habilidades técnicas más fuertes del perfil.",
        min_length=5,
        max_length=7
    )

class ProfileAnalyzer:
    """
    Clase para analizar perfiles profesionales (CVs) utilizando Gemini.
    """
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada.")
        
        # Inicializar el cliente de Gemini
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-3-flash-preview"

    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Analiza el texto de un CV y extrae cargos recomendados y palabras clave.
        
        Args:
            cv_text (str): El texto del currículum a analizar.
            
        Returns:
            dict: Un diccionario con las claves 'cargos_recomendados' y 'palabras_clave'.
        """
        if not cv_text or not cv_text.strip():
            raise ValueError("El texto del CV no puede estar vacío.")

        prompt = f"""
        Analiza el siguiente perfil profesional o currículum vitae y extrae la información solicitada.
        
        CV:
        {cv_text}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ProfileAnalysisSchema,
                    temperature=0.2,
                ),
            )
            
            if not response.text:
                raise RuntimeError("La respuesta del modelo está vacía.")
                
            # Parsear el JSON devuelto por el modelo
            result: Dict[str, Any] = json.loads(response.text)
            return result
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error al decodificar la respuesta JSON del modelo: {e}")
        except Exception as e:
            raise RuntimeError(f"Error durante el análisis del CV con Gemini: {e}")

if __name__ == '__main__':
    # Texto simulado de un perfil de desarrollo de software básico
    sample_cv = """
    Desarrollador de Software Junior con 2 años de experiencia.
    Conocimientos sólidos en Python, Django y Flask.
    Experiencia trabajando con bases de datos relacionales como PostgreSQL y MySQL.
    Familiarizado con control de versiones usando Git y GitHub.
    Conocimientos básicos de frontend con HTML, CSS y JavaScript.
    Apasionado por aprender nuevas tecnologías y resolver problemas complejos.
    Nivel de inglés intermedio (B2).
    """
    
    print("Iniciando análisis del CV de prueba...")
    try:
        analyzer = ProfileAnalyzer()
        resultado = analyzer.analyze_cv(sample_cv)
        
        print("\nResultado del análisis (JSON):")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nError en la ejecución: {e}")
