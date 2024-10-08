from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json
import logging
from db_api import api_invoice_async, api_profile_async
from services import robokassa_obj
from utils.cache import set_cache_profile, serialization_profile

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
    formatted_request = format_request_data(request)
    logger.info({"request": request, "request_data": formatted_request})
    query_params = request.query_params

    logger.info({"query_params": query_params})

    invoice = await api_invoice_async.get_invoice(int(query_params.get("InvId")))
    if not invoice:
        logger.error(f"Not invoice ERROR | {invoice}")
        return "ERROR"

    price = query_params.get("OutSum")
    inv_id = int(query_params.get("InvId"))
    email = query_params.get("EMail")
    signature = query_params.get("SignatureValue")


    if not robokassa_obj.check_signature(inv_id=inv_id, price=price, recv_signature=signature):
        logger.error(f"Check signature ERROR | {inv_id}")
        return "Check signature ERROR"


    if email and invoice.profiles.email != email.lower():
        await api_profile_async.update_email_of_profile(invoice.profiles.id, email.lower())

    profile = await api_profile_async.update_subscription_profile(invoice.profiles.id, 2)
    await set_cache_profile(profile.tgid, await serialization_profile(profile))
    return f"OK{inv_id}"

@app.get("/success", response_class=HTMLResponse)
async def success_payment(request: Request):
    formatted_request = format_request_data(request)
    # return templates.TemplateResponse("success.html", {"request": request, "request_data": formatted_request})
    return templates.TemplateResponse("success.html", {"request": request, "request_data": "Оплата прошла успешно!"})


@app.get("/fail", response_class=HTMLResponse)
async def success_payment(request: Request):
    formatted_request = format_request_data(request)
    # return templates.TemplateResponse("success.html", {"request": request, "request_data": formatted_request})
    return templates.TemplateResponse("success.html", {"request": request, "request_data": "Оплата не удалась."})