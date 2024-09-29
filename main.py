from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json
import logging
from db_api import api_invoice_async, api_profile_async
from payment_app.db_api.models import Profile
from services import robokassa_obj

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка Jinja2
templates = Jinja2Templates(directory="templates")


def format_request_data(request):
    request_data = {
        "HTTP Method": request.method,
        "URL": str(request.url),
        "Client IP": request.client.host,
        "Headers": {key.decode(): value.decode() for key, value in request.headers.raw},
        "Query Parameters": dict(request.query_params),
        "Path Parameters": dict(request.path_params)
    }
    return json.dumps(request_data, indent=4, ensure_ascii=False)

@app.get('/result', response_class=HTMLResponse)
async def result_confirm(request: Request):
    invoice = await api_invoice_async.get_invoice(request.get("InvId"))
    if not invoice:
        logger.error(f"Not invoice ERROR | {invoice}")
        return "ERROR"

    price = request.get("OutSum")
    inv_id = request.get("InvId")
    email = request.get("EMail")
    signature = request.get("SignatureValue")

    if not robokassa_obj.check_signature(inv_id=inv_id, price=price, recv_signature=signature):
        logger.error(f"Check signature ERROR | {inv_id}")
        return "Check signature ERROR"

    if email and invoice.profile.email != email.lower():
        await api_profile_async.update_email(invoice.profiles.id, email.lower())
    profile = await api_profile_async.update_tariff_of_profile(invoice.profiles.id, 2)
    return f"OK{inv_id}"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    formatted_request = format_request_data(request)
    return templates.TemplateResponse("success.html", {"request": request, "request_data": formatted_request})
