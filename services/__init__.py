from config import settings
from .payment import Robokassa
from .logger_service import create_logger

logger = create_logger(settings.LEVEL_LOGGER)
robokassa_obj = Robokassa(
    login=settings.ROBOKASSA_LOGIN,
    password_1=settings.ROBOKASSA_PASS_1,
    password_2=settings.ROBOKASSA_PASS_2
)