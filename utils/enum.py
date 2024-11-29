from enum import Enum

class PaymentName(Enum):
    """Класс со способами оплаты"""
    STARS = "stars"
    ROBOKASSA = "robokassa"

class Price(Enum):
    """Класс с ценами на premium sub"""
    STARS = 190
    RUB = 489

class AiModelName(Enum):
    """Класс с названиями нейросетей"""
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    MIDJOURNEY_6_0 = "mj-6-0"
    MIDJOURNEY_5_2 = "mj-5-2"
    # GPT_O1_PREVIEW = "o1-preview"
    # GPT_O1_MINI = "o1-mini"

class TariffCode(Enum):
    """Класс с названиями тариффов"""
    FREE = "Free"
    PREMIUM = "Premium"
    PROMO = "Promo"
