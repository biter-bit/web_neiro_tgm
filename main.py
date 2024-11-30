from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import logging
from db_api import api_invoice_async, api_profile_async, api_ref_link_async
from utils.enum import PaymentName
from utils.enum import Price
from config import settings
from services import robokassa_obj

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка Jinja2
templates = Jinja2Templates(directory="templates")

@app.get('/test', response_class=HTMLResponse)
async def test_request(request: Request):
    return templates.TemplateResponse("success.html", {"request": request, "request_data": "Тестовый запрос успешный!"})

@app.get('/result', response_class=HTMLResponse)
async def result_confirm(request: Request):
    query_params = request.query_params

    invoice = await api_invoice_async.pay_invoice(int(query_params.get("InvId")))
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

    invoice = await api_invoice_async.get_invoice(invoice_id=inv_id)
    if email and invoice.profiles.email != email.lower():
        await api_profile_async.update_email_profile(invoice.profile_id, email.lower())


    profile = await api_profile_async.update_subscription_profile(
        invoice.profile_id, invoice.tariff_id, settings.RECURRING
    )

    invoice_mother = await api_invoice_async.get_invoice_mother(profile_id=profile.id)
    await api_invoice_async.reset_attempt_debit(invoice_mother)

    if profile.referal_link_id:
        await api_ref_link_async.add_count_buy(profile.referal_link_id)
        await api_ref_link_async.add_sum_buy(profile.referal_link_id, Price.RUB.value, PaymentName.ROBOKASSA.value)
    # await set_cache_info(profile.tgid, await serialization_profile(profile))
    # await remove_user_in_notification(profile.tgid)
    return f"OK{inv_id}"

@app.get("/success", response_class=HTMLResponse)
async def success_payment(request: Request):
    return templates.TemplateResponse("success.html", {"request": request, "request_data": "Оплата прошла успешно!"})


@app.get("/fail", response_class=HTMLResponse)
async def success_payment(request: Request):
    return templates.TemplateResponse("success.html", {"request": request, "request_data": "Оплата не удалась."})