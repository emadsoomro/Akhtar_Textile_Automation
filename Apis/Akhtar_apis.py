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


@app.get("/", response_class=HTMLResponse)
def root_login(request: Request):
    return templates.TemplateResponse("index_1.html", {"request": request, "title": "Akhtar Textiles Automation"})

@app.get("/AT-execute")
async def AT_execute(username: str = Header(...), password: str = Header(...),file_AT: UploadFile = File(...)):
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file=file_AT, username=username, password=password, Title="AT_execute")
    except Exception as e:
        return {"error": (str(e))}

    return {"result_data" : result_data}


@app.get("/damco-execute")
async def damco_execute(username: str = Header(...), password: str = Header(...),file_damco: UploadFile = File(...)):
    result_data = []
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file=file_damco, username=username, password=password, Title="Damco_execute")
        result_data = convert_timestamps(result_data)
        # return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})
        return {"data": result_data}
    except Exception as e:
        # return templates.TemplateResponse("damco.html", {"request": request,"data":[], "error": str(e)})
        return {"data": result_data}



@app.get("/damco-ammend")
async def damco_ammend(username: str = Header(...), password: str = Header(...), file_damco: UploadFile = File(...)):
    result_data = []
    try:
        import tabs
        damco_automation = tabs.Damco_automation()
        result_data = damco_automation.gui_execute(file=file_damco, username=username, password=password,
                                     Title="Damco_ammend")

        result_data = convert_timestamps(result_data)
        # return templates.TemplateResponse("damco.html", {"request": request, "data": result_data, "error": ""})
        return {"data": result_data}
    except Exception as e:
        # return templates.TemplateResponse("damco.html", {"request": request, "data": [], "error": str(e)})
        return {"data": result_data}

def convert_timestamps(data_list):
    data_list_updated = []
    for data in data_list:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, pd.Timestamp):
                    data[key] = value.isoformat()
                    data_list_updated.append(data)
    return data_list_updated
