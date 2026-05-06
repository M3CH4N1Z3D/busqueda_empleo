import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class TorreScraper(BaseScraper):
    def buscar_ofertas(self, cargo):
        ofertas = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, channel="msedge")
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Navegar a la página de búsqueda de Torre
                search_url = f"https://torre.ai/search/jobs?q={cargo.replace(' ', '%20')}"
                logger.info(f"Navegando a {search_url}")
                page.goto(search_url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000) # Espera adicional para SPA
                
                # Verificar si redirigió a login
                if "accounts.torre.ai" in page.url or "login" in page.url:
                    logger.warning("Torre requiere autenticación. No se pueden extraer ofertas sin iniciar sesión.")
                    return ofertas
                
                # Esperar a que carguen los resultados
                try:
                    page.wait_for_selector("a[href*='/post/']", timeout=15000)
                    page.wait_for_timeout(2000)
                except PlaywrightTimeoutError:
                    logger.warning("No se encontraron resultados o la página tardó demasiado en cargar.")
                    return ofertas
                
                # Obtener los enlaces de las ofertas
                enlaces_ofertas = page.locator("a[href*='/post/']").all()
                
                # Limitar a los primeros 3 resultados
                enlaces_procesar = enlaces_ofertas[:3]
                urls_ofertas = []
                
                for enlace in enlaces_procesar:
                    url = enlace.get_attribute("href")
                    if url and not url.startswith("http"):
                        url = f"https://torre.ai{url}"
                    if url:
                        urls_ofertas.append(url)
                
                logger.info(f"Se encontraron {len(urls_ofertas)} ofertas para procesar.")
                
                # Procesar cada oferta
                for url in urls_ofertas:
                    try:
                        logger.info(f"Procesando oferta: {url}")
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_timeout(3000) # Espera para SPA
                        
                        # Extraer título
                        titulo = "No especificado"
                        try:
                            titulo_element = page.locator("h1").first
                            if titulo_element.count() > 0:
                                titulo = titulo_element.inner_text().strip()
                        except Exception as e:
                            logger.warning(f"No se pudo extraer el título: {e}")
                            
                        # Extraer empresa
                        empresa = "No especificada"
                        try:
                            # En Torre, la empresa suele estar cerca del título o en un elemento específico
                            empresa_element = page.locator("div:has-text('Company'), div:has-text('Organization')").locator("..").locator("span, p, a").last
                            if empresa_element.count() > 0:
                                empresa = empresa_element.inner_text().strip()
                        except Exception as e:
                            logger.warning(f"No se pudo extraer la empresa: {e}")
                            
                        # Extraer descripción
                        descripcion = "No especificada"
                        try:
                            # Buscar el contenedor principal de la descripción
                            desc_element = page.locator("div.job-description, div[data-cy='job-description'], article").first
                            if desc_element.count() == 0:
                                desc_element = page.locator("main").first
                                
                            if desc_element.count() > 0:
                                descripcion = desc_element.inner_text().strip()
                        except Exception as e:
                            logger.warning(f"No se pudo extraer la descripción: {e}")
                            
                        ofertas.append({
                            "titulo_oferta": titulo,
                            "empresa": empresa,
                            "url_aplicacion": url,
                            "descripcion": descripcion
                        })
                        
                    except Exception as e:
                        logger.error(f"Error al procesar la oferta {url}: {e}")
                        continue
                        
            except PlaywrightTimeoutError:
                logger.error("Tiempo de espera agotado al cargar la página de Torre.")
            except Exception as e:
                logger.error(f"Error inesperado durante el scraping de Torre: {e}")
            finally:
                browser.close()
                
        return ofertas
