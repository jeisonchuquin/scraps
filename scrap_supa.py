from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import random



# para iterar las demandas
def get_data_iter(iterable,driver):
    sleep(3)
    
    xpath_iter="//button[contains(@id,':"+str(iterable)+":') and contains(@alt,'Ver')]"
    
    
    login_button=driver.find_element(By.XPATH,xpath_iter)
    login_button.click() # Le doy click
    
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH,"//span[contains(text(),'Fecha')]"))
    )

    sleep(3)   
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    
    ## informacion general
    div=soup.find('div',class_='ui-dialog-content ui-widget-content')
    info_general=pd.read_html(str(div))[3]
    
    proceso_judicial=info_general.loc[info_general[0].str.contains('judicial'),1].iloc[0]
    tipo_pension=info_general.loc[info_general[0].str.contains('Tipo'),1].iloc[0]
    pension_actual=info_general.loc[info_general[0].str.contains('actual'),1].iloc[0]
    pension_actual=pension_actual.replace('$','')
    pension_actual=pension_actual.replace(',','')
    
    ## intervinientes
    # div=soup.find('div',id='form:j_idt95_content')
    personas=pd.read_html(str(div))[4].dropna()
    
    r_legal=personas.loc[personas[0].str.contains('Legal'),1].iloc[0]
    o_principal=personas.loc[personas[0].str.contains('principal'),1].iloc[0]
    
    
    
    ## Movimientos
    # div=soup.find('div',id='form:j_idt110')
    tabla_mov=pd.read_html(str(div))[5]
    
    fecha_inicio=tabla_mov['Fecha deuda'].min()
    try:
        fecha_inicio=pd.to_datetime(fecha_inicio,format='%d/%m/%Y')
    except:
        fecha_inicio=pd.to_datetime('01/01/1990',format='%d/%m/%Y')
        
    
    ultima_fecha=tabla_mov['Fecha deuda'].max()
    try:
        ultima_fecha=pd.to_datetime(ultima_fecha,format='%d/%m/%Y')
    except:
        ultima_fecha=pd.to_datetime('01/01/1990',format='%d/%m/%Y')
    
    estado=tabla_mov['Estado'].iloc[0]
    
    ## 
    login_button=driver.find_element(By.XPATH,"//button[@id='form:ta_co_movimientosPendientes']")
    login_button.click() # Le doy click
    
    sleep(2)
    
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    
    div=soup.find('div',id='form:d_pendientes')
    pendientes=pd.read_html(str(div))[1]
    
    total_pendiente=pendientes.loc[pendientes[0].str.contains('TOTAL'),1].iloc[0]
    total_pendiente=total_pendiente.replace('$','')
    total_pendiente=total_pendiente.replace(',','')
    
    num_pensiones=pendientes.loc[pendientes[0].str.contains('pendientes'),1].iloc[0]
    
    ## volvemos al inicio
    login_button=driver.find_element(By.XPATH,"//button[@id='form:ta_co_cerrarPendientes']")
    login_button.click() # Le doy click

    login_button=driver.find_element(By.XPATH,"//button[contains(@id,'form:j_idt') and contains(@onclick,'dDetalle.hide()')]")
    login_button.click() # Le doy click
    
    
    ## creamos dataframe final
    
    data={'TOTAL_PENDIENTE':total_pendiente,
          'PENSIONES_PENDIENTES':num_pensiones,
          'PROCESO_JUDICIAL':proceso_judicial,
          'TIPO_PENSION':tipo_pension,
          'PENSION_ACTUAL':pension_actual,
          'REPRESENTANTE_LEGAR':r_legal,
          'OBLIGADO_PRINCIPAL':o_principal,
          'FECHA_INICIO':fecha_inicio,
          'ULTIMA_FECHA_RPT':ultima_fecha,
          'ESTADO_DEUDA':estado}
    
    data=pd.DataFrame(data,index=[0])

    return data    


def get_supa_data(cedula,driver):

    driver.refresh()
    input_id = driver.find_element(By.XPATH, './/input[@id="form:t_texto_cedula"]')
    input_id.clear()
    input_id.send_keys(cedula)
    
    login_button = driver.find_element(By.XPATH, './/button[@id="form:b_buscar_cedula"]')
    login_button.click()
    sleep(random.uniform(2, 3))
    
    
    # numero de demandas
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    div=soup.find('div',class_='ui-datatable-tablewrapper')
    
    detalle_ver=pd.read_html(str(div))[0].dropna()
    detalle_ver=detalle_ver[detalle_ver.Detalle=='Ver']
    ndemandas=len(detalle_ver)
        
    if not detalle_ver.empty:
        df_demandas=pd.DataFrame()
        for ndemand in range(ndemandas):
            df_demandas_=get_data_iter(ndemand,driver)
            df_demandas=pd.concat([df_demandas,df_demandas_],axis=0)
    
        df_demandas.insert(loc=0,column='CEDULA',value=cedula)
    else:
        df_demandas=[{'CEDULA':cedula,
                      'TOTAL_PENDIENTE':0.0,
                      'PENSIONES_PENDIENTES':0.0,
                      'PROCESO_JUDICIAL':'000-000-000',
                      'TIPO_PENSION':'SN',                      
                      'PENSION_ACTUAL':0.0,
                      'REPRESENTANTE_LEGAR':'SN',
                      'OBLIGADO_PRINCIPAL':'SN',
                      'FECHA_INICIO':pd.to_datetime('1900-01-01'),
                      'ULTIMA_FECHA_RPT':pd.to_datetime('1900-01-01'),
                      'ESTADO_DEUDA':'SN'}]
        df_demandas=pd.DataFrame(df_demandas)
    
    return df_demandas
    

## SCRAPP PG-IESS
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')     
chrome_options.add_argument('--disable-dev-shm-usage') 
driver = webdriver.Chrome(options=chrome_options)
driver.get('https://supa.funcionjudicial.gob.ec/pensiones/publico/consulta.jsf')

## Para testear
cedula='1308076908'        
demanda_ci=get_supa_data(cedula,driver)

## EJECUCION COMPLETA
input_file = pd.read_excel('ids1.xlsx', dtype={'CI': str})    
data_supa=pd.DataFrame()
for index, documento in input_file.iterrows():
    cedula=documento.CI
    df_iter=get_supa_data(cedula, driver)
    data_supa=pd.concat([data_supa,df_iter],axis=0)

data_supa.reset_index(drop=True,inplace=True)

data_supa.to_excel('data_supa.xlsx',index=False)

