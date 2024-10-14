from datetime import datetime, timedelta

from db_api.interface_api import DataBaseApiInterface
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from config import settings
from db_api.models import Profile, AiModel, ChatSession, TextQuery, Tariff, ImageQuery, Invoice, RefLink
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from utils.enum import PaymentName
from sqlalchemy import func

from utils.enum import AiModelName, PaymentName


class DBApiAsync(DataBaseApiInterface):
    def __init__(self):
        self.async_engine_db = None
        self.async_session_db = None
        self._create_engine()
        self._create_session()

    def _create_engine(self):
        """Создание асинхронного движка базы данных"""
        self.async_engine_db = create_async_engine(url=settings.url_connect_with_asyncpg, echo=False)

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

class ApiRefLinkAsync(DBApiAsync):
    async def create_ref_link(self, name_link, owner_id):
        """Создай реферальную ссылку"""
        async with self.async_session_db() as session:
            # Получаем общее количество записей в RefLink
            total_links_count = await session.execute(func.count(RefLink.id))
            total_links_count = total_links_count.scalar()  # Получаем число

            # Увеличиваем общее количество на 1 для использования в ссылке
            new_id = total_links_count + 1
            ref_link = RefLink(
                name=name_link,
                owner_id=owner_id,
                link=f'{settings.USERNAME_BOT}?start={new_id}'
            )
            session.add(ref_link)  # Добавляем объект в сессию
            await session.commit()  # Сохраняем изменения в базе данных
            await session.refresh(ref_link)
            return ref_link

    async def add_click(self, link: str) -> RefLink | None:
        """Прибавь кол-во переходов по ссылке"""
        async with self.async_session_db() as session:
            query = (
                select(RefLink)
                .filter_by(link=link)
                .options(joinedload(RefLink.owner))
            )
            result = await session.execute(query)
            ref_link = result.unique().scalars().first()
            if ref_link is None:
                # Ссылка не найдена, обработка ситуации
                return None
            ref_link.count_clicks += 1
            await session.commit()
            await session.refresh(ref_link)

            return ref_link

    async def add_count_new_users(self, link_id: int) -> RefLink | None:
        """Прибавь кол-во переходов по ссылке"""
        async with self.async_session_db() as session:
            query = (
                select(RefLink)
                .filter_by(id=link_id)
                .options(joinedload(RefLink.owner))
            )
            result = await session.execute(query)
            ref_link = result.unique().scalars().first()
            if ref_link is None:
                # Ссылка не найдена, обработка ситуации
                return None
            ref_link.count_new_users += 1
            await session.commit()
            await session.refresh(ref_link)

            return ref_link

    async def add_count_buy(self, link_id: int) -> RefLink | None:
        """Прибавь кол-во покупок по ссылке"""
        async with self.async_session_db() as session:
            query = (
                select(RefLink)
                .filter_by(id=link_id)
                .options(joinedload(RefLink.owner))
            )
            result = await session.execute(query)
            ref_link = result.unique().scalars().first()
            if ref_link is None:
                # Ссылка не найдена, обработка ситуации
                return None
            ref_link.count_buys += 1
            await session.commit()
            await session.refresh(ref_link)

            return ref_link

    async def add_sum_buy(self, link_id: int, sum_buy: int, category: str) -> RefLink | None:
        """Прибавь сумму покупок по ссылке"""
        async with self.async_session_db() as session:
            query = (
                select(RefLink)
                .filter_by(id=link_id)
                .options(joinedload(RefLink.owner))
            )
            result = await session.execute(query)
            ref_link = result.unique().scalars().first()
            if ref_link is None:
                # Ссылка не найдена, обработка ситуации
                return None
            if category == PaymentName.STARS.value:
                ref_link.sum_buys_stars += sum_buy
            else:
                ref_link.sum_buys_rub += sum_buy
            await session.commit()
            await session.refresh(ref_link)

            return ref_link

class ApiInvoiceAsync(DBApiAsync):
    async def create_invoice(self, profile_id: int, tariff_id: int, provider: PaymentName, is_mother: bool = False) -> Invoice:
        """Создай транзакцию"""
        async with self.async_session_db() as session:
            invoice_obj = Invoice(
                provider=provider.name,
                tariff_id=tariff_id,
                profile_id=profile_id,
                is_mother=is_mother
            )
            session.add(invoice_obj)
            await session.commit()
            await session.refresh(invoice_obj)
            return invoice_obj

    async def get_invoice_mother(self, profile_id: int) -> Invoice:
        """Получает транзакцию по ID или возвращает все транзакции пользователя"""
        async with self.async_session_db() as session:
            query = (
                select(Invoice)
                .filter_by(profile_id=profile_id, is_paid=True, is_mother=True)
                .options(joinedload(Invoice.profiles))
                .options(joinedload(Invoice.tariffs))
            )
            result = await session.execute(query)
            invoice_obj = result.unique().scalars().first()
            return invoice_obj

    async def get_invoice(self, profile_id: int, invoice_id: int = None) -> Invoice:
        """Получает транзакцию по ID или возвращает все транзакции пользователя"""
        async with self.async_session_db() as session:
            query = (
                select(Invoice)
                .filter_by(profile_id=profile_id)
                .options(joinedload(Invoice.profiles))
                .options(joinedload(Invoice.tariffs))
            )

            # Если указан `invoice_id`, добавляем его к фильтру
            if invoice_id is not None:
                query = query.filter_by(id=invoice_id)

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

    async def subtracting_count_request_to_model_mj(self, profile_id: int, version: str) -> Profile:
        """Вычти кол-во допустимых запросов к модели chatgpt_4o_mini на 1 для пользователя."""
        async with self.async_session_db() as session:
            profile = await session.get(Profile, profile_id)
            if version == '5.2':
                profile.mj_daily_limit_5_2 -= 1
            elif version == "6.0":
                profile.mj_daily_limit_6_0 -= 1
            profile.count_request += 1
            await session.commit()
            await session.refresh(profile)
            return profile

    async def subtracting_count_request_to_model_gpt(self, profile_id: int, model_id: str) -> Profile:
        """Вычти кол-во допустимых запросов к модели chatgpt_4o_mini на 1 для пользователя."""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(id=profile_id)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile = result.unique().scalars().first()
            if model_id == AiModelName.GPT_4_O.value:
                profile.chatgpt_4o_daily_limit -= 1
            elif model_id == AiModelName.GPT_4_O_MINI.value:
                profile.chatgpt_4o_mini_daily_limit -= 1
            elif model_id == AiModelName.GPT_O1_PREVIEW.value:
                profile.chatgpt_o1_preview_daily_limit -= 1
            elif model_id == AiModelName.GPT_O1_MINI.value:
                profile.chatgpt_o1_mini_daily_limit -= 1
            profile.count_request += 1
            await session.commit()
            await session.refresh(profile)
            return profile

    async def check_have_profile(self, tgid: int):
        """Проверь есть ли пользователь в бд или нет"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(tgid=tgid)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile = result.unique().scalars().first()
            if profile:
                return profile
            return None

    async def get_profile(self, tgid: int) -> Profile | None:
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
            if profile:
                return profile
            return None

    async def create_profile(self, tgid: int, username: str, first_name: str, last_name: str, url: str, referal_link_id: int = None):
        async with self.async_session_db() as session:
            profile = Profile(
                username=username,
                tgid=tgid,
                first_name=first_name,
                last_name=last_name,
                url_telegram=url,
                tariff_id=1
            )
            if referal_link_id:
                profile.referal_link_id = referal_link_id
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

    async def get_or_create_profile(self, tgid: int, username: str, first_name: str, last_name: str, url: str, referal_link_id: int = None):
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
                if referal_link_id:
                    profile.referal_link_id = referal_link_id
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

    async def get_profiles_finish_sub(self):
        """Получить пользователей с закончившей подпиской"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(tariff_id=2)
                .filter(Profile.date_subscription <= func.now())
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profiles = result.scalars().all()

            for profile_obj in profiles:
                # Сбрасываем тариф на 1
                profile_obj.tariff_id = 1
                profile_obj.chatgpt_4o_mini_daily_limit = -1
                profile_obj.chatgpt_4o_daily_limit = 0
                profile_obj.mj_daily_limit_5_2 = 0
                profile_obj.mj_daily_limit_6_0 = 0
                profile_obj.chatgpt_o1_preview_daily_limit = 0
                profile_obj.chatgpt_o1_mini_daily_limit = 0

            await session.commit()
            return "Ok"

    async def unsubscribe(self, profile_id: int):
        """Отмени подписку для пользователя с указанным id"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(id=profile_id)
                .filter(Profile.date_subscription <= func.now())
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profile = result.scalars().first()

            profile.tariff_id = 1
            profile.chatgpt_4o_mini_daily_limit = -1
            profile.chatgpt_4o_daily_limit = 0
            profile.mj_daily_limit_5_2 = 0
            profile.mj_daily_limit_6_0 = 0
            profile.chatgpt_o1_preview_daily_limit = 0
            profile.chatgpt_o1_mini_daily_limit = 0
            profile.date_subscription = None

            await session.commit()
            return "Ok"

    async def update_limits_profile(self):
        """Обнови дневной баланс пользователей"""
        async with self.async_session_db() as session:
            query = (
                select(Profile)
                .filter_by(tariff_id=2)
                .options(joinedload(Profile.tariffs))
                .options(joinedload(Profile.ai_models_id))
            )
            result = await session.execute(query)
            profiles = result.scalars().all()

            for profile_obj in profiles:
                profile_obj.chatgpt_4o_mini_daily_limit = -1
                profile_obj.chatgpt_4o_daily_limit = 100
                profile_obj.mj_daily_limit_5_2 = 45
                profile_obj.mj_daily_limit_6_0 = 20
                profile_obj.chatgpt_o1_preview_daily_limit = 20
                profile_obj.chatgpt_o1_mini_daily_limit = 60

            await session.commit()
            return "Ok"


    async def update_subscription_profile(self, profile_id: int, tariff_id: int, recurring: bool = False):
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
            profile_obj.recurring = recurring
            profile_obj.chatgpt_4o_mini_daily_limit = -1
            profile_obj.chatgpt_4o_daily_limit = 100
            profile_obj.mj_daily_limit_5_2 = 45
            profile_obj.mj_daily_limit_6_0 = 20
            profile_obj.chatgpt_o1_preview_daily_limit = 20
            profile_obj.chatgpt_o1_mini_daily_limit = 60
            profile_obj.date_subscription = datetime.now() + timedelta(days=30)
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