import requests
import pandas as pd
from Backend_AkhtarT_Damco.Akhtar_Textiles.main import initiate_driver, login, fill_form, quit
from Backend_AkhtarT_Damco.DAMCO.dynamic2 import Automate
from Backend_AkhtarT_Damco.DAMCO.ammend import Ammend_Fields

class Damco_automation:
    try:
        ret=[]
        def gui_execute(self, file,username, password, Title, mode=""):
            error = ""
            if Title == "AT_execute":
                self.file_entry_AT = file
                self.username_AT = username
                self.password_AT = password

                error = self.execute_bot(mode)

            else:
                self.file_entry_DAMCO = file
                self.username_DAMCO = username
                self.password_DAMCO = password

                if Title == "Damco_execute":
                    error = self.execute()
                elif Title == "Damco_ammend":
                    error = self.Ammend_data()
            return error

        def execute_bot(self, mode):
            error = ""
            file = self.file_entry_AT
            email = self.username_AT
            pwd  = self.password_AT

            lgn = ""
            login_data = {
            "email" : email,
            "password" : pwd
            }
            df = pd.read_excel(file.file,dtype={'Seal Number': str})
            # df = pd.read_excel(file,dtype={'Seal Number': str})
            driver = initiate_driver("https://network.infornexus.com/")
            if driver != 'error':
                lgn = login(driver,login_data)

            if lgn == 'Login error':
                quit(driver)

            elif lgn == 'Login success':
                print(f'[INFO] Running in {mode} mode')
                error = fill_form(driver,df,mode)
            return error
        def execute(self):
            file = self.file_entry_DAMCO
            username = self.username_DAMCO
            password = self.password_DAMCO

            print("Reading From:", file)
            ret = Automate(file, username, password)
            return ret

        def Ammend_data(self):
            file = self.file_entry_DAMCO
            username = self.username_DAMCO
            password = self.password_DAMCO

            print("Reading From:", file)
            ret = Ammend_Fields(file, username, password)
            return ret

    except Exception as e:
        print(e)
        while True:
            pass

# aut= Damco_automation()
# aut.gui_execute("C:\\Users\\admin\\Downloads\\Emend Sheet2X - Copy.xlsx", "mrazaa", "atil1985", "Damco_ammend")
