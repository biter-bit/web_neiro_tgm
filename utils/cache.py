from services import redis
import json
from db_api.models import Profile, Tariff, AiModel
from config import settings


async def remove_user_in_notification(user_tgid: int | None) -> str:
    """Удали пользователя из списка 'Пользовательские уведомления' в redis"""
    await redis.srem('users_notifications', user_tgid)
    return "Ok"

async def add_user_in_notification(user_tgid: int | None) -> str:
    """Добавь пользователя в список 'Пользовательские уведомления' в redis"""
    await redis.sadd("users_notifications", user_tgid)
    return "Ok"

async def get_users_from_notification():
    """Получи пользователей из списка 'Пользовательские уведомления' в redis"""
    users_notifications = await redis.smembers("users_notifications")
    return users_notifications

async def get_cache_profile(profile_tgid: int | None) -> str:
    """Получает обьект из кэша"""
    cache_value = await redis.get(profile_tgid)
    return cache_value

async def set_cache_profile(profile_tgid: int | None, json_profile: str) -> str:
    """Добавляет обьект в кэш"""
    await redis.setex(profile_tgid, settings.TTL, json_profile)
    return "Ok"

async def serialization_profile(profile_obj: Profile) -> str:
    """Сериализует обьект пользователя в строку json"""
    profile_dict = profile_obj.to_dict()
    json_profile = json.dumps(profile_dict)
    return json_profile

async def deserialization_profile(cache_value_profile: str) -> Profile:
    """Десериализует строку пользователя в обьект Profile"""
    profile_data = json.loads(cache_value_profile)
    tariff = Tariff(**profile_data['tariffs'])
    ai_models_id = AiModel(**profile_data['ai_models_id'])
    profile_data['tariffs'] = tariff
    profile_data['ai_models_id'] = ai_models_id
    profile = Profile(**profile_data)
    return profile