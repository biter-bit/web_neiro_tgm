from email.policy import default
import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
from sqlalchemy import text, ForeignKey, BIGINT, String, Boolean
from typing import Annotated, Optional
from utils.enum import TariffCode, AiModelName, PaymentName


intpk = Annotated[int, mapped_column(primary_key=True)]
str_50 = Annotated[str, 50]
created = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated = Annotated[
    datetime.datetime, mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.datetime.utcnow
    )
]


class Base(DeclarativeBase):
    """Базовый класс моделей."""

    pass


# class AiOption(Base):
#     """Класс представляет собой доп. настройки для нейронных сетей."""
#
#     __tablename__ = "ai_option"
#
#     id: Mapped[intpk]
#     name: Mapped[str | None]
#     description: Mapped[str | None]
#
#     # element: Mapped[str | None]
#     # values_type: Mapped[str | None]
#     # option_type: Mapped[str | None]
#     # parameters: Mapped[str | None]
#     # defaults: Mapped[str | None]
#
#     created_at: Mapped[created]
#     updated_at: Mapped[updated]
#
#     option: Mapped[list["AiModel"]] = relationship(
#         back_populates="option",
#         secondary="ai_model_option"
#     )

class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[intpk]
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"),
                                                   nullable=True, default=None)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariff.id", ondelete='SET NULL'),
                                                  nullable=True, default=None)
    provider: Mapped[PaymentName]
    created_at: Mapped[created]
    updated_at: Mapped[updated]
    hash_transaction: Mapped[str | None]

    profiles: Mapped["Profile"] = relationship()
    tariffs: Mapped["Tariff"] = relationship()

class AiModel(Base):
    """Класс представляет из себя модель нейронных сетей"""
    __tablename__ = "ai_model"

    code: Mapped[str | None] = mapped_column(primary_key=True)
    name: Mapped[str | None]
    type: Mapped[str | None]
    is_active: Mapped[bool | None]

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    # option: Mapped[list["AiOption"]] = relationship(
    #     back_populates="option",
    #     secondary="ai_model_option"
    # )


class Tariff(Base):
    """Класс представляет собой тариф для пользования нейронными сетями"""
    __tablename__ = "tariff"

    id: Mapped[intpk]
    name: Mapped[str]
    code: Mapped[TariffCode] = mapped_column(unique=True)
    description: Mapped[str | None]
    chatgpt_4o_daily_limit: Mapped[int | None] = mapped_column(default=0)
    chatgpt_4o_mini_daily_limit: Mapped[int | None] = mapped_column(default=0)
    midjourney_6_0_daily_limit: Mapped[int | None] = mapped_column(default=0)
    midjourney_5_2_daily_limit: Mapped[int | None] = mapped_column(default=0)
    days: Mapped[int | None]
    price_rub: Mapped[int | None]
    price_stars: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    profiles: Mapped["Profile"] = relationship(back_populates="tariffs")

class Profile(Base):
    """Класс представляет собой профиль пользователя бота"""
    __tablename__ = "profile"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tgid: Mapped[int] = mapped_column(BIGINT, unique=True)
    username: Mapped[Optional[str]] = mapped_column(unique=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    email: Mapped[str | None]
    url_telegram: Mapped[str | None]
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariff.id", ondelete='SET NULL'),
                                                  nullable=True, default=None)
    ai_model_id: Mapped[int | None] = mapped_column(ForeignKey("ai_model.code", ondelete='SET NULL'),
                                                 nullable=True, default="gpt-4o-mini")
    update_daily_limits_time: Mapped[created]
    chatgpt_4o_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)
    chatgpt_4o_mini_daily_limit: Mapped[Optional[int]] = mapped_column(default=30)
    mj_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)
    count_request: Mapped[int | None] = mapped_column(default=0)
    # midjourney_6_0_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)
    # midjourney_5_2_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)

    is_staff: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    tariffs: Mapped["Tariff"] = relationship(back_populates="profiles")
    ai_models_id: Mapped["AiModel"] = relationship()


# class AiModelOptionM2M(Base):
#     """Класс представляет себя связующую таблицу опций модели и саму модель"""
#
#     __tablename__ = "ai_model_option"
#
#     id: Mapped[intpk]
#     ai_model_id: Mapped[str] = mapped_column(
#         String(50),
#         ForeignKey("ai_model.code", ondelete="CASCADE"),
#         primary_key=True
#     )
#     ai_option_id: Mapped[int] = mapped_column(
#         BIGINT,
#         ForeignKey("ai_option.id", ondelete="CASCADE"),
#         primary_key=True
#     )


class ChatSession(Base):
    """Класс представляет себя сессию чата (историю переписки с моделью)"""

    __tablename__ = "chat_session"

    id: Mapped[intpk]
    name: Mapped[str]
    ai_model_id: Mapped[int | None] = mapped_column(ForeignKey("ai_model.code", ondelete="CASCADE"),
                                                   nullable=True, default=None)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"),
                                                  nullable=True, default=None)
    active_generation: Mapped[Optional[bool]] = mapped_column(default=False)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    text_queries: Mapped[list["TextQuery"]] = relationship(
        back_populates="chat_session"
    )
    image_queries: Mapped[list["ImageQuery"]] = relationship(
        back_populates="chat_session"
    )


class TextQuery(Base):
    """Класс представляет себя запрос, отправленный к текстовой модели и от нее"""

    __tablename__ = "text_query"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_session.id", ondelete="CASCADE"),
                                                       nullable=True, default=None)
    query: Mapped[Optional[str]] = mapped_column(nullable=True)
    answer: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[Optional[str]] = mapped_column(nullable=False)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    chat_session: Mapped["ChatSession"] = relationship(
        back_populates="text_queries"
    )


class ImageQuery(Base):
    """Класс представляет себя запрос, отправленный к модели генерации картинки и от нее"""

    __tablename__ = "image_query"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_session.id", ondelete="CASCADE"),
                                                       nullable=True, default=None)
    query: Mapped[Optional[str]] = mapped_column(nullable=True)
    answer: Mapped[Optional[str]] = mapped_column(nullable=True)
    jobid: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[Optional[str]] = mapped_column(nullable=False)


    created_at: Mapped[created]
    updated_at: Mapped[updated]

    chat_session: Mapped["ChatSession"] = relationship(
        back_populates="image_queries"
    )