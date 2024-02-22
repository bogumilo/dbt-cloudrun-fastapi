import os
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud.logging import Client
from dbt.cli.main import dbtRunner, dbtRunnerResult
from pydantic import BaseModel


app = FastAPI()
templates = Jinja2Templates(directory="templates")

client = Client()
client.setup_logging()

class TargetRequest(BaseModel):
    target: str = "prod"

@app.get("/", response_class=HTMLResponse)
def hello(request: Request):
    """Return a friendly HTTP greeting."""
    message = "It's running!"

    # Fetch Cloud Run environment variables
    service = os.environ.get('K_SERVICE', 'Unknown service')
    revision = os.environ.get('K_REVISION', 'Unknown revision')

    logging.info(f'Service: {service}, Revision: {revision}')

    return templates.TemplateResponse("index.html",
                                      {"request": request,
                                       "message": message,
                                       "Service": service,
                                       "Revision": revision})

@app.post("/daily")
async def daily(request: Request):
    """DBT Daily Runner."""
    try:
        json_data = await request.json()
        target_request = TargetRequest(**json_data)

        # Initialize dbt (Ensure compatibility of 'dbtRunner' with FastAPI)
        dbt = dbtRunner()

        # CLI arguments setup
        cli_args = ["--project-dir", "dbt", "--profiles-dir", "dbt"]
        target_arg = ['--target', target_request.target]

        logging.info('Running: dbt source freshness')
        result: dbtRunnerResult = dbt.invoke(['source', 'freshness'] + cli_args + target_arg)

        # Handle the result object provided by 'dbtRunnerResult'
        if not result.success:  # Assuming 'success' attribute is available
           raise HTTPException(status_code=500, detail="DBT source freshness failed")

        logging.info('Running: dbt build')
        result: dbtRunnerResult = dbt.invoke(['build'] + cli_args + target_arg)

        # Handle the result object provided by 'dbtRunnerResult'
        if not result.success:
           raise HTTPException(status_code=500, detail="DBT build failed")

        logging.info("DBT Run Successfully")
        return "DBT Run Successfully"

    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
