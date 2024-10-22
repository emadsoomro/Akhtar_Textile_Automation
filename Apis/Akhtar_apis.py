import pandas as pd
from fastapi import FastAPI, Request, Form, File, UploadFile
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


@app.get("/", response_class=HTMLResponse)
def root_login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Akhtar Textiles Automation"})

@app.post("/AT-execute")
async def AT_execute(username_AT: str = Form(...),password_AT: str = Form(...),file_AT: UploadFile = File(...)):
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file_path=file_AT, username=username_AT, password=password_AT, Title="AT_execute")
    except Exception as e:
        return {"error": (str(e))}

    return {"result_data" : result_data}


@app.post("/damco-execute", response_class=HTMLResponse)
async def damco_execute(request: Request, username_damco: str = Form(...),password_damco: str = Form(...),file_damco: UploadFile = File(...)):
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file_path=file_damco, username=username_damco, password=password_damco, Title="Damco_execute")
        result_data = convert_timestamps(result_data)
        return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})
    except Exception as e:
        return templates.TemplateResponse("damco.html", {"request": request,"data":[], "error": str(e)})




@app.post("/damco-ammend", response_class=HTMLResponse)
async def damco_ammend(request: Request ,username_damco: str = Form(...),password_damco: str = Form(...),file_damco: UploadFile = File(...)):
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file_path=file_damco, username=username_damco, password=password_damco,
                                     Title="Damco_ammend")

        result_data = convert_timestamps(result_data)
        return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})

    except Exception as e:
        return templates.TemplateResponse("damco.html", {"request": request, "data": [], "error": str(e)})

def convert_timestamps(data_list):
    data_list_updated = []
    for data in data_list:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, pd.Timestamp):
                    data[key] = value.isoformat()
                    data_list_updated.append(data)
    return data_list_updated

