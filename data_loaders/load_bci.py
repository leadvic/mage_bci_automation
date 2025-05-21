from mage_ai.data_preparation.decorators import data_loader
from mage_ai.data_preparation.shared.secrets import get_secret_value

from pyvirtualdisplay import Display
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import os

@data_loader
def load_data(*args, **kwargs):
    def realizar_acciones_bancarias(url_banco_func, usuario_func, contrasena_func, pasos_navegacion_func, directorio_descargas_func):

        estado_final = "Error desconocido" # Para rastrear el resultado

        # Iniciar la pantalla virtual
        print("Iniciando pantalla virtual Xvfb...")
        display = Display(visible=0, size=(1920, 1080)) # visible=0 significa que no se muestra
        display.start()
        print("Pantalla virtual iniciada.")

        driver_func = None
        try:
            print("Intentando iniciar con undetected_chromedriver...")
            options_func = uc.ChromeOptions()

            # --- CONFIGURACIÓN DE DESCARGAS ---
            if not os.path.exists(directorio_descargas_func):
                os.makedirs(directorio_descargas_func)
                print(f"Directorio de descargas creado en: {directorio_descargas_func}")

            prefs = {
                "download.default_directory": directorio_descargas_func,
                "download.prompt_for_download": False, # No preguntar, solo descargar
                "download.directory_upgrade": True,
                "safeBrowse.enabled": True # Puede ser necesario para algunos sitios
            }
            options_func.add_experimental_option("prefs", prefs)
            # --- FIN CONFIGURACIÓN DE DESCARGAS ---

            options_func.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
            options_func.add_argument('--no-sandbox')
            options_func.add_argument('--disable-dev-shm-usage')
            options_func.add_argument('--window-size=1920,1080')
            options_func.add_argument("--disable-blink-features=AutomationControlled")

            driver_func = uc.Chrome(options=options_func, use_subprocess=True, enable_cdp_events=False)
            print("Navegador iniciado con undetected_chromedriver y configuración de descargas.")
            driver_func.get(url_banco_func)
            print(f"Navegando a: {url_banco_func}. Esperando posible desafío de Cloudflare...")
            time.sleep(10) # Espera inicial por si Cloudflare actúa

            wait_func = WebDriverWait(driver_func, 30) # Aumentar espera general si es necesario

            for i_func, paso_func in enumerate(pasos_navegacion_func):
                print(f"\nEjecutando paso {i_func+1}: {paso_func.get('descripcion', paso_func['accion'])}")
                # Pequeña espera para estabilizar, especialmente antes de cambiar de contexto o hacer clic
                time.sleep(paso_func.get('pre_espera_segundos', 1))


                try:
                    if paso_func['accion'] == 'escribir':
                        elemento_func = wait_func.until(EC.visibility_of_element_located(
                            (getattr(By, paso_func['tipo_selector'].upper()), paso_func['valor_selector'])
                        ))
                        elemento_func.clear()
                        for caracter_func in paso_func['valor_input']:
                            elemento_func.send_keys(caracter_func)
                            time.sleep(0.05)
                        print(f"Texto '{paso_func['valor_input'][:10]}...' escrito.")

                    elif paso_func['accion'] == 'click':
                        # Para clics, es mejor esperar a que sea 'element_to_be_clickable'
                        elemento_func = wait_func.until(EC.element_to_be_clickable(
                            (getattr(By, paso_func['tipo_selector'].upper()), paso_func['valor_selector'])
                        ))
                        driver_func.execute_script("arguments[0].scrollIntoView(true);", elemento_func) # Asegura visibilidad
                        time.sleep(0.5) # Pausa antes del clic
                        # Intento de clic robusto
                        try:
                            elemento_func.click()
                        except Exception as e_click_directo:
                            print(f"Clic directo falló: {e_click_directo}. Intentando clic con JavaScript...")
                            driver_func.execute_script("arguments[0].click();", elemento_func)
                        print(f"Click en elemento.")

                    elif paso_func['accion'] == 'esperar':
                        print(f"Esperando {paso_func['tiempo_segundos']} segundos...")
                        time.sleep(paso_func['tiempo_segundos'])

                    elif paso_func['accion'] == 'esperar_elemento':
                        print(f"Esperando elemento con {paso_func['tipo_selector']} '{paso_func['valor_selector']}'...")
                        tiempo_max_espera_elemento_func = paso_func.get('tiempo_max_espera', 30)
                        condicion = paso_func.get('condicion', 'presence') # presence, visible, clickable

                        if condicion == 'visible':
                            expected_condition = EC.visibility_of_element_located
                        elif condicion == 'element_to_be_clickable':
                            expected_condition = EC.element_to_be_clickable
                        else: # presence por defecto
                            expected_condition = EC.presence_of_element_located
                        
                        WebDriverWait(driver_func, tiempo_max_espera_elemento_func).until(expected_condition(
                            (getattr(By, paso_func['tipo_selector'].upper()), paso_func['valor_selector'])
                        ))
                        print("Elemento encontrado/listo.")

                    elif paso_func['accion'] == 'switch_to_iframe':
                        print(f"Intentando cambiar al iframe con {paso_func['tipo_selector']} '{paso_func['valor_selector']}'...")
                        tiempo_max_espera_iframe = paso_func.get('tiempo_max_espera', 20)
                        wait_iframe = WebDriverWait(driver_func, tiempo_max_espera_iframe)
                        
                        # Esperar a que el iframe esté presente antes de intentar cambiar
                        iframe_element = wait_iframe.until(EC.presence_of_element_located(
                            (getattr(By, paso_func['tipo_selector'].upper()), paso_func['valor_selector'])
                        ))
                        driver_func.switch_to.frame(iframe_element)
                        print("Cambiado al contexto del iframe.")
                        time.sleep(2) # Pequeña espera para que el contenido del iframe se asiente

                    elif paso_func['accion'] == 'switch_to_default_content':
                        driver_func.switch_to.default_content()
                        print("Vuelto al contenido principal de la página.")
                        time.sleep(1)


                except TimeoutException:
                    print(f"Error: Tiempo de espera agotado para el paso {i_func+1} ({paso_func.get('descripcion', 'N/A')}).")
                    if driver_func: driver_func.save_screenshot(f'error_paso_{i_func+1}_timeout.png')
                    estado_final = f"Timeout en paso {i_func+1}"
                    return estado_final # Salir de la función si un paso crucial falla
                except NoSuchElementException:
                    print(f"Error: No se pudo encontrar el elemento para el paso {i_func+1} ({paso_func.get('descripcion', 'N/A')}).")
                    if driver_func: driver_func.save_screenshot(f'error_paso_{i_func+1}_no_element.png')
                    estado_final = f"Elemento no encontrado en paso {i_func+1}"
                    return estado_final
                except StaleElementReferenceException:
                    print(f"Error: Elemento obsoleto (StaleElementReferenceException) en paso {i_func+1}. Reintentando localización o fallando.")
                    # Aquí podrías implementar un reintento si lo deseas, o simplemente fallar.
                    if driver_func: driver_func.save_screenshot(f'error_paso_{i_func+1}_stale.png')
                    estado_final = f"Elemento obsoleto en paso {i_func+1}"
                    return estado_final
                except Exception as e_func:
                    print(f"Error inesperado en paso {i_func+1} ({paso_func.get('descripcion', 'N/A')}): {e_func}")
                    if driver_func: driver_func.save_screenshot(f'error_paso_{i_func+1}_exception.png')
                    estado_final = f"Excepción en paso {i_func+1}: {str(e_func)[:100]}"
                    return estado_final
            
            estado_final = "Proceso completado (o al menos todos los pasos ejecutados)."
            print(f"\n{estado_final}")


        except Exception as e:
            print(f"Ocurrió un error: {e}")
            import traceback
            traceback.print_exc()
            if driver:
                driver.save_screenshot("error_xvfb_uc_test.png")
                print("Screenshot de error guardado en error_xvfb_uc_test.png")
        finally:
            if driver:
                driver.quit()
                print("Driver cerrado.")
            display.stop()
            print("Pantalla virtual Xvfb detenida.")
        return estado_final


    if __name__ == "__main__":
        directorio_descargas = os.path.join(os.getcwd(), "descargas_banco")

        url_login_banco = get_secret_value('bci_url')
        mi_rut = get_secret_value('rut')
        mi_clave = get_secret_value('bci_clave')

        pasos_para_llegar_a_pagina_objetivo = [
            # Login
            {
                'descripcion': 'Ingresar RUT', 'tipo_selector': 'id', 'valor_selector': 'rut_aux',
                'accion': 'escribir', 'valor_input': mi_rut, 'pre_espera_segundos': 2
            },
            {
                'descripcion': 'Ingresar contraseña', 'tipo_selector': 'id', 'valor_selector': 'clave',
                'accion': 'escribir', 'valor_input': mi_clave
            },
            {
                'descripcion': 'Click en botón de Ingresar', 'tipo_selector': 'xpath',
                'valor_selector': '//button[normalize-space()="Ingresar" and @type="submit"]', 'accion': 'click'
            },
            {
                'descripcion': 'Esperar carga post-login y posible redirección', 'accion': 'esperar',
                'tiempo_segundos': 12
            },
            {
                'descripcion': 'Esperar elemento clave del dashboard post-login', 'accion': 'esperar_elemento',
                'tipo_selector': 'id', 'valor_selector': 'page',
                'condicion': 'visible', 'tiempo_max_espera': 45
            },
            # Ir a la sección de Tarjetas y Mis movimientos
            {
                'descripcion': 'Click en enlace "Tarjetas"', 'tipo_selector': 'xpath',
                'valor_selector': '//a[@title="Tarjetas" and normalize-space()="Tarjetas"]', 'accion': 'click'
            },
            {
                'descripcion': 'Esperar a que "Mis movimientos" aparezca/sea clickeable', 'accion': 'esperar_elemento',
                'tipo_selector': 'xpath', 'valor_selector': '//a[@title="Mis movimientos" and normalize-space()="Mis movimientos"]',
                'condicion': 'element_to_be_clickable', 'tiempo_max_espera': 25 # Usar clickable
            },
            {
                'descripcion': 'Click en enlace "Mis movimientos"', 'tipo_selector': 'xpath',
                'valor_selector': '//a[@title="Mis movimientos" and normalize-space()="Mis movimientos"]',
                'accion': 'click'
            },
            # Esperar a que el iframe de contenido exista antes de intentar cambiar a él
            {
                'descripcion': 'Esperar a que el iframe de contenido ("iframeContenido") esté presente',
                'accion': 'esperar_elemento', 'tipo_selector': 'id', 'valor_selector': 'iframeContenido',
                'condicion': 'presence', 'tiempo_max_espera': 30
            },
            # Descargar Excel
            {
                'descripcion': 'Cambiar al contexto del iframe "iframeContenido"',
                'accion': 'switch_to_iframe', 'tipo_selector': 'id', 'valor_selector': 'iframeContenido'
            },
            {
                'descripcion': 'Esperar botón "Descargar Excel" en la página actual', 'accion': 'esperar_elemento',
                'tipo_selector': 'xpath',
                'valor_selector': "//a[contains(@class, 'bci-wk-button-with-icon') and starts-with(normalize-space(.), 'Descargar Excel')]",
                'condicion': 'element_to_be_clickable', 'tiempo_max_espera': 30
            },
            {
                'descripcion': 'Click en "Descargar Excel"', 'tipo_selector': 'xpath',
                'valor_selector': "//a[contains(@class, 'bci-wk-button-with-icon') and starts-with(normalize-space(.), 'Descargar Excel')]",
                'accion': 'click'
            },
            {
                'descripcion': 'Esperar a que la descarga del archivo comience/termine', 'accion': 'esperar',
                'tiempo_segundos': 10
            }
        ]
        resultado = realizar_acciones_bancarias(url_login_banco, mi_rut, mi_clave, pasos_para_llegar_a_pagina_objetivo, directorio_descargas)
        print(f"\nResultado final del proceso: {resultado}")

    return {}