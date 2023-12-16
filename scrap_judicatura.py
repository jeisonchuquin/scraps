import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import pandas as pd
import numpy as np

#Descargar webdriver de esta pagina https://selenium-python.readthedocs.io/installation.html#drivers


def get_data_ci_esatje(cedula:str,driver):
    # driver = webdriver.Chrome('./chromedriver') # REMPLAZA AQUI EL NOMBRE DE TU CHROME DRIVER
    # driver.get('https://procesosjudiciales.funcionjudicial.gob.ec/expel-juicios')

    driver.refresh()

    input_id = driver.find_element(By.XPATH, './/input[@id="mat-input-3"]') # instancio el xpath en donde se van a ingresar los valores
    input_id.clear() # Le hago clear a los inputs para escribir siempre desde cero
    input_id.send_keys(cedula) # ingreso cada elemento del documento

    login_button = driver.find_element(By.XPATH, './/button[@aria-label="Enviar formulario"]') # Busco el boton consultar
    login_button.click() # Le doy click

    sleep(random.uniform(2, 3)) # freno cada consulta en diferentes tiempo, esto sirve para que la página no reconozca ningun patrón de consulta
    
    try: # Me permite reconocer un error cuando no hay datos en la tabla, luego utilizo except para generar una instrucción 
        # Espero a que aparezca todo el contenido
        #demandas = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="form1:dataTableJuicios2_data"]//td[@role="gridcell"]')))
        demandas = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="cuerpo"]')))
        flag=1
        
    except: # Me sirve para generar una tabla predeterminada en caso de no hallar contenido en la tabla de consulta
        no_result = ['No presenta demandas judiciales']
        # cedula = [cedula]
       # no_dem =[]
        # ced_proce = [cedula[0] + no_result[0]]
        #for no in no_result:
        #    no_dem.append(no) # .text me ayuda a guardar los elementos como texto, sino se guardan como WebElement
        df = pd.DataFrame({'cedula': [cedula], 'numero': [0], 'fecha': [pd.to_datetime('1900-01-01')], 
                            'proceso': [np.nan], 'infraccion': ['NaN'], 'detalle': no_result, 'ced_pro': [cedula+'_'+'sin_info']})
        # print(df2)
        # df_consol = df_consol.append(df2, ignore_index=True)
        
        flag=0
        
        pass

    # demandas1 = list() # Guardo cada elemento escrapeado en una lista como texto
    if flag==1:
        # for demanda in demandas: # demandas:list, len=0, puede ser que len()>1
        #     demandas1.append(demanda.text) # .text me ayuda a guardar los elementos como texto, sino se guardan como WebElement
        
        demandas1 = demandas[0].text
        demandas1 = demandas1.split('\n')
        
        numero =[]
        fecha =[]
        proceso =[]
        infraccion =[]
        detalle =[]
        # ced_pro =[]
        # cedula_ = []
        
        for i in range(0, len(demandas1), 5):
            numero.append(demandas1[i])
            fecha.append(pd.to_datetime(demandas1[i+1],format='%d/%m/%Y'))
            proceso.append(demandas1[i+2])
            infraccion.append(demandas1[i+3])
            detalle.append(demandas1[i+4])
            # cedula_.append(cedula)
            
        # df = pd.DataFrame({'cedula':cedula, 'numero': numero, 'fecha': fecha, 'proceso': proceso, 'infraccion': infraccion, 'detalle': detalle})
        df = pd.DataFrame({ 'numero': numero, 'fecha': fecha, 'proceso': proceso, 'infraccion': infraccion, 'detalle': detalle})
        df.insert(loc=0, column='cedula', value=cedula)
        df['ced_pro']=df.cedula+'_'+df.proceso
        
        login_button2 = driver.find_element(By.XPATH, './/button[@class="botones btn-regresar mdc-button mat-mdc-button mat-primary mat-mdc-button-base"]') # Busco el boton consultar
        login_button2.click() # Le doy click
        sleep(random.uniform(2, 3)) # freno cada consulta en diferentes tiempo, esto sirve para que la página no reconozca ningun patrón de consulta

        
    
    return df
        


def get_data_name_esatje(cedula:str,nombre:str,driver):
    # driver = webdriver.Chrome('./chromedriver') # REMPLAZA AQUI EL NOMBRE DE TU CHROME DRIVER
    # driver.get('https://procesosjudiciales.funcionjudicial.gob.ec/expel-juicios')
    
    name_sep=nombre.strip().split(' ')
    if len(name_sep)>=4:
        driver.refresh()

        input_id = driver.find_element(By.XPATH, './/input[@id="mat-input-4"]') # instancio el xpath en donde se van a ingresar los valores
        input_id.clear() # Le hago clear a los inputs para escribir siempre desde cero
        input_id.send_keys(nombre) # ingreso cada elemento del documento
    
        login_button = driver.find_element(By.XPATH, './/button[@aria-label="Enviar formulario"]') # Busco el boton consultar
        login_button.click() # Le doy click
    
        sleep(random.uniform(2, 3)) # freno cada consulta en diferentes tiempo, esto sirve para que la página no reconozca ningun patrón de consulta
        
        try: # Me permite reconocer un error cuando no hay datos en la tabla, luego utilizo except para generar una instrucción 
            # Espero a que aparezca todo el contenido
            #demandas = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="form1:dataTableJuicios2_data"]//td[@role="gridcell"]')))
            demandas = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="cuerpo"]')))
            flag=1
            
        except: # Me sirve para generar una tabla predeterminada en caso de no hallar contenido en la tabla de consulta
            no_result = ['No presenta demandas judiciales']
            # cedula = [cedula]
           # no_dem =[]
            # ced_proce = [cedula[0] + no_result[0]]
            #for no in no_result:
            #    no_dem.append(no) # .text me ayuda a guardar los elementos como texto, sino se guardan como WebElement
            df = pd.DataFrame({'cedula': [cedula], 'numero': [0], 'fecha': [pd.to_datetime('1900-01-01')], 
                                'proceso': [np.nan], 'infraccion': ['NaN'], 'detalle': no_result, 'ced_pro': [cedula+'_'+'sin_info']})
            # print(df2)
            # df_consol = df_consol.append(df2, ignore_index=True)
            
            flag=0
            
            pass
    
        # demandas1 = list() # Guardo cada elemento escrapeado en una lista como texto
        if flag==1:
            # for demanda in demandas: # demandas:list, len=0, puede ser que len()>1
            #     demandas1.append(demanda.text) # .text me ayuda a guardar los elementos como texto, sino se guardan como WebElement
            
            demandas1 = demandas[0].text
            demandas1 = demandas1.split('\n')
            
            numero =[]
            fecha =[]
            proceso =[]
            infraccion =[]
            detalle =[]
            # ced_pro =[]
            # cedula_ = []
            
            for i in range(0, len(demandas1), 5):
                numero.append(demandas1[i])
                fecha.append(pd.to_datetime(demandas1[i+1],format='%d/%m/%Y'))
                proceso.append(demandas1[i+2])
                infraccion.append(demandas1[i+3])
                detalle.append(demandas1[i+4])
                # cedula_.append(cedula)
                
            # df = pd.DataFrame({'cedula':cedula, 'numero': numero, 'fecha': fecha, 'proceso': proceso, 'infraccion': infraccion, 'detalle': detalle})
            df = pd.DataFrame({ 'numero': numero, 'fecha': fecha, 'proceso': proceso, 'infraccion': infraccion, 'detalle': detalle})
            df.insert(loc=0, column='cedula', value=cedula)
            df['ced_pro']=df.cedula+'_'+df.proceso
            
            login_button2 = driver.find_element(By.XPATH, './/button[@class="botones btn-regresar mdc-button mat-mdc-button mat-primary mat-mdc-button-base"]') # Busco el boton consultar
            login_button2.click() # Le doy click
            sleep(random.uniform(2, 3)) # freno cada consulta en diferentes tiempo, esto sirve para que la página no reconozca ningun patrón de consulta

            
        
        return df



def get_data_scrap_esatje(cedula:str,nombre:str,drive):
    df_cedula=get_data_ci_esatje(cedula, driver)
    sleep(random.uniform(2, 3))
    df_name=get_data_name_esatje(cedula, nombre, driver)
    
    df_final=pd.concat([df_cedula,df_name],axis=0)
    df_final.drop_duplicates(subset='ced_pro',keep='first',inplace=True)
    df_final.reset_index(drop=True,inplace=True)
    
    df_final.drop(columns=['ced_pro','detalle'],inplace=True)
    
    return df_final
        


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')     
chrome_options.add_argument('--disable-dev-shm-usage') 
driver = webdriver.Chrome(options=chrome_options) # REMPLAZA AQUI EL NOMBRE DE TU CHROME DRIVER
driver.get('https://procesosjudiciales.funcionjudicial.gob.ec/expel-juicios') # Voy a la pagina que requiero

## datos para testear
cedula='0200576551'        
nombre='MORA MONAR MESIAS'
test_df=get_data_scrap_esatje(cedula,nombre,driver)

## Ejecución completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
df_consol=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    nombre=documento.NOMBRE
    df_iter=get_data_scrap_esatje(cedula, nombre, driver)
    df_consol=pd.concat([df_consol,df_iter],axis=0)

df_consol.reset_index(drop=True,inplace=True)
   
df_consol.to_excel('data_judicatura.xlsx',index=False)
