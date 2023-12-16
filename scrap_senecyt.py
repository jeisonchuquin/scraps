from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from time import sleep
from anticaptchaofficial.imagecaptcha import imagecaptcha
import pandas as pd
# import random
import cv2



chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')     
chrome_options.add_argument('--disable-dev-shm-usage') 
driver = webdriver.Chrome(options=chrome_options)
driver.get('https://www.senescyt.gob.ec/web/guest/consultas')
driver.set_window_size(1366, 768)


## PARA PONER BIEN NOMBRES EN TABLAS
def set_correct_names(titulos_1_:pd.DataFrame,lennames:list):   
    
    titulos_1=titulos_1_.copy()
    for i in range(titulos_1.shape[1]):
        titulos_1.iloc[:,i]=titulos_1.iloc[:,i].apply(lambda row: row[lennames[i]:])
        
    return titulos_1
    



## PARA PASAR EL CAPTCHA
def solve_captcha(driver):
    driver.execute_script("document.body.style.zoom='150%'")
    driver.save_screenshot('./captchas/captcha_senecyt.png')
    driver.execute_script("document.body.style.zoom='100%'")
    
    
    img = cv2.imread('./captchas/captcha_senecyt.png')
    #cv2.imshow("RESULT", img)
    #cv2.waitKey(0)
    
    ##### posicion de imagen captcha con zoom 150%
    y=545
    x=218
    h=45
    w=140
    img = img[y:y+h,x:x+w]
    cv2.imwrite('./captchas/captcha_senecyt.png',img)
    # cv2.imshow('Image', img)
    # cv2.destroyAllWindows()
    
    
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key("0cfd16d0d764c15019477c98c6ccba7f")
    
    captcha_text = solver.solve_and_return_solution("./captchas/captcha_senecyt.png")
    
    
    return captcha_text




## PARA OBTENER MENSAJES DE ERROR U OK
def get_message(cedula:str,driver):
    
    # sleep(random.uniform(2,3))
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH,'.//input[@id="formPrincipal:identificacion"]'))
        )
        input_id = driver.find_element(By.XPATH, './/input[@id="formPrincipal:identificacion"]')
        input_id.clear()
        input_id.send_keys(cedula)
    except:
        error_msg='Service Unavailable'
        return error_msg
    
    txt=solve_captcha(driver)
    
    # sleep(random.uniform(2,3))
    captcha_id=driver.find_element(By.XPATH,"//input[@id='formPrincipal:captchaSellerInput']")
    captcha_id.clear()
    captcha_id.send_keys(txt)
    
    
    # sleep(random.uniform(2,3))
    log_button=driver.find_element(By.XPATH,"//button[@id='formPrincipal:boton-buscar']")
    log_button.click()


    try:
        error_msg=driver.find_element(By.XPATH,"//span[@class='ui-messages-error-detail']").text 
        return error_msg ## error captcha
    except:
        # html_error=driver.page_source
        try:
            error_msg=driver.find_element(By.XPATH,"//h1").text
            return error_msg ## error proxy
        except:
            
            try:
                error_msg=driver.find_element(By.XPATH,"//div[@class='msg-rojo']").text
                return error_msg ## error no tiene titulo
            except:
                try:
                    error_msg=driver.find_element(By.XPATH,"//div[@id='main-message']//span[1]").text
                    return error_msg
                except:
                    msg=driver.find_element(By.XPATH,"//body").text
                    if len(msg)==0:
                        return 'Vacio'
                    else:
                        return 'Sin error'

    pass
    




## PARA PNER NIVELES DE TITULOS
def codec_niveles(headers:list):
    nivel=[]
    for titulo in headers:
        if 'cuarto' in titulo:
            nivel.append(4)
        elif 'tercer' in titulo:
            nivel.append(3)
        else:
            nivel.append(0)

    return nivel




## PARA OBTENER FORMATO DATAFRAME FINAL 
def get_data(pagina_full:list,headers:list,niveles_titulo:list):

    info_personal=pagina_full[2]
    info_personal.set_index(0,inplace=True)
    
    titulos=pd.DataFrame()
    pos_tables=list(range(4,4+len(headers)))
    pos_niveles=list(range(len(niveles_titulo)))
    for ntable,nnivel in zip(pos_tables,pos_niveles):
        titulos_=pagina_full[ntable]
        colnames=titulos_.columns
        lennames=[len(i) for i in colnames]
        titulos_=set_correct_names(titulos_,lennames)
        titulos_['Nivel']=niveles_titulo[nnivel]
        titulos=pd.concat([titulos,titulos_],axis=0)
        
    titulos.insert(loc=0,column='Nacionalidad',value=info_personal.loc['Nacionalidad:'].iloc[0])
    titulos.insert(loc=0,column='Genero',value=info_personal.loc['Género:'].iloc[0])
    titulos.insert(loc=0,column='Nombres',value=info_personal.loc['Nombres:'].iloc[0])
    titulos.insert(loc=0,column='cedula',value=info_personal.loc['Identificación:'].iloc[0])

    return titulos




## PARA DATAFRAME FINAL
def get_data_senecyt(cedula:str,driver):

    mensaje=get_message(cedula,driver)
    
    if 'obtuvieron' in mensaje:
        print('No tiene titulo registrado')
        data_sn={'cedula':cedula,                  
                  'Genero':'SN',
                  'Título':'ST',# ST: Sin Titulo
                  'Nacionalidad':'SN',
                  'Institución de Educación Superior':'SN',
                  'Tipo':'SN',
                  'Número de Registro':'SN',
                  'Fecha de Registro':pd.to_datetime('1900-01-01'),
                  'Área o Campo de Conocimiento':'SN',
                  'Nivel':0} 
        data_ind=pd.DataFrame(data_sn,index=[0])
        return data_ind
    else:
        for i in range(3):
            if mensaje=='Caracteres incorrectos':
                mensaje=get_message(cedula,driver)
            elif mensaje in ['Proxy Error','Service Unavailable','Vacio','No se puede acceder a este sitio']:
                driver.get('https://www.senescyt.gob.ec/web/guest/consultas')
                driver.set_window_size(1366, 768)
                mensaje=get_message(cedula,driver)
            else:
                break
        
    
    ## una vez que pasó el captcha
    
    
    if mensaje=='Sin error':        
        
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH,'//button[contains(text(),"Imprimir")]'))
            )
            
            headers=driver.find_elements(By.XPATH,".//div[@class='panel-heading']")
            headers=[i.text for i in headers][1:]
            
            
            niveles_titulo=codec_niveles(headers)
            
            
            html=driver.page_source
            pagina_full=pd.read_html(str(html))
        
        
            data_ind=get_data(pagina_full,headers,niveles_titulo)
            
            data_ind.drop(columns=['Nombres','Reconocido Por','Observación'],inplace=True)
        except:
            data_sn={'cedula':cedula,                  
                      'Genero':'SN',
                      'Título':'WP',# WP: White page, quedó muerta la pg
                      'Nacionalidad':'SN',
                      'Institución de Educación Superior':'SN',
                      'Tipo':'SN',
                      'Número de Registro':'SN',
                      'Fecha de Registro':pd.to_datetime('1900-01-01'),
                      'Área o Campo de Conocimiento':'SN',
                      'Nivel':0} 
            data_ind=pd.DataFrame(data_sn,index=[0])
            
        return data_ind
    
    elif 'obtuvieron' in mensaje:
        data_sn={'cedula':cedula,                  
                  'Genero':'SN',
                  'Título':'ST',# ST: Sin Titulo
                  'Nacionalidad':'SN',
                  'Institución de Educación Superior':'SN',
                  'Tipo':'SN',
                  'Número de Registro':'SN',
                  'Fecha de Registro':pd.to_datetime('1900-01-01'),
                  'Área o Campo de Conocimiento':'SN',
                  'Nivel':0} 
        data_ind=pd.DataFrame(data_sn,index=[0])
        
        return data_ind
    else:
        data_sn={'cedula':cedula,                  
                  'Genero':'SN',
                  'Título':'EC', # EC:Error Captcha
                  'Nacionalidad':'SN',
                  'Institución de Educación Superior':'SN',
                  'Tipo':'SN',
                  'Número de Registro':'SN',
                  'Fecha de Registro':pd.to_datetime('1900-01-01'),
                  'Área o Campo de Conocimiento':'SN',
                  'Nivel':0}  
        data_ind=pd.DataFrame(data_sn,index=[0])
        
        return data_ind
    





##
## Testeo

cedula=' 0918863218'        
cedula='1002114674'

z=get_data_senecyt(cedula, driver)


## Ejecución Completa
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
df_senecyt=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    df_iter=get_data_senecyt(cedula,driver)
    df_senecyt=pd.concat([df_senecyt,df_iter],axis=0)

df_senecyt.reset_index(drop=True,inplace=True)

df_senecyt.to_excel('data_senecyt.xlsx',index=False)




