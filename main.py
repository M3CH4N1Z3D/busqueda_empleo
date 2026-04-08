import os
import sys
import time
import json
from pypdf import PdfReader
from tabulate import tabulate

from profile_analyzer import ProfileAnalyzer
from scrapers import ComputrabajoScraper, ElEmpleoScraper, TorreScraper
from match_evaluator import MatchEvaluator
from cv_tailor import CVTailor
from email_notifier import EmailNotifier

def extraer_texto_pdf(ruta_archivo: str) -> str:
    """Extrae todo el texto de un archivo PDF."""
    try:
        reader = PdfReader(ruta_archivo)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        print(f"Error al leer el PDF {ruta_archivo}: {e}")
        raise

def main():
    archivo_hv = "mi_hv.pdf"
    
    if not os.path.exists(archivo_hv):
        print(f"Error: No se encontró el archivo '{archivo_hv}' en el directorio raíz.")
        sys.exit(1)
        
    print(f"Leyendo el archivo {archivo_hv}...")
    try:
        texto_hv = extraer_texto_pdf(archivo_hv)
    except Exception:
        sys.exit(1)
        
    if not texto_hv.strip():
        print("Error: El PDF está vacío o no se pudo extraer el texto.")
        sys.exit(1)
        
    print("Analizando el perfil para encontrar cargos ideales...")
    try:
        analyzer = ProfileAnalyzer()
        analisis = analyzer.analyze_cv(texto_hv)
        cargos_ideales = analisis.get('cargos_recomendados', [])
        print(f"Cargos encontrados: {', '.join(cargos_ideales)}")
    except Exception as e:
        print(f"Error al analizar el perfil: {e}")
        sys.exit(1)
        
    if not cargos_ideales:
        print("No se encontraron cargos ideales para buscar.")
        sys.exit(1)
        
    scrapers_activos = [ComputrabajoScraper(), ElEmpleoScraper(), TorreScraper()]
    evaluator = MatchEvaluator()
    
    ofertas_filtradas = []
    total_ofertas_evaluadas = 0
    
    print("\nIniciando búsqueda y evaluación de ofertas...")
    
    for cargo in cargos_ideales:
        print(f"\nBuscando ofertas para: {cargo}")
        ofertas_consolidadas = []
        
        for scraper in scrapers_activos:
            try:
                ofertas = scraper.buscar_ofertas(cargo)
                ofertas_consolidadas.extend(ofertas)
                print(f"Se encontraron {len(ofertas)} ofertas para '{cargo}' con {scraper.__class__.__name__}.")
            except Exception as e:
                print(f"Error al buscar ofertas para '{cargo}' con {scraper.__class__.__name__}: {e}")
                continue
            
        for oferta in ofertas_consolidadas:
            total_ofertas_evaluadas += 1
            titulo = oferta.get('titulo_oferta', 'Sin título')
            empresa = oferta.get('empresa', 'Empresa desconocida')
            print(f"Evaluando oferta: {titulo} en {empresa}...")
            
            try:
                descripcion_oferta = oferta.get('descripcion', '')
                if not descripcion_oferta or descripcion_oferta == 'No disponible':
                    print("  -> Oferta sin descripción, omitiendo.")
                    continue
                    
                resultado_json_str = evaluator.evaluar_oferta(texto_hv, descripcion_oferta)
                
                # Limpiar el string por si viene con formato markdown de código
                if resultado_json_str.startswith("```json"):
                    resultado_json_str = resultado_json_str[7:-3].strip()
                elif resultado_json_str.startswith("```"):
                    resultado_json_str = resultado_json_str[3:-3].strip()
                    
                resultado_evaluacion = json.loads(resultado_json_str)
                score = resultado_evaluacion.get('match_score', 0)
                
                print(f"  -> Score obtenido: {score}")
                
                if score >= 65:
                    ofertas_filtradas.append({
                        'Cargo Buscado': cargo,
                        'Título Oferta': titulo,
                        'Empresa': empresa,
                        'Score': score,
                        'URL': oferta.get('url_aplicacion', 'N/A'),
                        'Descripcion': descripcion_oferta
                    })
            except Exception as e:
                print(f"  -> Error al evaluar la oferta: {e}")
                
            # Evitar bloqueos
            time.sleep(5)
            
    print("\n" + "="*50)
    print("RESUMEN DEL PROCESO")
    print("="*50)
    print(f"Total de cargos buscados: {len(cargos_ideales)}")
    print(f"Total de ofertas evaluadas: {total_ofertas_evaluadas}")
    print(f"Total de ofertas con score >= 65: {len(ofertas_filtradas)}")
    print("="*50 + "\n")
    
    if ofertas_filtradas:
        # Ordenar por score descendente
        ofertas_filtradas.sort(key=lambda x: x['Score'], reverse=True)
        print("OFERTAS RECOMENDADAS:")
        print(tabulate(ofertas_filtradas, headers="keys", tablefmt="grid"))
        
        print("\nIniciando Fase 3: Adaptación de CV y Notificación...")
        tailor = CVTailor()
        notifier = EmailNotifier()
        
        for oferta in ofertas_filtradas:
            print(f"\nAdaptando CV para: {oferta['Título Oferta']} en {oferta['Empresa']}...")
            try:
                # Necesitamos la descripción de la oferta, la cual no guardamos en ofertas_filtradas.
                # Vamos a modificar ofertas_filtradas para incluir la descripción.
                # Pero como ya está hecho el append arriba, lo modificaré en el siguiente paso.
                # Por ahora asumo que 'Descripcion' está en el diccionario.
                descripcion = oferta.get('Descripcion', '')
                pdf_path = tailor.adaptar_cv(texto_hv, descripcion, oferta['Empresa'])
                print(f"CV adaptado guardado en: {pdf_path}")
                
                print("Enviando notificación por correo...")
                notifier.enviar_oferta(
                    titulo=oferta['Título Oferta'],
                    empresa=oferta['Empresa'],
                    score=oferta['Score'],
                    url=oferta['URL'],
                    pdf_path=pdf_path
                )
            except Exception as e:
                print(f"Error en la adaptación o notificación para esta oferta: {e}")
                
    else:
        print("No se encontraron ofertas que cumplan con el puntaje mínimo (>= 65).")

if __name__ == "__main__":
    main()
