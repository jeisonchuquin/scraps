from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import pandas as pd

## solo funciona para personas naturales

## PARA PONER BIEN NOMBRES EN TABLAS
def set_correct_names(titulos_1_:pd.DataFrame, lennames:list):   
    
    titulos_1=titulos_1_.copy()
    for i in range(titulos_1.shape[1]):
        titulos_1.iloc[:,i]=titulos_1.iloc[:,i].apply(lambda row: row[lennames[i]:])
        
    return titulos_1




## Para resolver captcha
def solveRecaptcha(sitekey, url):
    
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key("0cfd16d0d764c15019477c98c6ccba7f")
    solver.set_website_url(url)
    solver.set_website_key(sitekey)

    code = solver.solve_and_return_solution()


    return code



## Para obtener bandera de captcha
def get_flag_captcha(driver):
        
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id = 'rc-imageselect']"))
        )        
        bandera=1
    except:
        bandera=0
        
    return bandera



## Para obtener nombre de funcion callback
def get_callback_anonymus(driver):
    
    call_function="""    
    function findRecaptchaClients() {
      if (typeof (___grecaptcha_cfg) !== 'undefined') {
        return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
          const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' }
          const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object')
    
          objects.forEach(([toplevelKey, toplevel]) => {
            const found = Object.entries(toplevel).find(([_, value]) => (
              value && typeof value === 'object' && 'sitekey' in value && 'size' in value
            ))
    
            if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV') {
              data.pageurl = toplevel.baseURI
            }
    
            if (found) {
              const [sublevelKey, sublevel] = found
    
              data.sitekey = sublevel.sitekey
              const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback'
              const callback = sublevel[callbackKey]
              if (!callback) {
                data.callback = null
                data.function = null
              } else {
                data.function = callback
                const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('')
                data.callback = `___grecaptcha_cfg.clients${keys}`
              }
            }
          })
          return data
        })
    
      }
      return []
    }
    """
    
    callback_dict=driver.execute_script(f"{call_function} return findRecaptchaClients()")
    callback_dict=pd.DataFrame(callback_dict)
    
    return callback_dict.callback.iloc[0]



## Para tratar de obtener la info una sola vez
def get_info_sri(cedula:str,driver):
    
    if len(cedula)==10:
        cedula+='001'
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH,"//input[@id='busquedaRucId']"))
    )
    
    
    input_id = driver.find_element(By.XPATH, "//input[@id='busquedaRucId']")
    input_id.clear()
    input_id.send_keys(cedula)
    driver.save_screenshot('./sri_contri_img/1_in_ruc.png') # a ver si puso el ruc
    
    try:        
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH,'//span[contains(text(),"no generó resultados")]'))
        )
        driver.save_screenshot('./sri_contri_img/in_no_genero.png') # a ver si salió mensaje de no generó
        
        info_final = {'RUC':cedula, 'RAZON_SOCIAL':'SIN INFO', 'ESTADO_CONTRIBUYENTE':'SIN INFO', 
                      'ACTIVIDAD_ECONOMICA':'SIN INFO', 'FANTASMA': 'SIN INFO',
                      'CONTRIBUYENTE_TRANSACCION':'SIN INFO', 'TIPO_CONTRIBUYENTE':'SIN INFO',
                      'REGIMEN':'SIN INFO', 'CATEGORIA':'SIN INFO', 'OBLIGADO_CONTABILIDAD':'SIN INFO',
                      'AGENTE_RETENCION':'SIN INFO','CONTRIBUYENTE_ESPECIAL':'SIN INFO',
                      'FECHA_INICIO':pd.Timestamp('1900-01-01') , 'FECHA_ACTUALIZACION':pd.Timestamp('1900-01-01'),
                      'FECHA_CESE':pd.Timestamp('1900-01-01'), 'FECHA_REINICIO':pd.Timestamp('1900-01-01'),
                      'NO_ESTABLECIMIENTO':'SIN INFO',
                      'NOMBRE_COMERCIAL':'SIN INFO', 'UBICACION':'SIN INFO',
                      'ESTADO_ESTABLECIMIENTO':'SIN INFO'}
        info_final = pd.DataFrame(info_final, index=[0])
        
        return info_final        
    
    except:
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH,"//button[@class='ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only cyan-btn']"))
            )
            driver.save_screenshot('./sri_contri_img/2_in_buscar.png') # a ver si se puso el boton en azul
        except:
            return pd.DataFrame() #para cuando salga error de github
        
   
    # log_button = driver.find_element(
    #     By.XPATH, "//button[@class='ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only cyan-btn']")
    # log_button.click()

    sleep(2)
    # bandera=get_flag_captcha(driver)
    
    bandera = 0
    if bandera==0:    
        code = solveRecaptcha(
            "6Lc6rokUAAAAAJBG2M1ZM1LIgJ85DwbSNNjYoLDk",
            "https://srienlinea.sri.gob.ec/sri-en-linea/SriRucWeb/ConsultaRuc/Consultas/consultaRuc"
        )
        
        # code = result
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'g-recaptcha-response'))
        )
        
        driver.execute_script(
            "document.getElementById('g-recaptcha-response').innerHTML = " + "'" + code + "'")
    
        sleep(1)
        
        render_captcha=get_callback_anonymus(driver)
        driver.execute_script(
        f"{render_captcha}('{code}')"
        )
        
        # el=driver.find_element(By.XPATH, '//sri-root[@role = "main"]')    

        # action = webdriver.common.action_chains.ActionChains(driver)
        # action.move_to_element_with_offset(el, 200, 200) # modo pantalla navegador
        # action.move_to_element_with_offset(el, 300, 300) # modo headless
        # action.click()
        # action.perform()
        
    
    # driver.save_screenshot('./sri_contri_img/in_resultado.png') # a ver si pasó el captcha y aparecen resultados
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH,'//span[contains(text(),"Mostrar establecimientos")]'))
    )   
    driver.save_screenshot('./sri_contri_img/3_in_resultado.png') # a ver si pasó el captcha y aparecen resultados       
    
    log_button = driver.find_element(
        By.XPATH, '//span[contains(text(),"Mostrar establecimientos")]')
    log_button.click()

    
    sleep(2)
    # sacamos datos
    html = driver.page_source    
    # soup = BeautifulSoup(html, 'html.parser')
    driver.save_screenshot('./sri_contri_img/4_in_esta.png') # a ver si pasó me dío establecimientos
    
    tablas_info = pd.read_html(str(html))
    
    actividad_eco = tablas_info[0].droplevel(level=0, axis=1).columns[0]
    tipo_contribuyente = tablas_info[1]
    tipo_contribuyente.columns = ['TIPO_CONTRIBUYENTE', 'REGIMEN', 'CATEGORIA']
    contabilidad = tablas_info[2]
    contabilidad.columns = ['OBLIGADO_CONTABILIDAD', 'AGENTE_RETENCION', 'CONTRIBUYENTE_ESPECIAL']
    fechas_act = tablas_info[3]
    fechas_act.columns = ['FECHA_INICIO', 'FECHA_ACTUALIZACION', 'FECHA_CESE', 'FECHA_REINICIO'] 
    fechas_act.fillna('1900-01-01', inplace=True)
    fechas_act = fechas_act.apply(pd.to_datetime)
    establecimientos = tablas_info[4]
    colnames=establecimientos.columns
    lennames=[len(i) for i in colnames]
    establecimientos=set_correct_names(establecimientos,lennames)
    establecimientos.columns = ['NO_ESTABLECIMIENTO', 'NOMBRE_COMERCIAL', 'UBICACION', 'ESTADO_ESTABLECIMIENTO'] 
    
    complementos = WebDriverWait(driver, 4).until(
        EC.presence_of_all_elements_located((By.XPATH, '//span[@class="titulo-consultas-1 tamano-defecto-campos"]'))
    )
    
    ruc = complementos[0].text
    razon_social = complementos[1].text
    fantasma = complementos[2].text
    transacciones = complementos[3].text
    estado = driver.find_element(By.XPATH, "//span[@class = 'verde']").text
    
    info_final = {'RUC':ruc, 'RAZON_SOCIAL':razon_social, 'ESTADO_CONTRIBUYENTE':estado,
              'ACTIVIDAD_ECONOMICA':actividad_eco, 'FANTASMA':fantasma, 
              'CONTRIBUYENTE_TRANSACCION':transacciones}
    info_final = pd.DataFrame(info_final, index=[0])
    
    info_final = pd.concat([info_final, tipo_contribuyente, contabilidad, 
                            fechas_act, establecimientos], axis=1)
    
    driver.refresh()
    
    return info_final



## Para que intente 5 veces
def get_data_sri(cedula,driver):
    
    error = 0
    for i in range(10):
        if error == 0:
            driver.refresh()
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[@title='reCAPTCHA']"))
                )
                error = 1
            except:
                error = 0
        else:
            break
        
    
    if error != 0:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='busquedaRucId']"))
        )
        
        info_final = get_info_sri(cedula, driver)
        for i in range(2):
            if info_final.empty:
                info_final = get_info_sri(cedula, driver)
            else:
                break
        
        if info_final.empty:
            info_final = {'RUC':cedula, 'RAZON_SOCIAL':'GIT ERROR', 'ESTADO_CONTRIBUYENTE':'SIN INFO', 
                          'ACTIVIDAD_ECONOMICA':'SIN INFO', 'FANTASMA': 'SIN INFO',
                          'CONTRIBUYENTE_TRANSACCION':'SIN INFO', 'TIPO_CONTRIBUYENTE':'SIN INFO',
                          'REGIMEN':'SIN INFO', 'CATEGORIA':'SIN INFO', 'OBLIGADO_CONTABILIDAD':'SIN INFO',
                          'AGENTE_RETENCION':'SIN INFO','CONTRIBUYENTE_ESPECIAL':'SIN INFO',
                          'FECHA_INICIO':pd.Timestamp('1900-01-01') , 'FECHA_ACTUALIZACION':pd.Timestamp('1900-01-01'),
                          'FECHA_CESE':pd.Timestamp('1900-01-01'), 'FECHA_REINICIO':pd.Timestamp('1900-01-01'),
                          'NO_ESTABLECIMIENTO':'SIN INFO',
                          'NOMBRE_COMERCIAL':'SIN INFO', 'UBICACION':'SIN INFO',
                          'ESTADO_ESTABLECIMIENTO':'SIN INFO'}
            info_final = pd.DataFrame(info_final, index=[0])
            
        
    else:
         info_final = {'RUC':cedula, 'RAZON_SOCIAL':'NO CAPTCHA', 'ESTADO_CONTRIBUYENTE':'SIN INFO', 
                       'ACTIVIDAD_ECONOMICA':'SIN INFO', 'FANTASMA': 'SIN INFO',
                       'CONTRIBUYENTE_TRANSACCION':'SIN INFO', 'TIPO_CONTRIBUYENTE':'SIN INFO',
                       'REGIMEN':'SIN INFO', 'CATEGORIA':'SIN INFO', 'OBLIGADO_CONTABILIDAD':'SIN INFO',
                       'AGENTE_RETENCION':'SIN INFO','CONTRIBUYENTE_ESPECIAL':'SIN INFO',
                       'FECHA_INICIO':pd.Timestamp('1900-01-01') , 'FECHA_ACTUALIZACION':pd.Timestamp('1900-01-01'),
                       'FECHA_CESE':pd.Timestamp('1900-01-01'), 'FECHA_REINICIO':pd.Timestamp('1900-01-01'),
                       'NO_ESTABLECIMIENTO':'SIN INFO',
                       'NOMBRE_COMERCIAL':'SIN INFO', 'UBICACION':'SIN INFO',
                       'ESTADO_ESTABLECIMIENTO':'SIN INFO'}
         info_final = pd.DataFrame(info_final, index=[0])
    
    return info_final    



##
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--incognito")
# chrome_options.add_argument('--no-sandbox')     
# chrome_options.add_argument('--disable-dev-shm-usage') 
chrome_options.add_argument("--headless")
# chrome_options.add_argument('--no-proxy-server')


driver = webdriver.Chrome(chrome_options)
driver.get('https://srienlinea.sri.gob.ec/sri-en-linea/SriRucWeb/ConsultaRuc/Consultas/consultaRuc')
driver.set_window_size(1920, 1080)

## test
cedula = '1712183845001'
cedula = '0201086568'
cedula = '0502268113'
cedula = '0200576551'
z = get_data_sri(cedula, driver)
driver.quit()

