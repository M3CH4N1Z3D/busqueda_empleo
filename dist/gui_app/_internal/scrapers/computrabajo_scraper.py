import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from .base_scraper import BaseScraper

class ComputrabajoScraper(BaseScraper):
    def __init__(self):
        # URL base configurada para Bogotá, Colombia
        self.base_url = "https://co.computrabajo.com/empleos-en-bogota-dc"

    def _random_delay(self):
        """Genera un delay aleatorio entre 2 y 5 segundos para mitigar bloqueos."""
        delay = random.uniform(2.0, 5.0)
        time.sleep(delay)

    def buscar_ofertas(self, cargo):
        """
        Busca ofertas de trabajo para un cargo específico y extrae los primeros 10 resultados.
        """
        resultados = []
        
        with sync_playwright() as p:
            # Lanzar navegador en modo no headless para ver el proceso
            browser = p.chromium.launch(headless=False, channel="msedge")
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                print(f"Navegando a {self.base_url}...")
                page.goto(self.base_url, timeout=60000)
                self._random_delay()

                # Buscar el input de cargo
                print(f"Buscando el cargo: {cargo}")
                search_input = page.locator("input#prof-cat-search-input")
                if not search_input.is_visible():
                    search_input = page.locator("input[placeholder*='Cargo']")
                
                search_input.fill(cargo)
                self._random_delay()

                # Hacer clic en el botón de buscar
                search_button = page.locator("button#search-button")
                if not search_button.is_visible():
                    search_button = page.locator("button:has-text('Buscar')")
                
                search_button.click()
                self._random_delay()

                # Esperar a que carguen los resultados (artículos de ofertas)
                try:
                    page.wait_for_selector("article.box_offer", timeout=15000)
                except PlaywrightTimeoutError:
                    print("No se encontraron resultados o la página tardó mucho en cargar.")
                    return resultados
                
                # Obtener los enlaces de las primeras 10 ofertas orgánicas
                ofertas_locators = page.locator("article.box_offer a.js-o-link").all()
                enlaces_ofertas = []
                
                for loc in ofertas_locators:
                    href = loc.get_attribute("href")
                    if href and href not in enlaces_ofertas:
                        enlaces_ofertas.append(href)
                    if len(enlaces_ofertas) >= 10:
                        break

                print(f"Se encontraron {len(enlaces_ofertas)} ofertas para analizar.")

                # Iterar sobre los enlaces extraídos para obtener el detalle
                for href in enlaces_ofertas:
                    url_oferta = f"https://co.computrabajo.com{href}" if href.startswith("/") else href
                    print(f"Analizando oferta: {url_oferta}")
                    
                    oferta_page = context.new_page()
                    try:
                        oferta_page.goto(url_oferta, timeout=30000)
                        self._random_delay()

                        # Inicializar datos por defecto
                        titulo = "No disponible"
                        empresa = "No disponible"
                        descripcion = "No disponible"

                        # Extraer título
                        try:
                            titulo_loc = oferta_page.locator("h1.fwB.fs24.mb5.box_detail_po").first
                            if not titulo_loc.is_visible():
                                titulo_loc = oferta_page.locator("h1").first
                            if titulo_loc.is_visible():
                                titulo = titulo_loc.inner_text().strip()
                        except Exception as e:
                            print(f"Error extrayendo título: {e}")

                        # Espera explícita para asegurar que el contenido cargó
                        try:
                            oferta_page.wait_for_selector('p:has-text("Descripción de la oferta"), h2:has-text("Descripción de la oferta"), .box_detail', timeout=5000)
                        except PlaywrightTimeoutError:
                            print("Timeout esperando el contenido de la oferta.")

                        # Extraer empresa
                        try:
                            empresa_loc = oferta_page.locator("h1 + p, h1 + a, .empresa, .company").first
                            if not empresa_loc.is_visible():
                                empresa_loc = oferta_page.locator("a.fs16.fwB").first
                            if not empresa_loc.is_visible():
                                empresa_loc = oferta_page.locator("p.fs16.fwB").first
                            if empresa_loc.is_visible():
                                empresa = empresa_loc.inner_text().strip()
                        except Exception as e:
                            print(f"Error extrayendo empresa: {e}")

                        # Extraer descripción
                        try:
                            descripcion = oferta_page.evaluate("""() => {
                                const headers = Array.from(document.querySelectorAll('*')).filter(el => el.textContent.trim() === 'Descripción de la oferta');
                                if(headers.length > 0) {
                                    let content = '';
                                    let nextEl = headers[0].nextElementSibling;
                                    while(nextEl) {
                                        content += nextEl.innerText + '\\n';
                                        nextEl = nextEl.nextElementSibling;
                                    }
                                    return content.trim();
                                }
                                return 'No disponible';
                            }""")
                        except Exception as e:
                            print(f"Error extrayendo descripción: {e}")

                        resultados.append({
                            "titulo_oferta": titulo,
                            "empresa": empresa,
                            "url_aplicacion": url_oferta,
                            "descripcion": descripcion
                        })

                    except Exception as e:
                        print(f"Error al procesar la oferta {url_oferta}: {e}")
                    finally:
                        oferta_page.close()
                        self._random_delay()

            except Exception as e:
                print(f"Ocurrió un error general durante la búsqueda: {e}")
            finally:
                browser.close()

        return resultados

if __name__ == '__main__':
    scraper = ComputrabajoScraper()
    cargo_prueba = 'Desarrollador Python Junior'
    print(f"Iniciando prueba de scraping para: {cargo_prueba}")
    
    datos = scraper.buscar_ofertas(cargo_prueba)
    
    print("\n--- Resultados Obtenidos ---")
    for i, dato in enumerate(datos, 1):
        print(f"\nOferta {i}:")
        print(f"Título: {dato['titulo_oferta']}")
        print(f"Empresa: {dato['empresa']}")
        print(f"URL: {dato['url_aplicacion']}")
        print(f"Descripción (primeros 500 caracteres): {dato['descripcion'][:500]}...")
