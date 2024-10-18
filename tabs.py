import requests
import pandas as pd
from Backend_AkhtarT_Damco.Akhtar_Textiles.main import initiate_driver, login, fill_form, quit
from Backend_AkhtarT_Damco.DAMCO.dynamic2 import Automate
from Backend_AkhtarT_Damco.DAMCO.ammend import Ammend_Fields

class Damco_automation:
    try:
        ret=[]
        def gui_execute(self, file_path,username, password, Title):
            final_data = {}
            if Title == "AT_execute":
                self.file_entry_AT = file_path
                self.username_AT = username
                self.password_AT = password
                final_data = self.execute_bot()

            else:
                self.file_entry_DAMCO = file_path
                self.username_DAMCO = username
                self.password_DAMCO = password

                if Title == "Damco_execute":
                    final_data = self.execute()
                elif Title == "Damco_ammend":
                    final_data = self.Ammend_data()
            return final_data

        def execute_bot(self):
            file = self.file_entry_AT
            email = self.username_AT
            pwd  = self.password_AT

            login_data = {
            "email" : email,
            "password" : pwd
            }
            df = pd.read_excel(file.file,dtype={'Seal Number': str})
            driver = initiate_driver("https://network.infornexus.com/")
            if driver != 'error':
                lgn = login(driver,login_data)

            if lgn == 'Login error':
                quit(driver)

            elif lgn == 'Login success':
                print(f'[INFO] Running in {self.mode.get()} mode')
                ret = fill_form(driver,df,self.mode.get())
            return ret
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

