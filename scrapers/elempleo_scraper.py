import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ElEmpleoScraper(BaseScraper):
    def buscar_ofertas(self, cargo):
        ofertas = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Navegar a la página de búsqueda
                search_url = "https://www.elempleo.com/co/ofertas-empleo/"
                logger.info(f"Navegando a {search_url}")
                page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                
                # Buscar explícitamente el input del buscador
                logger.info(f"Buscando cargo: {cargo}")
                page.fill('input.js-search-input, input[type="search"], input[placeholder*="Cargo"], input[placeholder*="cargo"]', cargo)
                page.keyboard.press('Enter')
                
                # Esperar a que carguen los resultados reales
                page.wait_for_timeout(3000)
                
                # Esperar a que carguen los resultados
                try:
                    page.wait_for_selector('.result-item', timeout=15000)
                except PlaywrightTimeoutError:
                    logger.warning("No se encontraron resultados con '.result-item', intentando selectores alternativos.")
                
                # Extraer los 10 primeros resultados
                resultados = page.query_selector_all('.result-item')
                if not resultados:
                    # Fallback selector
                    resultados = page.query_selector_all('.job-item')
                
                resultados = resultados[:10]
                
                enlaces_ofertas = []
                for resultado in resultados:
                    try:
                        titulo_elem = resultado.query_selector('h2.text-ellipsis a, h2 a, .job-title a')
                        empresa_elem = resultado.query_selector('.info-company-name, .company-name')
                        
                        if titulo_elem:
                            titulo_oferta = titulo_elem.inner_text().strip()
                            href = titulo_elem.get_attribute('href')
                            url_aplicacion = href if href.startswith('http') else "https://www.elempleo.com" + href
                            empresa = empresa_elem.inner_text().strip() if empresa_elem else "Empresa confidencial"
                            
                            enlaces_ofertas.append({
                                'titulo_oferta': titulo_oferta,
                                'empresa': empresa,
                                'url_aplicacion': url_aplicacion
                            })
                    except Exception as e:
                        logger.error(f"Error extrayendo info de la lista: {e}")
                
                # Extraer detalle de cada oferta
                total_ofertas = len(enlaces_ofertas)
                for i, oferta in enumerate(enlaces_ofertas, 1):
                    try:
                        print(f"Analizando oferta {i} de {total_ofertas}...")
                        logger.info(f"Extrayendo detalle de {oferta['url_aplicacion']}")
                        page.goto(oferta['url_aplicacion'], wait_until='domcontentloaded', timeout=60000)
                        
                        # Esperar a que cargue la descripción
                        page.wait_for_timeout(2000) # Espera explícita
                        
                        descripcion = ""
                        try:
                            # Intentar con selector de clase
                            desc_elem = page.wait_for_selector('.description-block, .job-description', timeout=5000)
                            if desc_elem:
                                descripcion = desc_elem.inner_text().strip()
                        except PlaywrightTimeoutError:
                            # Fallback con evaluate
                            descripcion = page.evaluate('''() => {
                                const headers = Array.from(document.querySelectorAll('h2, h3, strong'));
                                const targetHeader = headers.find(h => 
                                    h.textContent.includes('Descripción de la oferta') || 
                                    h.textContent.includes('Perfil requerido') ||
                                    h.textContent.includes('Descripción')
                                );
                                if (targetHeader && targetHeader.nextElementSibling) {
                                    return targetHeader.parentElement.innerText;
                                }
                                const container = document.querySelector('.container-fluid, .main-content');
                                return container ? container.innerText : document.body.innerText;
                            }''')
                        
                        oferta['descripcion'] = descripcion
                        ofertas.append(oferta)
                        
                    except Exception as e:
                        logger.error(f"Error extrayendo detalle de la oferta {oferta['url_aplicacion']}: {e}")
                        oferta['descripcion'] = "No se pudo extraer la descripción."
                        ofertas.append(oferta)
                        
            except Exception as e:
                logger.error(f"Error general en ElEmpleoScraper: {e}")
            finally:
                browser.close()
                
        return ofertas
