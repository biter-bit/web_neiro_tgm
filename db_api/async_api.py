from db_api.interface_api import DataBaseApiInterface
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from config import settings
from db_api.models import Profile, AiModel, ChatSession, TextQuery, Tariff, ImageQuery, Invoice
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from utils.enum import PaymentName
from utils.enum import AiModelName


class DBApiAsync(DataBaseApiInterface):
    def __init__(self):
        self.async_engine_db = None
        self.async_session_db = None
        self._create_engine()
        self._create_session()

    def _create_engine(self):
        """Создание асинхронного движка базы данных"""
        self.async_engine_db = create_async_engine(url=settings.url_connect_with_asyncpg, echo=True)

    def _create_session(self):
        """Создание асинхронной сессии для работы с базой данных"""
        self.async_session_db = async_sessionmaker(self.async_engine_db)

    async def update_data(self, obj):
        """Обнови данные для обьекта в бд"""
        async with self.async_session_db() as session:
            await session.merge(obj)
            await session.commit()
            return "Ok"

class ApiTextQueryAsync(DBApiAsync):
    async def save_message(self, answer: str, text_query_id):
        """Сохрани ответ текстовой нейронки в бд"""
        async with self.async_session_db() as session:
            text_query = await session.get(TextQuery, text_query_id)
            text_query.answer = answer
            text_query.status = 'finish'
            await session.commit()
            return text_query

    async def create_text_query(self, query: str, chat_session_id):
        """Подготовь текстовый запрос"""
        async with self.async_session_db() as session:
            text_query = TextQuery(
                status="in_process",
                query=query,
                chat_session_id=chat_session_id,
            )
            session.add(text_query)
            await session.commit()
            await session.refresh(text_query)
            return text_query

class ApiInvoiceAsync(DBApiAsync):
    async def create_invoice(self, profile_id: int, tariff_id: int, provider: PaymentName) -> Invoice:
        """Создай транзакцию"""
        async with self.async_session_db() as session:
            invoice_obj = Invoice(
                provider=provider.name,
                tariff_id=tariff_id,
                profile_id=profile_id,
            )
            session.add(invoice_obj)
            await session.commit()
            await session.refresh(invoice_obj)
            return invoice_obj

    async def get_invoice(self, invoice_id: int) -> Invoice:
        """Получи транзакцию"""
        async with self.async_session_db() as session:
            query = (
                select(Invoice)
                .filter_by(id=invoice_id)
                .options(joinedload(Invoice.profiles))
                .options(joinedload(Invoice.tariffs))
            )
            result = await session.execute(query)
            invoice_obj = result.unique().scalars().first()
            return invoice_obj

    async def pay_invoice(self, invoice_id: int) -> Invoice:
        """Оплати транзакцию"""
        async with self.async_session_db() as session:
            query = (
                select(Invoice)
                .filter_by(id=invoice_id)
                .options(joinedload(Invoice.profiles))
                .options(joinedload(Invoice.tariffs))
            )
            result = await session.execute(query)
            invoice_obj = result.unique().scalars().first()
            invoice_obj.is_paid = True
            await session.commit()
            await session.refresh(invoice_obj)
            return invoice_obj

class ApiImageQueryAsync(DBApiAsync):
    async def create_image_query(self, query: str, chat_session_id: int, jobid: str) -> ImageQuery:
        """Подготовь запрос генерации картинки"""
        async with self.async_session_db() as session:
            image_query = ImageQuery(
                status="in_process",
                query=query,
                chat_session_id=chat_session_id,
                jobid=jobid
            )
            session.add(image_query)
            await session.commit()
            await session.refresh(image_query)
            return image_query

    async def get_image_query(self, query_id: str):
        """Получи запрос картинки"""
        async with self.async_session_db() as session:
            image_query = await session.get(ImageQuery, query_id)
            return image_query

    async def save_answer_query(self, url_photo: str, image_id: UUID) -> str:
        """Сохрани результат генерации фото"""
        async with self.async_session_db() as session:
            image_query = await session.get(ImageQuery, image_id)
            image_query.answer = url_photo
            await session.commit()
            return "Ok"

class ApiChatSessionAsync(DBApiAsync):
    async def get_text_messages_from_session(self, session_id: int, name_ai_model: str):
        """Верни список сообщений с нейронной сетью в сессии"""
        async with self.async_session_db() as session:
            messages = []
            query = (
                select(ChatSession)
                .filter_by(id=session_id, ai_model_id=name_ai_model)
                .options(selectinload(ChatSession.text_queries))
            )
            result = await session.execute(query)
            session_chat = result.unique().scalars().first()
            for msg in session_chat.text_queries:
                if msg.query and msg.answer:
                    messages.append({"role": "user", "content": msg.query})
                    messages.append({"role": "assistant", "content": msg.answer})
            return messages

    async def delete_context_from_session(self, session_id: int, profile: Profile) -> str:
        """Удали выбранную сессию и создай новую"""
        async with self.async_session_db() as session:
            session_obj = await session.get(ChatSession, session_id)
            if not session_obj:
                return "Not object"
            await session.delete(session_obj)
            await session.commit()
        await self.get_or_create_session(profile, profile.ai_model_id)
        return "Ok"

    async def get_or_create_session(self, profile: Profile, model: str):
        """Создай сессию для пользователя если ее нет"""
        async with self.async_session_db() as session:
            query = (
                select(ChatSession)
                .filter_by(profile_id=profile.id, ai_model_id=model)
                .options(selectinload(ChatSession.text_queries))
                .options(selectinload(ChatSession.image_queries))
            )
            result = await session.execute(query)
            session_chat = result.unique().scalars().first()
            if not session_chat:
                session_chat = ChatSession(
                    profile_id=profile.id,
                    ai_model_id=model,
                    name='Новый диалог 1',
                )
                session.add(session_chat)
                await session.commit()
                await session.refresh(session_chat)
            return session_chat

    async def active_generic_in_session(self, chat_session_id: int) -> bool:
        """Включи статус генерации в указанной сессии"""
        async with self.async_session_db() as session:
            chat_session = await session.get(ChatSession, chat_session_id)
            chat_session.active_generation = True
            await session.commit()
            return True

    async def deactivate_generic_in_session(self, chat_session_id: int):
        """Выключи статус генерации в указанной сессии"""
        async with self.async_session_db() as session:
            chat_session = await session.get(ChatSession, chat_session_id)
            chat_session.active_generation = False
            await session.commit()
            return "Ok"

class ApiProfileAsync(DBApiAsync):
    async def replace_model_of_profile(self, profile: Profile, model: str):
        """Измени модель для пользователя"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(tgid=profile.tgid)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile_obj = result.unique().scalars().first()
            profile_obj.ai_model_id = model
            await session.commit()
            await session.refresh(profile_obj)
            return profile_obj

    async def update_email_of_profile(self, profile_id: int, email: str):
        """Обнови почту пользователя"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(id=profile_id)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile_obj = result.unique().scalars().first()
            profile_obj.email = email
            await session.commit()
            return "Ok"

    async def subtracting_count_request_to_model_chatgpt_4o(self, profile_id: int) -> str:
        """Удали кол-во токенов запроса"""
        async with self.async_session_db() as session:
            profile_obj = await session.get(Profile, profile_id)
            profile_obj.chatgpt_4o_daily_limit -= 1
            await session.commit()
            return "Ok"

    async def subtracting_count_request_to_model_chatgpt_4o_mini(self, profile_id: int) -> str:
        """Вычти кол-во допустимых запросов к модели chatgpt_4o_mini на 1 для пользователя."""
        async with self.async_session_db() as session:
            profile_id = await session.get(Profile, profile_id)
            profile_id.chatgpt_4o_mini_daily_limit -= 1
            await session.commit()
            return "Ok"

    async def subtracting_count_request_to_model_mj(self, profile_id: int) -> str:
        """Вычти кол-во допустимых запросов к модели chatgpt_4o_mini на 1 для пользователя."""
        async with self.async_session_db() as session:
            profile_id = await session.get(Profile, profile_id)
            profile_id.mj_daily_limit -= 1
            profile_id.count_request += 1
            await session.commit()
            return "Ok"

    async def subtracting_count_request_to_model_gpt(self, profile_id: int, model_id: str) -> str:
        """Вычти кол-во допустимых запросов к модели chatgpt_4o_mini на 1 для пользователя."""
        async with self.async_session_db() as session:
            profile = await session.get(Profile, profile_id)
            if model_id == AiModelName.GPT_4_O.value:
                profile.chatgpt_4o_daily_limit -= 1
            elif model_id == AiModelName.GPT_4_O_MINI.value:
                profile.chatgpt_4o_mini_daily_limit -= 1
            profile.count_request += 1
            await session.commit()
            return "Ok"

    async def get_or_create_profile(self, tgid: int, username: str, first_name: str, last_name: str, url: str):
        """Создай пользователя если его нет в бд"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(tgid=tgid)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile = result.unique().scalars().first()
            if not profile:
                profile = Profile(
                    username=username,
                    tgid=tgid,
                    first_name=first_name,
                    last_name=last_name,
                    url_telegram=url,
                    tariff_id=1
                )
                session.add(profile)
                await session.commit()
                query = (
                    select(Profile)
                    .filter_by(tgid=tgid)
                    .options(joinedload(Profile.tariffs))
                    .options(joinedload(Profile.ai_models_id))
                )
                result = await session.execute(query)
                profile = result.unique().scalars().first()
            return profile

    async def update_subscription_profile(self, profile_id: int, tariff_id: int):
        """Сделай премиум доступ для пользователя"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(id=profile_id)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile_obj = result.unique().scalars().first()
            profile_obj.tariff_id = tariff_id
            profile_obj.chatgpt_4o_mini_daily_limit = -1
            profile_obj.chatgpt_4o_daily_limit = 50
            profile_obj.mj_daily_limit = 35
            await session.commit()
            await session.refresh(profile_obj)
            return profile_obj

class ApiTariffAsync(DBApiAsync):
    async def get_tariff(self, tariff_id):
        """Получи тариф"""
        async with self.async_session_db() as session:
            tariff_obj = await session.get(Tariff, tariff_id)
            return tariff_obj

class ApiAiModelAsync(DBApiAsync):
    async def get_all_ai_models(self) -> dict:
        """Получи все модели нейронок из бд в виде словаря"""
        async with self.async_session_db() as session:
            result = await session.execute(select(AiModel))
            ai_models = result.scalars().all()
            ai_models_dict = {model.code: model for model in ai_models}
        return ai_models_dict