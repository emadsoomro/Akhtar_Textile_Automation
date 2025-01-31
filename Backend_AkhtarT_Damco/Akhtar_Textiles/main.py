import pandas as pd 
import time
from pathlib import Path
import json
import traceback
from datetime import datetime
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import NoAlertPresentException,NoSuchWindowException
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore
import psycopg2
from psycopg2 import sql
from selenium.webdriver.chrome.service import Service
import os
from dotenv import load_dotenv
import sys

database_path = os.getcwd()+"\database.json"

with open(fr"{database_path}",'r') as database:
    database_cred = json.load(database)

def failed_po(cursor):

    cursor.execute('select PO_NUMBER from NXS_failed_records;')
    po_lst = [row[0] for row in cursor.fetchall()]
    return po_lst

def delete_row(conn,cursor,po):

    query = """
            DELETE FROM NXS_failed_records  
            WHERE PO_number = %s
                """
    cursor.execute(query,(po,))
    conn.commit()

def create_table(conn, cursor):
    for types in ['success','failed']:
        table_name = sql.Identifier('nxs_{}_records'.format(types))
        create_table_query = sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {} 
                    (id SERIAL PRIMARY KEY, 
                    PO_number BIGINT UNIQUE, 
                    Assign_Equipment_ID VARCHAR(50), 
                    Booking_Number VARCHAR(50), 
                    Shipment_load_type VARCHAR(200), 
                    Invoice_Number VARCHAR, 
                    Bill_Waybill VARCHAR(50), 
                    Carrier VARCHAR(50), 
                    Updated_Transload_location_US_only VARCHAR(50), 
                    Estimated_Departure_Date DATE, 
                    Equipment_number_type VARCHAR(50), 
                    Seal_number INTEGER, 
                    CTN_QTY INTEGER, 
                    Units INTEGER,
                    Route_Number BIGINT,
                    STATUS VARCHAR,
                    Timestamp TIMESTAMP)""").format(table_name)
        
        cursor.execute(create_table_query)
        conn.commit()

def insert_data(conn, cursor, data,types):
    table_name = sql.Identifier('nxs_{}_records'.format(types))
    insert_query = sql.SQL(""" INSERT INTO {} (
                    PO_number, 
                    Assign_Equipment_ID, 
                    Booking_Number, 
                    Shipment_load_type, 
                    Invoice_Number, 
                    Bill_Waybill, 
                    Carrier, 
                    Updated_Transload_location_US_only, 
                    Estimated_Departure_Date, 
                    Equipment_number_type, 
                    Seal_number, 
                    CTN_QTY, 
                    Units,
                    Route_Number,
                    STATUS,
                    timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (PO_number) DO UPDATE
                    SET Assign_Equipment_ID = EXCLUDED.Assign_Equipment_ID,
                    Booking_Number = EXCLUDED.Booking_Number,
                    Shipment_load_type = EXCLUDED.Shipment_load_type,
                    Invoice_Number = EXCLUDED.Invoice_Number,
                    Bill_Waybill = EXCLUDED.Bill_Waybill,
                    Carrier = EXCLUDED.Carrier,
                    Updated_Transload_location_US_only = EXCLUDED.Updated_Transload_location_US_only,
                    Estimated_Departure_Date = EXCLUDED.Estimated_Departure_Date,
                    Equipment_number_type = EXCLUDED.Equipment_number_type,
                    Seal_number = EXCLUDED.Seal_number,
                    CTN_QTY = EXCLUDED.CTN_QTY,
                    Units = EXCLUDED.Units,
                    Route_Number = EXCLUDED.Route_Number,
                    STATUS = EXCLUDED.STATUS,
                    timestamp = EXCLUDED.timestamp""").format(table_name)
    
    # Insert data into the table
    cursor.executemany(insert_query, (data))
    conn.commit()

def create_directory(relative_path):
    absolute_path = Path.cwd() / Path(relative_path)
    
    if not absolute_path.exists():
        absolute_path.mkdir(parents=True)
        return 0
    else:
        return 1

def db_lst_append(lst,row,route_number=0):
    try:
        db_data = (
            
            row['PO Numbers:'],
            row['Assign Equipment ID'],
            row['Booking Number'],
            row['Shipment Load Type'],
            row['Invoice Number'],
            row['BL / Waybill #'],
            row['Select Carrier'],
            row['Updated Transload Location (US Only)'],
            row['Estimated Departure Date'],
            row['Equipment # Type'],
            row['Seal Number'],
            row['CTN QTY'],
            row['UNITS'],
            route_number,
            row['Status'],
            datetime.now().isoformat())
        lst.append(db_data)
    except KeyError:
        db_data = (
            
            row['PO Numbers:'],
            row['Assign Equipment ID'],
            row['Booking Number'],
            row['Shipment Load Type'],
            row['Invoice Number'],
            '',
            row['Select Carrier'],
            '',
            row['Estimated Departure Date'],
            row['Equipment # Type'],
            row['Seal Number'],
            row['CTN QTY'],
            row['UNITS'],
            route_number,
            row['Status'],
            datetime.now().isoformat()
        )
        lst.append(db_data)

def append_data(lst,row,route_number=None):
    try:
        lst.append({
                            'Assign Equipment ID': row['Assign Equipment ID'],
                            'PO Numbers:':row['PO Numbers:'],
                            'Booking Number':row['Booking Number'],
                            'Shipment Load Type':row['Shipment Load Type'],
                            'Invoice Number':row['Invoice Number'],
                            "BL / Waybill #" : row['BL / Waybill #'],
                            'Select Carrier':row['Select Carrier'],
                            'Updated Transload Location (US Only)':row['Updated Transload Location (US Only)'],
                            'Estimated Departure Date':row['Estimated Departure Date'],
                            'Equipment # Type':row['Equipment # Type'],
                            'Seal Number':row['Seal Number'],
                            'CTN QTY':row['CTN QTY'],
                            'UNITS':row['UNITS'],
                            "Root number": route_number,
                            "Status": row["Status"]
                        })
    except KeyError:
        lst.append({
                            'Assign Equipment ID': row['Assign Equipment ID'],
                            'PO Numbers:':row['PO Numbers:'],
                            'Booking Number':row['Booking Number'],
                            'Shipment Load Type':row['Shipment Load Type'],
                            'Invoice Number':row['Invoice Number'],
                            'Estimated Departure Date':row['Estimated Departure Date'],
                            'Equipment # Type':row['Equipment # Type'],
                            'Seal Number':row['Seal Number'],
                            'CTN QTY':row['CTN QTY'],
                            'UNITS':row['UNITS'],
                            "Root number": route_number,
                            "Status": row["Status"]
                        })

def wait_for_element_to_load(driver,by,selector,t=7):
    try:
        elem = WebDriverWait(driver,t).until(
            EC.presence_of_element_located((by,selector))
        )
        return elem
    except Exception as e:
        print(f'Timeout error {e}')
        return None

def is_element_clickibale(driver,by,selector,t=25):
    try:
        elem = WebDriverWait(driver,t).until(
            EC.element_to_be_clickable((by,selector))
        )
        return elem
    except Exception as e:
        print(f'Timeout error {e}')
        return None

def wait_for_elements_to_load(driver,by,selector,t=25):
    try:
        elem = WebDriverWait(driver,t).until(
            EC.presence_of_all_elements_located((by,selector))
        )
        return elem
    except Exception as e:
        print(f'Timeout error {e}')
        return None
    
def convert_date_to_numeric(date_string):
    # Parse the date string to a datetime object
    date_object = datetime.strptime(date_string, '%B %d, %Y')
    return date_object



def initiate_driver(URL):
    try:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Run in headless mode (without GUI)
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--no-sandbox")  # Disable the sandbox for security reasons
        chrome_options.add_argument("--disable-dev-shm-usage")  # Disable the use of /dev/shm
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument("--disable-software-rasterizer")  # Disable software rasterizer
        chrome_options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
        chrome_options.add_argument("--disable-setuid-sandbox")  # Disable sandboxing
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(URL)
        print(Fore.GREEN + f"[Info] driver initiated successfully")
        print(Fore.RESET)
        return driver
    except Exception as e:
       
        print(Fore.RED + f"[INFO] Error initiating driver: {e}")
        print(Fore.RESET)
        traceback.print_exc()  # Print the full traceback
        return None

def login(driver,data):
    try:
        wait_for_element_to_load(driver,By.ID,'login').send_keys(data["email"])
        wait_for_element_to_load(driver,By.ID,'password').send_keys(data["password"])
        wait_for_element_to_load(driver,By.ID,'loginButton').click()
        error = wait_for_element_to_load(driver,By.ID,'alertboxmessage',5)
        if error is not None:

            return 'Login error'
        else:
            return 'Login success'
    except:
        return 'error' 

def form_submit(driver,row,data,db_data_lst_fld,db_data_lst_scs,df,mode):
    wait_for_element_to_load(driver,By.XPATH,"//input[contains(@name,'BookingNumber')]").send_keys(row['Booking Number'])
    time.sleep(1)
    wait_for_element_to_load(driver,By.XPATH,"//select[contains(@name,'LoadType')]").send_keys(row['Shipment Load Type'])
    time.sleep(1)
    wait_for_element_to_load(driver,By.XPATH,"//input[contains(@name,'invoiceNumber')]").send_keys(row['Invoice Number'])
    time.sleep(1)
    if 'BL / Waybill #' in df.columns.tolist():
        try:
            wait_for_element_to_load(driver,By.XPATH,"//input[contains(@name,'houseBillOfLadingNumber')]").send_keys(row['BL / Waybill #'])
            bl=True
        except KeyError:
            wait_for_element_to_load(driver,By.XPATH,"//input[contains(@name,'houseBillOfLadingNumber')]").send_keys(row['BL / Waybill #'])
            bl=False                
    time.sleep(1)
    if 'Select Carrier' in df.columns.tolist():
        wait_for_element_to_load(driver,By.XPATH,"(//select[contains(@name,'propertyValue')])[1]").send_keys(row['Select Carrier'])
    if 'Updated Transload Location (US Only)' in df.columns.tolist():
        time.sleep(1)
        wait_for_element_to_load(driver,By.XPATH,"(//select[contains(@name,'propertyValue')])[2]").send_keys(row['Updated Transload Location (US Only)'])
    date = row['Estimated Departure Date']
    month = str(date.strftime("%b"))
    day = str(date.strftime("%d"))
    year = str(date.strftime("%Y"))

    today_date = datetime.today().date()
    # Get the day of the month
    day_of_month = str(today_date.day)

    wait_for_element_to_load(driver,By.XPATH,"//select[contains(@name,'1_eventDateTimeInTZ_month')]").send_keys(month)
    time.sleep(1)
    day_drp = wait_for_element_to_load(driver,By.XPATH,"//select[contains(@name,'1_eventDateTimeInTZ_day')]")
    if day_of_month == day:
        js_code = """
        const dropdown = arguments[0];
        const valueToSelect = arguments[1];
        dropdown.value = valueToSelect;
            """
        driver.execute_script(js_code, day_drp, day)
    else:
        day_drp.send_keys(day)
    
    time.sleep(1)
    wait_for_element_to_load(driver,By.XPATH,"//select[contains(@name,'1_eventDateTimeInTZ_year')]").send_keys(year)
    time.sleep(1)
    wait_for_element_to_load(driver,By.XPATH,"//select[contains(@name,'EditType')]").send_keys(row['Equipment # Type'])
    time.sleep(1)
    wait_for_element_to_load(driver,By.XPATH,"//input[contains(@name,'EditSeal')]").send_keys(row['Seal Number'])
    
    item_quantity = wait_for_element_to_load(driver,By.XPATH,"(//td[@class='datafieldlabelsmall'])[2]").text
    item_quantity = item_quantity.strip()
    item_quantity = item_quantity.split(".")[0]
    print(item_quantity)
    pkg_count = wait_for_element_to_load(driver,By.XPATH,"(//td[@class='datafieldlabelsmall'])[3]").text
    pkg_count = pkg_count.strip()
    pkg_count = pkg_count.split(".")[0]
    print(pkg_count)
    root_number = 0
    if int(item_quantity.replace(',','')) == row['UNITS'] and int(pkg_count.replace(',','')) == row['CTN QTY']:

        print('appending')
        time.sleep(3)
        
        try:
            wait_for_element_to_load(driver,By.XPATH,"//input[@value='Preview']").click()
        except:
            validate = driver.find_element(By.XPATH,"//input[@value='Preview']")
            driver.execute_script("arguments[0].scrollIntoView(true);", validate)
            driver.execute_script("arguments[0].click();", validate)
        time.sleep(3)
        root_number = wait_for_element_to_load(driver,By.XPATH,
        "//td[contains(text(),'Ref Number')]//following-sibling::td[1]").text
        print(f'[INFO] Route number:{root_number}')
        if mode == 'Approve':
            try:
                wait_for_element_to_load(driver,By.XPATH,"(//input[@value='Approve'])[1]").click()
            except:
                approve = driver.find_element(By.XPATH,"(//input[@value='Approve'])[1]")
                driver.execute_script("arguments[0].scrollIntoView(true);", approve)
                driver.execute_script("arguments[0].click();", approve)
            
            wait_for_element_to_load(driver,By.XPATH,"(//input[@value='OK'])[1]").click()
        else:
            pass
        row["Status"]= "success"
        db_lst_append(db_data_lst_scs,row,root_number)
        append_data(data,row,root_number)
        fld_po_lst = failed_po(cursor)
        if row['PO Numbers:'] in fld_po_lst:
            delete_row(conn,cursor,row['PO Numbers:'])
        print(Fore.GREEN + '[INFO] form filled successfully')
    else:
        row["Status"]= "failed"
        print(Fore.RED + '[INFO] Quantity and units not matched')
        db_lst_append(db_data_lst_fld,row,root_number)
        append_data(data,row)



def fill_form(driver,df,mode):
    global conn
    global cursor
    try:
        conn = psycopg2.connect(database_cred["database_url"])
        cursor = conn.cursor()
        print(Fore.GREEN + '[INFO] Database connection formed')
    except Exception as e:
        conn = None
        cursor = None
        print(Fore.RED + '[INFO] Error connecting to database',e)
    
    create_table(conn,cursor)
    create_directory('result_sheets')

    try:
        error = ""
        nexus_col_list = ["PO Numbers:","Assign Equipment ID","Booking Number","Shipment Load Type","Invoice Number","BL / Waybill #","Select Carrier","Updated Transload Location (US Only)","Estimated Departure Date","Equipment # Type","Seal Number","CTN QTY","UNITS","Status"]
        df["Status"] = "-"
        df.columns = df.columns.str.strip()  # Remove leading/trailing white spaces
        df.columns = df.columns.str.replace(' ', ' ', regex=True).str.replace('\n', '', regex=True)
        df = df.fillna('')
        data = []
        db_data_lst_scs = []
        db_data_lst_fld = []
        if set(df.columns) == set(nexus_col_list):
            for index,row in df.iterrows():

                try:
                    print(Fore.RESET + f"row {index} started with PO number: {row['PO Numbers:']}")
                    url = "https://network.infornexus.com//en/trade/PackByScan"
                    driver.get(url)

                    shipment_scan_href = wait_for_element_to_load(driver,By.XPATH,'//a[contains(.,"Shipment Scan")]')
                    try:
                        shipment_scan_href.click()
                    except:
                        driver.execute_script("arguments[0].scrollIntoView(true);", shipment_scan_href)
                        driver.execute_script("arguments[0].click();", shipment_scan_href)


                    assign_eqp_id_chkbx = wait_for_element_to_load(
                        driver,By.XPATH,'//label[contains(.,"Assign Equipment ID")]//preceding-sibling::input')
                    try:
                        assign_eqp_id_chkbx.click()
                    except:
                        driver.execute_script("arguments[0].scrollIntoView(true);", assign_eqp_id_chkbx)
                        driver.execute_script("arguments[0].click();", assign_eqp_id_chkbx)

                    driver.find_element(By.NAME,"poNum").send_keys(row['PO Numbers:'])
                    wait_for_element_to_load(driver,By.XPATH,"//button[contains(.,'OK')]").click()

                    clickable = is_element_clickibale(driver,By.XPATH,"//button[contains(@class,'page-next')]",3)

                    wait_for_element_to_load(driver,By.XPATH,"(//div[contains(@class,'hd-checker')])[1]").click()

                    results_selected = wait_for_element_to_load(driver,By.XPATH,"(//td[contains(.,'Packages Selected')]//following-sibling::td)[1]//span").text
                    print(results_selected)
                    if results_selected == '0':
                        try:
                            wait_for_element_to_load(driver,By.XPATH,"//a[contains(.,'Select All')]").click()
                        except:
                            print("Select all Anchor not found")

                    results_selected = wait_for_element_to_load(driver,By.XPATH,"(//td[contains(.,'Packages Selected')]//following-sibling::td)[1]//span").text
                    result_found = wait_for_element_to_load(driver, By.XPATH, f'//div[contains(@id,"{row["PO Numbers:"]}")]', 5)

                    if result_found is None:
                        print(Fore.RED + f'[INFO] Results not for PO number:{row["PO Numbers:"]}')
                        print(Fore.RESET)
                        print(Fore.GREEN + f'[INFO] Searching if PO number:{row["PO Numbers:"]} already assigned')
                        print(Fore.RESET)
                        home = driver.find_element(By.XPATH,"(//a[@id='navmenu__home'])[1]").get_attribute('href')
                        driver.get(home)

                        url = "https://network.infornexus.com//en/trade/PackByScan"
                        driver.get(url)

                        create_shipment_href = wait_for_element_to_load(
                        driver,By.XPATH,'//a[contains(.,"Create Shipment")]').click()
                        time.sleep(3)
                        wait_for_element_to_load(driver,By.XPATH,"//input[@name='poNum']").send_keys(row['PO Numbers:'])
                        days = driver.find_element(By.XPATH,"//input[@name='executionDateDays']")
                        print(days)
                        days.clear()
                        time.sleep(2)
                        wait_for_element_to_load(driver,By.XPATH,"//button[contains(.,'OK')]").click()
                        wait_for_element_to_load(driver,By.XPATH,"(//div[contains(@class,'hd-checker')])[1]").click()
                        wait_for_element_to_load(driver,By.XPATH,"(//button[contains(.,'Create Shipment')])[1]").click()
                        print(Fore.GREEN + f'[INFO] Moving to Next PO')
                        print(Fore.RESET)
                        continue


                    if (str(results_selected) == str(row['CTN QTY'])):
                        if result_found is not None:
                            time.sleep(2)
                            wait_for_element_to_load(driver,By.XPATH,"(//button[contains(.,'Assign Equipment ID')])[1]").click()
                            wait_for_element_to_load(driver,By.XPATH,"//form[contains(.,'Container/Equipment #:')]//input").send_keys(row['Assign Equipment ID'])
                            wait_for_element_to_load(driver,By.XPATH,"//button[contains(.,'Apply')]").click()

                            try:
                                wait_for_element_to_load(driver,By.XPATH,'(//button[contains(.,"OK")])[2]',2).click()

                            except :
                                pass

                            time.sleep(2)
                            home = driver.find_element(By.XPATH,"(//a[@id='navmenu__home'])[1]").get_attribute('href')
                            driver.get(home)
                            time.sleep(1)
                            url = "https://network.infornexus.com//en/trade/PackByScan"
                            driver.get(url)

                            create_shipment_href = wait_for_element_to_load(
                            driver,By.XPATH,'//a[contains(.,"Create Shipment")]').click()
                            time.sleep(3)
                            wait_for_element_to_load(driver,By.XPATH,"//input[@name='poNum']").send_keys(row['PO Numbers:'])
                            days = driver.find_element(By.XPATH,"//input[@name='executionDateDays']")
                            print(days)
                            days.clear()
                            time.sleep(2)
                            wait_for_element_to_load(driver,By.XPATH,"//button[contains(.,'OK')]").click()
                            wait_for_element_to_load(driver,By.XPATH,"(//div[contains(@class,'hd-checker')])[1]").click()
                            wait_for_element_to_load(driver,By.XPATH,"(//button[contains(.,'Create Shipment')])[1]").click()
                            print(Fore.GREEN + f'[INFO] Filling form')
                            print(Fore.RESET)
                            form_submit(driver,row,data,db_data_lst_fld,db_data_lst_scs,df,mode)
                            continue
                        else:
                            keep_open(driver)
                            print(Fore.RED + f'[INFO] Results didnt matched for PO number:{row["PO Numbers:"]}')
                            print(Fore.RESET)

                except Exception as e:
                    print(Fore.RED + f'[INFO] error filling the form',e)
                    append_data(data,row)
                    row["Status"] = "failed"
                    db_lst_append(db_data_lst_fld, row)
                    print(traceback.format_exc())
                    print(Fore.RESET)

        else:
            print(Fore.RED + f'Invalid file format: Headers do not match')
            print(Fore.RESET)
            error = "Invalid file format: Headers do not match"

        try:
            insert_data(conn,cursor,db_data_lst_scs,'success')
            insert_data(conn,cursor,db_data_lst_fld,'failed')

        except PermissionError:
            print(Fore.RED + '[INFO] Error inserting data into database')
            print(Fore.RESET)
    except NoSuchWindowException:
        print(Fore.RED + f'[INFO] browser window closed')
        print(Fore.RESET)
        error = "browser window closed"
    return error
def keep_open(driver):
    while True:
        pass

def quit(driver):
    driver.quit()

