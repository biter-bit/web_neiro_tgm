from services import redis
import json
from db_api.models import Profile, Tariff, AiModel

async def get_cache_profile(profile_tgid: int | None) -> str:
    """Получает обьект из кэша"""
    cache_value = await redis.get(profile_tgid)
    return cache_value

async def set_cache_profile(profile_tgid: int | None, json_profile: str) -> str:
    """Добавляет обьект в кэш"""
    await redis.set(profile_tgid, json_profile)
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