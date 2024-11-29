from services import redis, logger
import json
from db_api.models import Profile
from config import settings
from typing import Union


async def remove_user_in_notification(user_tgid: int | None) -> str:
    """Удали пользователя из списка 'Пользовательские уведомления' в redis"""
    await redis.srem('users_notifications', user_tgid)
    return "Ok"

async def set_cache_custom(key_obj: Union[str, int], json_profile: str) -> bool:
    """Добавляет обьект в кэш"""
    await redis.setex(key_obj, settings.TTL, json_profile)
    return True

async def serialization_profile(profile: Profile) -> str:
    """Сериализует обьект пользователя в строку json."""
    try:
        profile_dict = profile.to_dict()
        json_profile = json.dumps(profile_dict)
        return json_profile
    except Exception as e:
        logger.error(f"Ошбика сериализации профиля - {profile.tgid}")