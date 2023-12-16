from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd
import random
import re
import PyPDF2
import os



## Borramos todos los archivos que pueden existir en la carpeta
ruta=os.getcwd()+"\iess_docs\\"
try:
    for file_name in os.listdir(ruta):
        file = ruta + file_name
        if os.path.isfile(file):
            print('Archivo eliminado:', file)
            os.remove(file)
except:
    pass

## CONFIGURACION DE RUTA DE DESCARGAS

chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory" : ruta,"directory upgrade":True}
chromeOptions.add_experimental_option("prefs",prefs)
chromeOptions.add_argument('--no-sandbox')     
chromeOptions.add_argument('--disable-dev-shm-usage') 



##
driver = webdriver.Chrome(options=chromeOptions)
driver.get('https://www.iess.gob.ec/empleador-web/pages/morapatronal/certificadoCumplimientoPublico.jsf') # Voy a la pagina que requiero


def get_values(reader,tipo:str='RUC'):
    text_pg1=reader.pages[0].extract_text().replace('\n', '')
    if text_pg1!='':
        if 'USD' in text_pg1:
            # valor=re.findall(r'\d+(?:[,.]\d+)*', text_pg1)
            valor1=re.findall(r'USD \d+(?:[,.]\d+)*', text_pg1)
            valor2=re.findall(r'USD\d+(?:[,.]\d+)*', text_pg1)
            valor3=re.findall(r'\$\d+(?:[,.]\d+)*', text_pg1)
            valor=valor1+valor2+valor3
            if len(valor)>0:
                # valor=valor[-4] #tomamos esa pos, por la fecha queda en lista [2023,04,30]                  
                valor=[value.replace(',','') for value in valor]
                valor=[value.replace('USD','') for value in valor]
                valor=[value.replace('$','') for value in valor]
                valor=sum([float(value) for value in valor])
            else:
                valor=0
        else:
            valor=0
    else:
        valor=0
    if tipo=='CED':
        os.remove('./iess_docs/certificado_voluntario_ced.pdf')
    else:
        os.remove('./iess_docs/certificado_empresa_ruc.pdf')
    
    return valor




def get_info(cedula:str,driver,tipo:str='CED'):
    driver.refresh()
    input_id = driver.find_element(By.XPATH, './/input[@name="frmCertificadoCumplimiento:j_id9"]')
    input_id.clear()
    input_id.send_keys(cedula)
    
    sleep(random.uniform(1, 2))

    login_button = driver.find_element(By.XPATH, './/input[@name="frmCertificadoCumplimiento:j_id11"]')
    login_button.click()
    
    sleep(3)
    
    if tipo=='CED':
        try:
            reader_ced=PyPDF2.PdfReader("./iess_docs/certificado_voluntario_ced.pdf")    
            valor=get_values(reader_ced,'CED')
        except:
            valor = 0.0
    else:
        try:
            reader_ruc=PyPDF2.PdfReader("./iess_docs/certificado_empresa_ruc.pdf")
            valor=get_values(reader_ruc,'RUC')
        except:
            valor = 0.0
        # if len(valor)==0 or valor==0:
        #     valor=0
        # else:
        #     valor=valor[0]
        
    
    data={'cedula':cedula,'valor':valor}
    data=pd.DataFrame(data,index=[0])
    
    return data




def get_info_iess(cedula:str,driver):
    if len(cedula)==10:
        ruc=cedula+'001'
    else:
        ruc=cedula
    
    if len(cedula)==13:
        try:
            df_ruc=get_info(ruc,driver,'RUC')
            return df_ruc
        except:
            pass
    else:
        df_ced=get_info(cedula,driver,'CED')
        sleep(random.uniform(2, 3))
        try:
            df_ruc=get_info(ruc,driver,'RUC')
            df_ruc.cedula=cedula           
        except:
            df_ruc=pd.DataFrame()
            
        df_consol=pd.concat([df_ced,df_ruc],axis=0)
        
        df_consol.valor=df_consol.valor.astype('float')        
        df_consol=df_consol.groupby('cedula')['valor'].sum()
        df_consol=df_consol.reset_index()
        
        return df_consol



## test individual
cedula='1792049989001'        
get_info_iess(cedula,driver)



## Ejecución Completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
df_iess=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    df_iter=get_info_iess(cedula,driver)
    df_iess=pd.concat([df_iess,df_iter],axis=0)

df_iess.reset_index(drop=True,inplace=True)

df_iess.to_excel('data_iess.xlsx',index=False)



##
