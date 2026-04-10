import os
import json
from google import genai
from docxtpl import DocxTemplate
from docx2pdf import convert

class CVTailor:
    def __init__(self):
        self.client = genai.Client()
        self.model_id = "gemini-2.5-flash"
        
        # Asegurar que el directorio de salidas exista
        os.makedirs("salidas", exist_ok=True)

    def adaptar_cv(self, cv_base_text: str, job_description: str, empresa: str) -> str:
        prompt = (
            "Analiza el CV base y la oferta de trabajo. Devuelve un JSON con TRES claves: "
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
                "resumen_profesional": "Profesional con experiencia en el área, adaptando el perfil a los requerimientos de la oferta.",
                "aptitudes_clave": "Habilidades técnicas, Trabajo en equipo, Resolución de problemas",
                "exp_spark_team": "Experiencia en desarrollo y mantenimiento de aplicaciones, trabajando en equipo para lograr los objetivos del proyecto."
            }

        print(datos_cv)

        # Generar PDF desde Word
        pdf_path = self._generar_pdf_desde_word(datos_cv, empresa)
        return pdf_path

    def _generar_pdf_desde_word(self, json_data: dict, empresa: str) -> str:
        # Limpiar el nombre de la empresa para el archivo
        empresa_limpia = "".join(c if c.isalnum() else "_" for c in empresa)
        temp_docx_path = os.path.join("salidas", f"temp_HV_{empresa_limpia}.docx")
        pdf_path = os.path.join("salidas", f"HV_Adaptada_{empresa_limpia}.pdf")
        
        # Abrir plantilla
        plantilla_path = "plantilla_hv.docx"
        if not os.path.exists(plantilla_path):
            raise FileNotFoundError(f"No se encontró la plantilla: {plantilla_path}")
            
        doc = DocxTemplate(plantilla_path)
        
        lista_aptitudes = json_data.get('aptitudes_clave', [])
        if isinstance(lista_aptitudes, str):
            lista_aptitudes = [apt.strip() for apt in lista_aptitudes.split(',')] # Fallback por si devuelve string

        contexto = {
            'RESUMEN_PROFESIONAL': json_data.get('resumen_profesional', ''),
            'APTITUDES_CLAVE': lista_aptitudes,
            'EXP_SPARK_TEAM': json_data.get('exp_spark_team', '')
        }
        
        doc.render(contexto)
                
        # Guardar temporal
        doc.save(temp_docx_path)
        
        # --- REEMPLAZO UNIVERSAL PARA FORMAS, CUADROS DE TEXTO, ENCABEZADOS Y PIES DE PÁGINA ---
        # docxtpl a veces ignora marcadores dentro de formas (shapes) o cuadros de texto.
        # Esta lógica adicional asegura que cualquier marcador restante sea reemplazado preservando el formato.
        from docx import Document
        from docx.text.paragraph import Paragraph
        
        doc_manual = Document(temp_docx_path)
        
        # Formatear lista de aptitudes como viñetas para el reemplazo manual
        aptitudes_str = "\n• ".join(lista_aptitudes) if lista_aptitudes else ""
        if aptitudes_str and not aptitudes_str.startswith("•"):
            aptitudes_str = "• " + aptitudes_str
            
        replacements = {
            '{{ RESUMEN_PROFESIONAL }}': json_data.get('resumen_profesional', ''),
            '{{ APTITUDES_CLAVE }}': aptitudes_str,
            '{{ EXP_SPARK_TEAM }}': json_data.get('exp_spark_team', '')
        }
        
        # Buscar en todas las partes del documento (cuerpo principal, encabezados, pies de página)
        parts = [doc_manual.part]
        for rel in doc_manual.part.rels.values():
            if "header" in rel.reltype or "footer" in rel.reltype:
                parts.append(rel.target_part)
                
        for part in parts:
            element = part.element
            # Buscar todos los párrafos, incluyendo los que están dentro de cuadros de texto (w:txbxContent)
            for p_node in element.xpath('.//w:p'):
                p = Paragraph(p_node, part)
                for key, val in replacements.items():
                    while key in p.text:
                        # Encontrar el índice de inicio del marcador en el texto del párrafo
                        start_idx = p.text.find(key)
                        if start_idx == -1:
                            break
                            
                        # Mapear cada carácter del párrafo a su run correspondiente
                        run_mapping = []
                        for run_idx, run in enumerate(p.runs):
                            for char_idx in range(len(run.text)):
                                run_mapping.append((run_idx, char_idx))
                                
                        if not run_mapping or start_idx + len(key) > len(run_mapping):
                            break
                            
                        start_run_idx = run_mapping[start_idx][0]
                        end_run_idx = run_mapping[start_idx + len(key) - 1][0]
                        
                        if start_run_idx == end_run_idx:
                            # El marcador está completamente dentro de un solo run
                            run = p.runs[start_run_idx]
                            run.text = run.text.replace(key, str(val), 1)
                        else:
                            # El marcador está dividido en múltiples runs
                            for i in range(start_run_idx, end_run_idx + 1):
                                run = p.runs[i]
                                if i == start_run_idx:
                                    # Mantener el texto antes del marcador y añadir el reemplazo
                                    run_start_char = run_mapping[start_idx][1]
                                    run.text = run.text[:run_start_char] + str(val)
                                elif i == end_run_idx:
                                    # Mantener el texto después del marcador
                                    run_end_char = run_mapping[start_idx + len(key) - 1][1]
                                    run.text = run.text[run_end_char + 1:]
                                else:
                                    # Los runs intermedios se vacían
                                    run.text = ""
                                    
        doc_manual.save(temp_docx_path)
        # ---------------------------------------------------------------------------------------
        
        # Convertir a PDF
        try:
            convert(temp_docx_path, pdf_path)
        except Exception as e:
            print(f"Error al convertir a PDF: {e}")
            # Si falla la conversión, al menos dejamos el docx
            return temp_docx_path
        finally:
            # Eliminar temporal si existe
            if os.path.exists(temp_docx_path):
                try:
                    os.remove(temp_docx_path)
                except OSError as e:
                    print(f"No se pudo eliminar el archivo temporal {temp_docx_path}: {e}")
        
        return pdf_path
