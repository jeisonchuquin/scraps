from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from time import sleep
from datetime import date
import pandas as pd
import random
import re


def solveRecaptcha(sitekey, url):
    
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key("0cfd16d0d764c15019477c98c6ccba7f")
    solver.set_website_url(url)
    solver.set_website_key(sitekey)

    code = solver.solve_and_return_solution()


    return code




## PARA PONER EN FORMATO DATAFRAME
def get_demandas_table(table:list,cedula:str,nombre:str=None):
    demandas=pd.DataFrame()
    for i in range(0,len(table),2):
        # Nro. delito
        info_delito=table[i].copy()
        num_delito=info_delito.columns[0]
        num_delito=re.findall(r'\d+', num_delito)[0]
        
        info_delito.columns=['col'+'_'+str(i) for i in range(info_delito.shape[1])]
        
        # Delito
        delito=info_delito.loc[info_delito.col_1=='DELITO:','col_2'].iloc[0]
        
        # Lugar
        lugar=info_delito.loc[info_delito.col_1=='LUGAR','col_2'].iloc[0]
        
        # Fecha
        fecha_delito=info_delito.loc[info_delito.col_3=='FECHA','col_4'].iloc[0]
        fecha_delito=pd.to_datetime(fecha_delito,format='%Y-%m-%d')
        
        
        ## SUJETOS
        sujetos_info=table[i+1].copy()
        sujetos_info.columns=sujetos_info.columns.droplevel()
        
        if nombre!=None:
            nombre_=nombre.split(' ')
            nombre_='|'.join(nombre_)
            sujetos_info=sujetos_info[sujetos_info['NOMBRES COMPLETOS'].str.contains(nombre_,regex=True)]
            sujetos_info.loc[sujetos_info.CEDULA.isna(),'CEDULA']=cedula
            sujetos_info.loc[sujetos_info.CEDULA==0,'CEDULA']=cedula
            
        
        
        sujetos_info.dropna(subset='CEDULA',inplace=True)
        sujetos_info=sujetos_info[sujetos_info.CEDULA!='S/N']
        sujetos_info.CEDULA=sujetos_info.CEDULA.astype(int)
        sujetos_info=sujetos_info[sujetos_info.CEDULA==int(cedula)]    
        
        
        ## dataframe final
        sujetos_info['Fecha']=fecha_delito
        sujetos_info['Nro_delito']=num_delito
        sujetos_info['Delito']=delito
        sujetos_info['Lugar']=lugar
        sujetos_info.CEDULA=cedula
        
        demandas=pd.concat([demandas,sujetos_info],axis=0)
    
    return demandas



## PARA OBTENER LAS TABLAS EN HTML Y FORMATEAR
def get_demandas_ci_table(cedula:str,nombre:str,ced_del:bool,driver):
    
    driver.refresh()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID,'main-iframe'))    
        )
        
        driver.switch_to.frame('main-iframe')
        
        captcha_frame = driver.find_element(By.CSS_SELECTOR,'iframe[title="reCAPTCHA"]')
        driver.switch_to.frame(captcha_frame)
       
        driver.find_element(By.XPATH,"//div[@class='recaptcha-checkbox-border']").click()
        
        code = solveRecaptcha(
            "6Ld38BkUAAAAAPATwit3FXvga1PI6iVTb6zgXw62",
            "https://www.gestiondefiscalias.gob.ec/siaf/informacion/web/noticiasdelito/index.php"
        )
        
        
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
    except:
        pass
    ## aqui deberia de haber psasdo el captcha y mostrar la página de ingresar datos    
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,"//input[@id='pwd']"))
    )
    input_id = driver.find_element(By.XPATH, "//input[@id='pwd']")
    input_id.clear()
    if nombre==None:
        input_id.send_keys(cedula)
        flag=1
    elif len(nombre.strip().split(' '))>=4:
        input_id.send_keys(nombre)
        flag=1
    else:
        flag=0
    
    if flag==1:    
        login_button = driver.find_element(By.XPATH, "//input[@id='buscar' and contains(@value,'Denuncia')]")
        login_button.click()
        sleep(random.uniform(2, 3))
        
        # OBTENGO LOS DATAFRAMES
        html=driver.page_source
        soup=BeautifulSoup(html,'html.parser')
        div=soup.select_one("div#resultados")
        
        # Le eestrcutra html del div resultados
        try:
            table=pd.read_html(str(div))
            demandado1=get_demandas_table(table,cedula,nombre)
            demandado1.drop(columns='NOMBRES COMPLETOS',inplace=True)
            if ced_del:
                demandado1['ced_del']=demandado1.CEDULA+'_'+demandado1.Nro_delito
        except:
            demandado1=pd.DataFrame()
            
        return demandado1



## PARA OBTNER BASE CONSOLIDAD POR NOMBRE Y CEDULA
def get_fge_data(cedula:str,nombre:str,driver):
    # por nombre
    df_nombre=get_demandas_ci_table(cedula,nombre,True, driver)
    
    # por cedula
    df_cedula=get_demandas_ci_table(cedula,None,True, driver)
    
    df_full=pd.concat([df_nombre,df_cedula],axis=0)
    try:
        df_full.drop_duplicates(subset='ced_del',keep='first',inplace=True)
        df_full.drop(columns='ced_del',inplace=True)
    except:
        df_full=[{'CEDULA':cedula,
                  'ESTADO':'LIMPIO',
                  'Fecha':date.today(),
                  'Nro_delito':'Sin Delito',
                  'Delito':'Sin Delito',
                  'Lugar':'Sin Informacion'}]
        df_full=pd.DataFrame(df_full)
    
    return df_full



chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')     
chrome_options.add_argument('--disable-dev-shm-usage') 
driver = webdriver.Chrome(options=chrome_options) # REMPLAZA AQUI EL NOMBRE DE TU CHROME DRIVER
driver.get('https://www.gestiondefiscalias.gob.ec/siaf/informacion/web/noticiasdelito/index.php') # Voy a la pagina que requiero

## datos para testear
cedula='1313573998'        
nombre='ARAGUNDY SALTOS MARIA BELEN' ## 4 NOMBRES

# por nombre
df_nombre=get_demandas_ci_table(cedula,nombre,False, driver)

# por cedula
df_cedula=get_demandas_ci_table(cedula,None,False, driver)


## Ejecución completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
df_consol=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    nombre=documento.NOMBRE
    df_iter=get_fge_data(cedula,nombre,driver)
    
    df_consol=pd.concat([df_consol,df_iter],axis=0)

df_consol.reset_index(drop=True,inplace=True)

df_consol.to_excel('data_fiscalia.xlsx',index=False)



