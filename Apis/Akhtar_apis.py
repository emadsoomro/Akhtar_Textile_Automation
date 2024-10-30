import pandas as pd
from fastapi import FastAPI, Request, Form, File, UploadFile, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


@app.post("/nexus-execute")
async def nexus_execute(username: str = Header(...), password: str = Header(...), mode: str = Header(...),file: UploadFile = File(...)):
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        error =damco_automation.gui_execute(file=file, username=username, password=password, Title="AT_execute", mode=mode)
        return {"error": error}
    except Exception as e:
        return {"error": (str(e))}



@app.post("/damco-execute")
async def damco_execute(username: str = Header(...), password: str = Header(...),file: UploadFile = File(...)):
    result_data = []
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        error = damco_automation.gui_execute(file=file, username=username, password=password, Title="Damco_execute")
        # result_data = convert_timestamps(result_data)
        # return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})
        return {"error": error}
    except Exception as e:
        # return templates.TemplateResponse("damco.html", {"request": request,"data":[], "error": str(e)})
        return {"error": str(e)}



@app.post("/damco-ammend")
async def damco_ammend(username: str = Header(...), password: str = Header(...), file_damco: UploadFile = File(...)):
    result_data = []
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        error = damco_automation.gui_execute(file=file_damco, username=username, password=password,
                                     Title="Damco_ammend")

        # result_data = convert_timestamps(result_data)
        # return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})
        return {"error": error}
    except Exception as e:
        # return templates.TemplateResponse("damco.html", {"request": request, "data": [], "error": str(e)})
        return {"error": str(e)}

def convert_timestamps(data_list):
    data_list_updated = []
    for data in data_list:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, pd.Timestamp):
                    data[key] = value.isoformat()
                    data_list_updated.append(data)
    return data_list_updated

