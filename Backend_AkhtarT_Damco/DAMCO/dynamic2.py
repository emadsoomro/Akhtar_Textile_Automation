from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.alert import Alert 
from selenium.webdriver.support.ui import Select 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException,NoSuchWindowException)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from datetime import date as dt
import pandas as pd
import time
import json 
import math as m 
from colorama import Fore, Style
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
import traceback



# service=Service(ChromeDriverManager().install())

# laod envoirement variables
load_dotenv()

database_url = os.getenv("DATABASE_URL")

db_params = {
    "dbname": "your_database_name",
    "user": "your_username",
    "password": "your_password",
    "host": "your_host",
    "port": "your_port"
}
with open(r"ports_of_discharge.json",'r') as f:
    ports = json.load(f)

with open(r"database.json",'r') as database:
    database_cred = json.load(database)

'''
Function to delete rows for given PO number
'''
def delete_row(conn,cursor,po):

    query = """
            DELETE FROM dmc_failed_records 
            WHERE PO_NUMBER = %s
                """
    cursor.execute(query,(po,))
    conn.commit()

'''
function to create table if they already does not exists
'''
def create_table(conn, cursor):
    # Creates two tables for success and failed records by iterating throught list
    for types in ['success','failed']:
        table_name = sql.Identifier('dmc_{}_records'.format(types))
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY, 
                PO_NUMBER VARCHAR,
                Plan_HOD VARCHAR,
                Country VARCHAR,
                Order_Qty VARCHAR,
                CARTON_QTY VARCHAR,
                GROSS_WEIGHT VARCHAR,
                CARTON_CBM VARCHAR,
                CTN_Type VARCHAR,
                BOOKING_ID VARCHAR,
                BOOKING_STATUS VARCHAR,
                Timestamp DATE)""").format(table_name)
        
        cursor.execute(create_table_query)
        conn.commit()

'''
Function to insert the data into success and failed tables
'''
def insert_data(conn, cursor, data,types):
    table_name = sql.Identifier('dmc_{}_records'.format(types))
    insert_query = sql.SQL("""
        INSERT INTO {} (
            PO_NUMBER,
            Plan_HOD,
            Country,
            Order_Qty,
            GROSS_WEIGHT,
            CARTON_QTY,
            CARTON_CBM,
            CTN_Type,
            BOOKING_ID,
            BOOKING_STATUS,
            timestamp
        )
        VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s,%s)
        ON CONFLICT (PO_NUMBER) DO UPDATE
        SET Plan_HOD = EXCLUDED.Plan_HOD,
            Country = EXCLUDED.Country,
            Order_Qty = EXCLUDED.Order_Qty,
            GROSS_WEIGHT = EXCLUDED.GROSS_WEIGHT,
            CARTON_QTY = EXCLUDED.CARTON_QTY,
            CARTON_CBM = EXCLUDED.CARTON_CBM,
            CTN_Type = EXCLUDED.CTN_Type,
            BOOKING_ID = EXCLUDED.BOOKING_ID,
            BOOKING_STATUS = EXCLUDED.BOOKING_STATUS,
            timestamp = EXCLUDED.timestamp                               
    """).format(table_name)
    
    # Insert data into the table
    cursor.execute(insert_query, (data))
    conn.commit()

'''
Funtion to extract PO numbers from failed records table and return is as a list
'''
def failed_po(cursor):

    cursor.execute('select PO_NUMBER from DMC_failed_records;')
    po_lst = [row[0] for row in cursor.fetchall()]
    return po_lst

def IdentifyPort(country:str):
    print(country)
    print(ports[country.upper()])
    try:
        return ports[country]
    except:
        return None
def Automate(file, username, password):
    conn = psycopg2.connect(database_cred["database_url"])
    cursor = conn.cursor()

    # Get the current date for table name
    current_date = datetime.now().strftime("%Y%m%d")
    table_name = current_date

    # Create a table based on the current date
    create_table(conn, cursor)
    fld_po_lst = failed_po(cursor)
    TIMEOUT = 30
    file = file; username= username; password = password

    print(Fore.LIGHTGREEN_EX+f"[INFO] Reading Data from {file.filename}"+Style.RESET_ALL)
    dtype_dict = {
    'numerical_column': float,
    'wildcard_column': str
    }
    CTN_TYPE = {
        "10X": "24x16x10-RS10",
        "12X": "24x16x12-RS12X",
        'EURO': "25x16x11-Euro",
        '6X': "24X16X6-RS6",
        '5X': "24x16x5-RS5X",
        '8X': "24x16x8-RS8X",
        "14X": "24X16X14-RS14X",
        'RA-12': "22x14.5x12-RA12",
        'RA-6': "22x14.5x6-RA6"
    }
    data = pd.read_excel(file.file,dtype=dtype_dict)
    # print(data.columns)

    final_df_failed = pd.DataFrame()

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (without GUI)
    chrome_options.add_argument("--no-sandbox")  # Disable the sandbox for security reasons
    chrome_options.add_argument("--disable-dev-shm-usage")  # Disable the use of /dev/shm
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--disable-software-rasterizer")  # Disable software rasterizer
    chrome_options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
    chrome_options.add_argument("--disable-setuid-sandbox")  # Disable sandboxing
    chrome_options.add_argument("--window-size=1920,1080")
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    # driver = webdriver.Chrome()

    driver.get("https://auth.damco.com/adfs/ls/?wtrealm=https%3A%2F%2Fportal.damco.com&wctx=WsFedOwinState%3DclUNwkNUP4dpiVAR1vBCtUw6PO0n1IdLnSzMvQIIahHiM5jw7bnM1i2W9bgWqEHiqJv0vURH11fUgH0T2bI4Ldn9clIwiH17_zsNz9TN0eh1xHQLEkPZ7RW9GtRMhvKeVb78R-6cSvuxKdlD7UzvO_hdhYv_dP-c15p-EL_jLfk&wa=wsignin1.0")
    time.sleep(3)

    login_username = driver.find_element(value='ctl00_ContentPlaceHolder1_UsernameTextBox')
    login_username.send_keys(username)
    login_password = driver.find_element(value='ctl00_ContentPlaceHolder1_PasswordTextBox')
    login_password.send_keys(password)
    login_enter = driver.find_element(value = 'ctl00_ContentPlaceHolder1_SubmitButton')
    login_enter.send_keys(Keys.ENTER)

    try:

        element = WebDriverWait(driver,5).until(
            EC.presence_of_element_located((By.ID,'ctl00_ContentPlaceHolder1_ErrorTextLabel')))
        if 'Authentication Failed'.lower() in element.text.lower():
            return False 
    except:
        pass
    print(Fore.GREEN+"Login SuccessFull..."+Style.RESET_ALL)
    print(data.head())
    dict_data = []
    for index,df in data.iterrows():
        if True:
            data_dict = {"PO_num": "", "Plan_HOD": "", "Country": "", "Order_Qty": "", "GROSS_WT": "", "CARTON_QTY": "",
                         "CARTON_CBM": "", "CTN_Type": "", "booking_id": "", "booking_status": ""}
            final_df = pd.DataFrame()
            try:
                df = df[['PO#','Plan-HOD','Country','CARTON QTY','Order Qty','CTN Type','CARTON CBM','GROSS WT']]
                df['PO#']=df['PO#'].split("_")[0]
                PO = df['PO#'].split("-")[0]
                L_NO = int(df['PO#'].split("-")[1])
                date = f"{df['Plan-HOD'].year}-{df['Plan-HOD'].month}-{df['Plan-HOD'].day}"
                print("[Extracted Info] \n ")
                print(f"<PO> : {PO}")
                print(f"<Line No> : {index}")
                parsed_date = datetime.strptime(date,'%Y-%m-%d')
                date = parsed_date.strftime("%Y-%m-%d")
                print(f"<date> : {date}")


                driver.get("https://booking.damco.com/ShipperPortalWeb/SearchAction.action") 

                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,'searchPO_PO_No')))

                po_number = driver.find_element(value='searchPO_PO_No')
                po_number.send_keys(PO)
                #print("got search")

                search_po_number = driver.find_element(value='searchPObtn')
                search_po_number.send_keys(Keys.ENTER)

                try:
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "selAllCkhBox")))
                    check_box = driver.find_element(By.XPATH, "//input[@id='selAllCkhBox']")
                    time.sleep(1)
                    if not check_box.is_selected():
                        check_box.click()
                except:
                    try:
                        error = driver.find_element(By.ID, "poErrorMsg")
                        error = error.text
                        print(Fore.CYAN + f"{error}" + Style.RESET_ALL)
                    except:
                        pass


                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.XPATH,"//input[@type='button' and @class='new submit poActionButton']")))

                book_button = driver.find_element(by=By.XPATH , value = "//input[@type='button' and @class='new submit poActionButton']")
                book_button.click()
                
                #print("got booking")


                #WebDriverWait(driver,3).until(EC.alert_is_present())
                time.sleep(3)
                try:
                    pop_up = Alert(driver)
                    pop_up.accept()
                    #print("got popup")
                except Exception as e:
                    print(Fore.CYAN+"Alert not found, continuing forward"+Style.RESET_ALL)
                
                
                country = df['Country']
                
                port_of_discharge = IdentifyPort(country)
                if port_of_discharge == None:
                    continue
                IDS = {
                    "estmDlvrDtId":str(date), 
                    # 'letterOfCreditId':"TEST", 
                    # 'exportLicenseId':"TEST ",
                    # "remark":"TEST TEST", 
                    # "cutOfCumm":"TEST TEST",
                    "officeGrpId":"DAMCO PAKISTAN (PVT) LTD [PKMERCANTIHQ]",
                    "portLoadGrpId":"Port Qasim [ TRM ]",
                    "portOfDischargeGrpId":str(port_of_discharge)
                    }

                #input("Enter To Enter To Continue")
                
                for key in IDS:
                    value = IDS.get(key)
                    WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,key)))
                    field = driver.find_element(value=key)
                    field.send_keys(value)
                    
                #print("got keys")
                booking = driver.find_element(by=By.ID,value="soIdId")
                booking_id = booking.get_attribute("value")
                details_button = driver.find_element(by=By.ID,value="tab_treetab3")
                details_button.click()
                #print("got details")
                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,'LineTableId')))
                #checking whether the table is available to edit or not
                table = driver.find_element(By.ID, 'LineTableId')
                rows = table.find_elements(By.TAG_NAME,'tr',)
                
                #print("="*10)
                if len(rows)>1:
                    ls = []
                    for r in rows:
                        LN_TR = r.get_attribute('id')[:5]
                        if LN_TR == 'LN_TR':
                            ls.append(r)
                    for ind, row in enumerate(ls):
                        if row.get_attribute('id') == f'LN_TR{ind}':
                            id_ = f'EditSOForm_soDto_soLineDtoList_{ind}__liRef'
                            WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,id_)))
                            element = row.find_element(By.ID,id_)
                            line_no = element.get_attribute('value')
                            #print("-->",line_no)
                            if int(line_no) != L_NO:
                                detail_box = driver.find_element(by=By.ID,value=f'EditSOForm_soDto_soLineDtoList_{ind}__selected')
                                if not detail_box.is_selected():
                                    detail_box.click()
                                    #print(f"Line No {line_no}: got selected")
                                delete_button = driver.find_element(by = By.ID,value ="deleteButtonId" )
                                delete_button.click()
                                WebDriverWait(driver,TIMEOUT).until(EC.alert_is_present())
                                Alert(driver).accept()
                                #print("got delete button")
                time.sleep(2)
                row_index = 0
                table = driver.find_element(By.ID, 'LineTableId')
                rows = table.find_elements(By.TAG_NAME,'tr',)
                for r in rows:
                    LN_TR = r.get_attribute('id')[:6]
                    if LN_TR[:5] == 'LN_TR':
                        row_index = LN_TR[-1]
                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,f'qtyUnitId{row_index}')))
                dropdown = Select(driver.find_element(by=By.ID,value=f"qtyUnitId{row_index}"))
                dropdown.select_by_visible_text("PCS")
                #print("got PCS")            
                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,f'pkgUnitId{row_index}')))
                dropdown = Select(driver.find_element(by=By.ID,value=f"pkgUnitId{row_index}"))
                dropdown.select_by_visible_text("CARTONS")
                #print("got cartons")

                field_dict = {
                    #"bookedPackagesId0":df['CARTON QTY'], 
                    # "bookedWeightId0":"0.5", #fixed
                    # "bookedMeasurementId0":df['CARTON CBM'],
                    f"lnMkNum{row_index}":"As Actual", #fixed
                    f"lnDesc{row_index}":"Ready-made garments", #fixed
                }

                bookedPackageID = driver.find_element(by=By.ID,value=f'bookedPackagesId{row_index}')
                value = bookedPackageID.text
                if  len(value) > 0:
                    for _ in len(value):
                        bookedPackageID.send_keys(Keys.BACK_SPACE)
                driver.execute_script(f"document.getElementById('bookedPackagesId{row_index}').value = {(int(df['CARTON QTY']))}")
                for key in field_dict:

                    value = field_dict.get(key)
                    WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,key)))
                    field = driver.find_element(by=By.ID,value=key)
                    field.clear()
                    for chr in value:
                        field.send_keys(chr)
                    
                #print("--"*10)
                #print(float(df['Order Qty'])*0.6)
                weight= m.ceil(float(df['Order Qty'])*0.7)
                #weight = format(weight,'.2f')
                #print(weight)
                #driver.execute__script(f"document.getElementById('bookedWeightId{row_index}').value = {weight}")
                bookedPackageID = driver.find_element(by=By.ID,value=f'bookedWeightId{row_index}')
                value = bookedPackageID.text
                if  len(value) > 0:
                    for _ in len(value):
                        bookedPackageID.send_keys(Keys.BACK_SPACE)
                driver.execute_script(f"document.getElementById('bookedWeightId{row_index}').value={weight}")
                
                #print("got keys details")
                #print(str(df["CTN Type"]))
                types = list(CTN_TYPE.keys())
                if str(df['CTN Type']) in types:
                    dropdown = driver.find_element(by=By.XPATH, value=f"(//select[contains(@id,'dynafield')])[1]")
                    # dropdown = Select(driver.find_element(by=By.ID,value=f"dynafield_0_0_refValue"))
                    dropdown = Select(dropdown)
                    dropdown.select_by_visible_text(CTN_TYPE.get(str(df['CTN Type'])))  # no column in excel
                    # print("got field1")

                    dropdown = driver.find_element(by=By.XPATH, value=f"(//select[contains(@id,'dynafield')])[2]")
                    dropdown = Select(dropdown)
                    dropdown.select_by_visible_text(CTN_TYPE.get(str(df['CTN Type'])))  # no column in excel
                    # print("got field2")
                    # print(CTN_TYPE.get(str(df['CTN Type'])))
                else:
                    raise ValueError
                    
                field = driver.find_element(by=By.NAME,value=f"soDto.soLineDtoList[{row_index}].soLineRefDtoList[4].refValue")
                field.send_keys(int(df['CARTON QTY']))
                #print("got count")

                #driver.execute__script(f"document.getElementById('bookedMeasurementId{row_index}').value = {format(float(df['CARTON CBM']),'.2f')}")
                bookedPackageID = driver.find_element(by=By.ID,value=f'bookedMeasurementId{row_index}')
                value = bookedPackageID.text
                if  len(value) > 0:
                    for _ in len(value):
                        bookedPackageID.send_keys(Keys.BACK_SPACE)
                driver.execute_script(f"document.getElementById('bookedMeasurementId{row_index}').value ={format(float(df['CARTON CBM']),'.2f')}")
                
                # WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,"MsgDivId")))
                # checker = driver.find_element(by=By.ID,value='MsgDivId')
                # print(checker.text)
                #S Number
                s1 = driver.find_element(by=By.ID,value=f'EditSOForm_soDto_soLineDtoList_{row_index}__soLineHtsDtoList_0__htsCode')
                value = s1.text
                if  len(value) == 0:
                    driver.execute_script(f"document.getElementById('EditSOForm_soDto_soLineDtoList_{row_index}__soLineHtsDtoList_0__htsCode').value = 6203.2200")
                
                
                # if False:
                #WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,"tab_treetab1")))
                #print("got headers")
                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,'SaveAsMenuBtnId')))
                save_button = driver.find_element(by=By.ID,value="SaveAsMenuBtnId")
                save_button.click()
                #print("got save button")

                WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,'SOStatusOption')))
                span_tag = driver.find_element(by=By.ID, value = 'SOStatusOption')
                draft_and_finished = span_tag.find_elements(by=By.TAG_NAME, value = 'a')
                # WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.XPATH,"//a[contains(@onclick, 'saveAsBookingOption('draft')')]")))
                # button = driver.find_element(by=By.XPATH,value="//a[contains(@onclick, 'saveAsBookingOption('draft')')]")
                
                #input("Enter to continue....!")
                draft_and_finished[1].click()
                time.sleep(2)
                try:
                    pop_up = Alert(driver)
                    pop_up.accept()
                    #print("got popup")
                except Exception as e:
                    print(Fore.CYAN+"Alert not found, continuing forward"+Style.RESET_ALL)
                WebDriverWait(driver, TIMEOUT).until(EC.invisibility_of_element_located((By.ID, 'progressStatusId')))
                WebDriverWait(driver, TIMEOUT).until(EC.invisibility_of_element_located((By.ID, 'progressStatusId')))
                WebDriverWait(driver,3).until(EC.text_to_be_present_in_element((By.ID,'MsgDivId'),f'{booking_id} saved successfully'))
                time.sleep(2)
                #
                # WebDriverWait(driver,TIMEOUT).until(EC.presence_of_element_located((By.ID,'MsgDivId')))
                
                
                print(Fore.GREEN+'Booking Fininsed....!!!'+Style.RESET_ALL)
                print("<Booking ID> : ",Fore.GREEN+booking_id,Style.RESET_ALL)
                df['booking_status'] = "success" 
                df['booking_id'] = booking_id 
                data_to_insert = (
                    str(df['PO#']),str(df['Plan-HOD']),str(df['Country']),
                    str(df['Order Qty']),str(df['GROSS WT']),str(df['CARTON QTY']),
                    str(df['CARTON CBM']),str(df['CTN Type']),df['booking_id'],df['booking_status'],dt.today()
                )
                final_df = pd.concat([final_df, df], axis=1)
                print(Fore.GREEN+"->"*3,Fore.GREEN+"Success"+Style.RESET_ALL)
                print(Fore.GREEN+"->"*3,Fore.GREEN+"Inserting in database"+Style.RESET_ALL)
                # final_df = final_df.T
                insert_data(conn, cursor, data_to_insert,'success')
                if str(df['PO#']) in fld_po_lst:
                    delete_row(conn,cursor,str(df['PO#']))
                print(Fore.GREEN+"->"*3,Fore.GREEN+"Inserted in database successfully"+Style.RESET_ALL)
                print(Fore.MAGENTA+"->"*3,Fore.MAGENTA+"-"*10,Style.RESET_ALL)
                

            except NoSuchElementException:
                traceback.print_exc()
                print(NoSuchElementException)
                print(Fore.RED+"Record not found.")
                df['booking_status'] = "failed" 
                df['booking_id'] = '-'
                print(Fore.RED+"->"*3,Fore.RED+"Failed"+Style.RESET_ALL)
                data_to_insert = (
                    str(df['PO#']),str(df['Plan-HOD']),str(df['Country']),
                    str(df['Order Qty']),str(df['GROSS WT']),str(df['CARTON QTY']),
                    str(df['CARTON CBM']),str(df['CTN Type']),df['booking_id'],df['booking_status'],dt.today()
                )
                insert_data(conn, cursor, data_to_insert,'failed')
                # final_df = final_df.T

                print(Fore.MAGENTA+"->"*3,Fore.MAGENTA+"-"*10,Style.RESET_ALL)
                continue
            except Exception as e:
                traceback.print_exc()
                print(str(e))
                df['booking_status'] = "failed" 
                df['booking_id'] = '-'
                print(Fore.RED+"->"*3,Fore.RED+"Failed"+Style.RESET_ALL)
                data_to_insert = (
                    str(df['PO#']),str(df['Plan-HOD']),str(df['Country']),
                    str(df['Order Qty']),str(df['GROSS WT']),str(df['CARTON QTY']),
                    str(df['CARTON CBM']),str(df['CTN Type']),df['booking_id'],df['booking_status'],dt.today()
                )
                print(data_to_insert)
                insert_data(conn, cursor,data_to_insert,'failed')
                print(Fore.MAGENTA+"->"*3,Fore.MAGENTA+"-"*10,Style.RESET_ALL)
                continue

            final_df = pd.concat([final_df, df], axis=1)
            final_df_transpose = final_df.T
            final_df_dict = final_df_transpose.to_dict(orient="records")[0]
            data_dict.update({"PO_num": final_df_dict['PO#'], "Plan_HOD": final_df_dict["Plan-HOD"],
                              "Country": final_df_dict["Country"], "Order_Qty": final_df_dict["Order Qty"],
                              "GROSS_WT": final_df_dict["GROSS WT"], "CARTON_QTY": final_df_dict["CARTON QTY"],
                              "CARTON_CBM": final_df_dict["CARTON CBM"], "CTN_Type": final_df_dict["CTN Type"],
                              "booking_id": final_df_dict["booking_id"],
                              "booking_status": final_df_dict["booking_status"]})
            dict_data.append(data_dict)
    driver.quit()

    return dict_data

            
        




'''

MsgDivId = ID for 43680233 saved successfully

progressStatusId is ID for draft

4100563463


2100045080
'''


# Automate(file_path=r"C:\Users\SAAD\Downloads\AUTO Data NON USA ONLY (2).xlsx", username="hamid@akhtar.com.pk", password="panhwar123")
