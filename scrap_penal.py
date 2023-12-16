from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import pandas as pd
import random


## espacio para captcha
def solveRecaptcha(sitekey, url):
    
    solver = recaptchaV2Proxyless()    
    solver.set_verbose(1)
    solver.set_key("0cfd16d0d764c15019477c98c6ccba7f")
    solver.set_website_url(url)
    solver.set_website_key(sitekey)

    code = solver.solve_and_return_solution()


    return code




def bypass_captcha_antecedentes(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID,'main-iframe'))    
    )
    
    driver.switch_to.frame('main-iframe')
    
    captcha_frame = driver.find_element(By.CSS_SELECTOR,'iframe[title="reCAPTCHA"]')
    driver.switch_to.frame(captcha_frame)

    driver.find_element(By.XPATH,"//div[@class='recaptcha-checkbox-border']").click()
       
    code = solveRecaptcha(
        "6Ld38BkUAAAAAPATwit3FXvga1PI6iVTb6zgXw62",
        "https://certificados.ministeriodelinterior.gob.ec/gestorcertificados/antecedentes/"
    )

    # code = result['code']
    
    driver.switch_to.default_content()
    driver.switch_to.frame('main-iframe')

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'g-recaptcha-response'))
    )
    
    driver.execute_script(
        "document.getElementById('g-recaptcha-response').innerHTML = " + "'" + code + "'"
    )
    sleep(1)
    driver.execute_script(
        "onCaptchaFinished(" + "'" + code + "')"
    )
    
    # driver.refresh()
    
    pass



##
def get_info_antecedentes(cedula:str,driver):    
    driver.execute_script("document.body.style.zoom='100%'")

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,"//a[@aria-label = 'dismiss cookie message']"))
         )
        driver.find_element(By.XPATH,"//a[@aria-label = 'dismiss cookie message']").click()
        
    except:
        pass        
    

    sleep(random.uniform(2, 3))
    ## luego de haver aprobado el captcha
    input_id=driver.find_element(By.XPATH,"//button[contains(@class,'ui-button')]//span[contains(text(),'Aceptar')]")
    input_id.click()
    
    sleep(random.uniform(2, 3))
    ##    
    input_ced=driver.find_element(By.XPATH,"//input[@id='txtCi']")
    input_ced.clear() # Le hago clear a los inputs para escribir siempre desde cero
    input_ced.send_keys(cedula) # ingreso cada elemento del documento
    
    sleep(random.uniform(2, 3))
    ## boton siguiente
    log_button=driver.find_element(By.XPATH,"//button[@id='btnSig1']")
    log_button.click()
    
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH,"//div[@id='tab2' and @style='']"))
     )  
 
    
    ## llenamos motivo
    fill_text=driver.find_element(By.XPATH,"//textarea[@id='txtMotivo']")
    motivo=['Consulta de demanda','Demandado consulta','Consulta de interes',
            'Consulta algo','Consulta de testo','Certificado antecedentes',
            'Motivo personal','Curiosidad antecedentes']
    pos=int(random.uniform(1,8))
    
    fill_text.send_keys(motivo[pos])
    
    sleep(random.uniform(2, 3))
    ## click en siguiente
    log_button=driver.find_element(By.XPATH,"//button[@id='btnSig2']")
    log_button.click()
    
    ## sacamos info
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    
    div=soup.find('div',id='tab3')
    info_general=pd.read_html(str(div))[0]
    
    ## damos formato de dataframe
    antecedentes=info_general.loc[info_general[0].str.contains('Antecedentes'),1].iloc[0]
    data=[{'cedula':cedula,
          'antecedentes':antecedentes}]
    data=pd.DataFrame(data)
    
    sleep(random.uniform(2, 3))
    driver.refresh()
    
    return data



def get_data_antecedentes(cedula:str,driver):
    flag=0
    for i in range(3):
        if flag==0:
            try:
                data=get_info_antecedentes(cedula, driver)
                flag=1
            except:
                try:
                    driver.refresh()
                    bypass_captcha_antecedentes(driver)
                    sleep(3)
                    data=get_info_antecedentes(cedula, driver)
                    flag=1
                except:
                    data=pd.DataFrame([{'cedula':cedula,
                                        'antecedentes':'ERROR'}])
                    flag=0

    return data
        



chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--no-sandbox')     
# chrome_options.add_argument('--disable-dev-shm-usage') 
driver = webdriver.Chrome(options=chrome_options)
driver.get('https://certificados.ministeriodelinterior.gob.ec/gestorcertificados/antecedentes/') # Voy a la pagina que requiero
driver.set_window_size(1366, 768)
## test
cedula='0601025687'
test=get_data_antecedentes(cedula,driver)



## Ejecucuión completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
data_penal=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    df_iter=get_info_antecedentes(cedula, driver)
    data_penal=pd.concat([data_penal,df_iter],axis=0)

data_penal.reset_index(drop=True,inplace=True)

data_penal.to_excel('data_penal.xlsx',index=False)

