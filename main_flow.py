import os
import time
import json
import docx
from tabulate import tabulate

from profile_analyzer import ProfileAnalyzer
from scrapers import ComputrabajoScraper, ElEmpleoScraper, TorreScraper
from match_evaluator import MatchEvaluator
from cv_tailor import CVTailor
from email_notifier import EmailNotifier

def extraer_texto_docx(ruta_archivo: str) -> str:
    """Extrae todo el texto de un archivo DOCX de forma segura."""
    try:
        with open(ruta_archivo, 'rb') as f:
            doc = docx.Document(f)
            texto = ""
            for para in doc.paragraphs:
                texto += para.text + "\n"
            return texto
    except Exception as e:
        print(f"Error al leer el DOCX {ruta_archivo}: {e}")
        raise

def ejecutar_flujo_principal(docx_path: str, email_destino: str):
    if not os.path.exists(docx_path):
        raise Exception(f"No se encontró el archivo '{docx_path}'.")
        
    print(f"-> Leyendo el archivo temporal DOCX...")
    texto_hv = extraer_texto_docx(docx_path)
        
    if not texto_hv.strip():
        raise Exception("El documento está vacío o no se pudo extraer el texto.")
        
    print("-> Analizando el perfil con IA para encontrar cargos ideales...")
    analyzer = ProfileAnalyzer()
    analisis = analyzer.analyze_cv(texto_hv)
    cargos_ideales = analisis.get('cargos_recomendados', [])
    print(f"-> Cargos recomendados por la IA: {', '.join(cargos_ideales)}")
        
    if not cargos_ideales:
        raise Exception("No se encontraron cargos ideales para buscar.")
        
    scrapers_activos = [ComputrabajoScraper(), ElEmpleoScraper(), TorreScraper()]
    evaluator = MatchEvaluator()
    
    ofertas_filtradas = []
    total_ofertas_evaluadas = 0
    errores_scrapers = []
    
    print("\n" + "-"*40)
    print("INICIANDO BÚSQUEDA Y EVALUACIÓN DE OFERTAS")
    print("-"*40)
    
    for cargo in cargos_ideales:
        print(f"\n>>> Buscando ofertas para el cargo: '{cargo}'")
        ofertas_consolidadas = []
        
        for scraper in scrapers_activos:
            nombre_scraper = scraper.__class__.__name__
            print(f"  -> Consultando portal: {nombre_scraper}...")
            try:
                ofertas = scraper.buscar_ofertas(cargo)
                ofertas_consolidadas.extend(ofertas)
                print(f"  -> ¡Éxito! Se encontraron {len(ofertas)} ofertas en {nombre_scraper}.")
            except Exception as e:
                error_msg = f"Error al buscar ofertas para '{cargo}' con {nombre_scraper}: {e}"
                print(f"  -> [ERROR] {error_msg}")
                errores_scrapers.append(error_msg)
                continue
            
        print(f"\n>>> Evaluando {len(ofertas_consolidadas)} ofertas consolidadas para '{cargo}'...")
        for oferta in ofertas_consolidadas:
            total_ofertas_evaluadas += 1
            titulo = oferta.get('titulo_oferta', 'Sin título')
            empresa = oferta.get('empresa', 'Empresa desconocida')
            print(f"\n  [Oferta {total_ofertas_evaluadas}] Evaluando: '{titulo}' en '{empresa}'")
            
            try:
                descripcion_oferta = oferta.get('descripcion', '')
                if not descripcion_oferta or descripcion_oferta == 'No disponible':
                    print("    -> Oferta sin descripción, omitiendo.")
                    continue
                    
                print("    -> Analizando compatibilidad con IA...")
                resultado_json_str = evaluator.evaluar_oferta(texto_hv, descripcion_oferta)
                
                # Limpiar el string por si viene con formato markdown de código
                if resultado_json_str.startswith("```json"):
                    resultado_json_str = resultado_json_str[7:-3].strip()
                elif resultado_json_str.startswith("```"):
                    resultado_json_str = resultado_json_str[3:-3].strip()
                    
                resultado_evaluacion = json.loads(resultado_json_str)
                score = resultado_evaluacion.get('match_score', 0)
                
                print(f"    -> Score de compatibilidad obtenido: {score}/100")
                
                if score >= 65:
                    print("    -> ¡Oferta aprobada! (Score >= 65)")
                    ofertas_filtradas.append({
                        'Cargo Buscado': cargo,
                        'Título Oferta': titulo,
                        'Empresa': empresa,
                        'Score': score,
                        'URL': oferta.get('url_aplicacion', 'N/A'),
                        'Descripcion': descripcion_oferta
                    })
                else:
                    print("    -> Oferta descartada (Score < 65)")
            except Exception as e:
                print(f"    -> [ERROR] al evaluar la oferta: {e}")
                
            # Evitar bloqueos
            print("    -> Pausa de 5 segundos para evitar bloqueos de API...")
            time.sleep(5)
            
    print("\n" + "="*50)
    print("RESUMEN DEL PROCESO")
    print("="*50)
    print(f"Total de cargos buscados: {len(cargos_ideales)}")
    print(f"Total de ofertas evaluadas: {total_ofertas_evaluadas}")
    print(f"Total de ofertas con score >= 65: {len(ofertas_filtradas)}")
    print("="*50 + "\n")
    
    if total_ofertas_evaluadas == 0:
        mensaje_error = "No se encontraron ofertas en ninguno de los portales."
        if errores_scrapers:
            mensaje_error += "\nErrores reportados por los scrapers:\n" + "\n".join(errores_scrapers)
        raise Exception(mensaje_error)
    
    if ofertas_filtradas:
        # Ordenar por score descendente
        ofertas_filtradas.sort(key=lambda x: x['Score'], reverse=True)
        print("\nOFERTAS RECOMENDADAS:")
        print(tabulate(ofertas_filtradas, headers="keys", tablefmt="grid"))
        
        print("\n" + "-"*40)
        print("INICIANDO FASE 3: ADAPTACIÓN DE CV Y NOTIFICACIÓN")
        print("-" *40)
        tailor = CVTailor()
        
        # Configurar el notificador con el correo destino
        # Asumimos que EmailNotifier puede recibir el correo destino o lo configuramos
        # Si EmailNotifier no recibe el correo en el constructor, lo pasamos en enviar_oferta
        notifier = EmailNotifier()
        
        for i, oferta in enumerate(ofertas_filtradas, 1):
            print(f"\n>>> Procesando oferta recomendada {i}/{len(ofertas_filtradas)}")
            print(f"  -> Adaptando CV para: '{oferta['Título Oferta']}' en '{oferta['Empresa']}'...")
            try:
                descripcion = oferta.get('Descripcion', '')
                txt_path = tailor.adaptar_cv(texto_hv, descripcion, oferta['Empresa'])
                print(f"  -> ¡Sugerencias generadas con éxito! Guardadas en: {txt_path}")
                
                print(f"  -> Enviando notificación por correo a {email_destino}...")
                # Modificamos la llamada para incluir el email destino si es posible, 
                # o asumimos que el notificador usa el .env pero le pasamos el destino
                # Como no podemos ver EmailNotifier, intentaremos pasar el email_destino
                # Si falla, el usuario tendrá que ajustar EmailNotifier
                try:
                    notifier.enviar_oferta(
                        titulo=oferta['Título Oferta'],
                        empresa=oferta['Empresa'],
                        score=oferta['Score'],
                        url=oferta['URL'],
                        txt_path=txt_path,
                        destinatario=email_destino # Añadimos el destinatario
                    )
                    print("  -> ¡Correo enviado exitosamente!")
                except TypeError:
                    # Si enviar_oferta no acepta destinatario, llamamos sin él
                    print("  -> [ADVERTENCIA] EmailNotifier.enviar_oferta no acepta 'destinatario'. Usando configuración por defecto.")
                    notifier.enviar_oferta(
                        titulo=oferta['Título Oferta'],
                        empresa=oferta['Empresa'],
                        score=oferta['Score'],
                        url=oferta['URL'],
                        txt_path=txt_path
                    )
                    print("  -> ¡Correo enviado exitosamente (configuración por defecto)!")
            except Exception as e:
                print(f"  -> [ERROR] en la adaptación o notificación para esta oferta: {e}")
                
    else:
        print("\n[INFO] No se encontraron ofertas que cumplan con el puntaje mínimo (>= 65).")
