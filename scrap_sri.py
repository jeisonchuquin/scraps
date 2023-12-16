from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import pandas as pd
import random


## para poner formato al dataframe
def set_format_values(d_firmes_: pd.DataFrame):
    d_firmes = d_firmes_.copy()
    d_firmes[1] = d_firmes[1].str.replace('$', '')
    d_firmes[1] = d_firmes[1].str.replace(',', '')
    d_firmes[1] = d_firmes[1].astype('float')

    return d_firmes



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
        driver.find_element(By.XPATH,"//div[@class='col-sm-12 animated fadeInUp ng-star-inserted']")        
        bandera=1        
    except:
        try:
            driver.find_element(By.XPATH,"//span[contains(text(),'ciudadano /')]")
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
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH,"//input[@id='busquedaRucId']"))
    )
    
    
    input_id = driver.find_element(By.XPATH, "//input[@id='busquedaRucId']")
    input_id.clear()
    input_id.send_keys(cedula)
    
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH,"//button[@class='ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only cyan-btn']"))
    )
   
    log_button = driver.find_element(
        By.XPATH, "//button[@class='ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only cyan-btn']")
    log_button.click()

    sleep(5)        
    bandera=get_flag_captcha(driver)
    
    if bandera==0:    
        code = solveRecaptcha(
            "6Lc6rokUAAAAAJBG2M1ZM1LIgJ85DwbSNNjYoLDk",
            "https://srienlinea.sri.gob.ec/sri-en-linea/SriPagosWeb/ConsultaDeudasFirmesImpugnadas/Consultas/consultaDeudasFirmesImpugnadas"
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
    
        
    
    sleep(random.uniform(2, 3))
    # sacamos datos
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # div = soup.find_all(
    #     'div', class_='col-sm-12 animated fadeInUp ng-star-inserted')
    
    # driver.find_element(By.XPATH,"//span[contains(text(),'ciudadano')]")
    
    
    try:
        div = soup.find_all(
            'div', class_='col-sm-12 animated fadeInUp ng-star-inserted')
        
        tablas = pd.read_html(str(div))
        d_firmes = tablas[0]  # deudas firmes
        d_impug = tablas[1]  # deudas inpugandas
        f_pago = tablas[2]  # facilidades de pago
    
        d_firmes = set_format_values(d_firmes)
        d_impug = set_format_values(d_impug)
        f_pago = set_format_values(f_pago)
    
        data = [{'cedula': cedula,
                 'deduda_firme': d_firmes[1].sum(),
                 'deuda_impugnada':d_impug[1].sum(),
                 'facilidad_pago':f_pago[1].sum(),
                 'flag':1.0}]
        data = pd.DataFrame(data)
    
    except:
        try:
            driver.find_element(By.XPATH,"//span[contains(text(),'ciudadano /')]")
            data = [{'cedula': cedula,
                     'deduda_firme': 0.0,
                     'deuda_impugnada': 0.0,
                     'facilidad_pago': 0.0,
                     'flag':1.0}]
            data = pd.DataFrame(data)
        except:            
            data = [{'cedula': cedula,
                     'deduda_firme': 0.0,
                     'deuda_impugnada': 0.0,
                     'facilidad_pago': 0.0,
                     'flag':0.0}]
            data = pd.DataFrame(data)
    
    sleep(random.uniform(3, 4))
    driver.refresh()
    
    return data



## Para que intente 5 veces
def get_data_sri(cedula,driver):
    
    error = 0
    for i in range(5):
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
        valores = get_info_sri(cedula, driver)
        valor = valores.iloc[0,1:].sum()
        for i in range(2):
            if valor == 0:
                sleep(random.uniform(5, 7))
                try:
                    valores = get_info_sri(cedula, driver)
                    valor = valores.iloc[0,1:].sum()
                except:
                    valor = 0
            else:
                break
    else:
         valores = [{'cedula':cedula,
                     'deduda_firme':0.0,
                     'deuda_impugnada':0.0,
                     'facilidad_pago':0.0,
                     'flag':-1.0}] # la página no cargó el captcha
         valores = pd.DataFrame(valores)
    return valores    



##
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
chrome_options.add_argument('--no-sandbox')     
chrome_options.add_argument('--disable-dev-shm-usage') 
# chrome_options.add_argument("--headless")
# chrome_options.add_argument('--no-proxy-server')


driver = webdriver.Chrome(options=chrome_options)
driver.get('https://srienlinea.sri.gob.ec/sri-en-linea/SriPagosWeb/ConsultaDeudasFirmesImpugnadas/Consultas/consultaDeudasFirmesImpugnadas')


## test
cedula = '1712183845001'
cedula = '0201086568'
cedula = '0502268113'
get_data_sri(cedula, driver)


cedula = '0918863218'
get_data_sri(cedula,driver)

cedula = '1790007871001'    
z=get_data_sri(cedula, driver)


## Ejecucuión completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
data_sri=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    df_iter=get_data_sri(cedula, driver)
    data_sri=pd.concat([data_sri,df_iter],axis=0)

data_sri.reset_index(drop=True,inplace=True)

data_sri.to_excel('data_sri.xlsx',index=False)


###

from seleniumwire import webdriver
from fp.fp import FreeProxy

proxy = FreeProxy(country_id=['US', 'BR'], timeout=0.3).get()


wire_options = {
    'proxy': {
        'http': f'{proxy}',
        'https': f'{proxy}',
        'verify_ssl': False,
    },
}

driver = webdriver.Chrome(seleniumwire_options=wire_options)
# driver.get('http://httpbin.org/ip')
driver.get('https://srienlinea.sri.gob.ec/sri-en-linea/SriPagosWeb/ConsultaDeudasFirmesImpugnadas/Consultas/consultaDeudasFirmesImpugnadas')

