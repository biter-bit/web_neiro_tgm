import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
from sqlalchemy import text, ForeignKey, BIGINT, Boolean
from typing import Annotated, Optional
from utils.enum import TariffCode, PaymentName


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

class Profile(Base):
    """Класс представляет собой профиль пользователя бота"""
    __tablename__ = "profile"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tgid: Mapped[int] = mapped_column(BIGINT, unique=True)
    username: Mapped[Optional[str]] = mapped_column(unique=False, nullable=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    email: Mapped[str | None]
    url_telegram: Mapped[str | None]
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariff.id", ondelete='SET NULL'),
                                                  nullable=True, default=None)
    ai_model_id: Mapped[str] = mapped_column(ForeignKey("ai_model.code", ondelete='SET NULL'),
                                                 nullable=True, default="gpt-4o-mini")
    date_subscription: Mapped[datetime.datetime] = mapped_column(nullable=True)
    chatgpt_4o_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)

    chatgpt_4o_mini_daily_limit: Mapped[Optional[int]] = mapped_column(default=-1)
    chatgpt_o1_preview_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)
    chatgpt_o1_mini_daily_limit: Mapped[Optional[int]] = mapped_column(default=0)
    mj_daily_limit_5_2: Mapped[Optional[int]] = mapped_column(default=0)
    mj_daily_limit_6_0: Mapped[Optional[int]] = mapped_column(default=0)
    count_request: Mapped[int | None] = mapped_column(default=0)
    recurring: Mapped[bool] = mapped_column(default=False)
    referral_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("ref_link.id", ondelete="SET NULL", use_alter=True),
        nullable=True
    )
    is_promo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_staff: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    tariff: Mapped["Tariff"] = relationship(back_populates="profiles")
    ai_model: Mapped["AiModel"] = relationship(back_populates="choice_model_profiles")

    my_ref_links: Mapped[list["RefLink"]] = relationship(back_populates="owner", foreign_keys="RefLink.owner_id")
    referral_link: Mapped["RefLink"] = relationship(back_populates="referral_profiles", foreign_keys="Profile.referral_link_id")

    # my_links: Mapped[list["RefLink"]] = relationship(back_populates="owner", foreign_keys="RefLink.owner_id")
    # referral_link: Mapped["RefLink"] = relationship(back_populates="referral_profiles", foreign_keys="RefLink.id")

    def to_dict(self):
        """Преобразует объект Profile в словарь."""
        return {
            "id": str(self.id),
            "tgid": self.tgid,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "url_telegram": self.url_telegram,
            "tariff_id": self.tariff_id,
            "ai_model_id": self.ai_model_id,
            "date_subscription": self.date_subscription.isoformat() if self.date_subscription and isinstance(self.date_subscription, datetime.datetime) else None,
            "chatgpt_4o_daily_limit": self.chatgpt_4o_daily_limit,
            "chatgpt_4o_mini_daily_limit": self.chatgpt_4o_mini_daily_limit,
            "mj_daily_limit_5_2": self.mj_daily_limit_5_2,
            "mj_daily_limit_6_0": self.mj_daily_limit_6_0,
            "count_request": self.count_request,
            "is_staff": self.is_staff,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at and isinstance(self.created_at, datetime.datetime) else None,  # Преобразуем дату
            "updated_at": self.updated_at.isoformat() if self.updated_at and isinstance(self.updated_at, datetime.datetime) else None,  # Преобразуем дату
            # "my_ref_links": [link.to_dict() for link in self.my_ref_links],
            # "referral_link": self.referral_link.to_dict() if self.referral_link else None,
            # "tariff": self.tariff.to_dict() if self.tariff else None,
            # "ai_model": self.ai_model.to_dict() if self.ai_model else None,
        }

class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[intpk]
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"),
                                                   nullable=True, default=None)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariff.id", ondelete='SET NULL'),
                                                  nullable=True, default=None)
    child_attempt_debit: Mapped[int] = mapped_column(default=0)
    provider: Mapped[PaymentName]
    created_at: Mapped[created]
    updated_at: Mapped[updated]
    hash_transaction: Mapped[str | None]
    is_mother: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profiles: Mapped["Profile"] = relationship()
    tariffs: Mapped["Tariff"] = relationship()

class AiModel(Base):
    """Класс представляет из себя модель нейронных сетей"""
    __tablename__ = "ai_model"

    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str | None]
    type: Mapped[str | None]
    is_active: Mapped[bool | None]
    position_number: Mapped[int | None] = mapped_column(unique=True, default=None)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    choice_model_profiles: Mapped[list["Profile"]] = relationship(back_populates="ai_model")

    def to_dict(self):
        """Преобразует объект AiModel в словарь."""
        return {
            "code": self.code,
            "name": self.name,
            "type": str(self.type),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,  # Преобразуем дату
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # Преобразуем дату
        }

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

    profiles: Mapped["Profile"] = relationship(back_populates="tariff")

    def to_dict(self):
        """Преобразует объект Tariff в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "code": str(self.code),
            "description": self.description,
            "chatgpt_4o_daily_limit": self.chatgpt_4o_daily_limit,
            "chatgpt_4o_mini_daily_limit": self.chatgpt_4o_mini_daily_limit,
            "midjourney_6_0_daily_limit": self.midjourney_6_0_daily_limit,
            "midjourney_5_2_daily_limit": self.midjourney_5_2_daily_limit,
            "days": self.days,
            "price_rub": self.price_rub,
            "price_stars": self.price_stars,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,  # Преобразуем дату
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # Преобразуем дату
        }

class RefLink(Base):
    """Класс представляет собой реферальные ссылки пользователей и статистику по ним"""
    __tablename__ = "ref_link"

    id: Mapped[intpk]
    name: Mapped[Optional[str]] = mapped_column(unique=False)
    link: Mapped[str] = mapped_column(nullable=False, unique=True)
    count_clicks: Mapped[Optional[int]] = mapped_column(default=0)
    count_buys: Mapped[Optional[int]] = mapped_column(default=0)
    count_new_users: Mapped[Optional[int]] = mapped_column(default=0)
    sum_buys_rub: Mapped[Optional[int]] = mapped_column(default=0)
    sum_buys_stars: Mapped[Optional[int]] = mapped_column(default=0)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profile.id", ondelete='CASCADE'), nullable=False)

    created_at: Mapped[created]
    updated_at: Mapped[updated]

    owner: Mapped["Profile"] = relationship(back_populates="my_ref_links", foreign_keys="RefLink.owner_id")
    referral_profiles: Mapped[list["Profile"]] = relationship(back_populates="referral_link", foreign_keys="Profile.referral_link_id")
    # owner: Mapped["Profile"] = relationship(back_populates="my_links", foreign_keys="Profile.id")
    # referral_profiles: Mapped[list["Profile"]] = relationship(back_populates="referral_link", foreign_keys="Profile.referral_link_id")

    def to_dict(self):
        """Преобразует обьект RefLink в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "link": self.link,
            "count_clicks": self.count_clicks,
            "count_buys": self.count_buys,
            "count_new_users": self.count_new_users,
            "sum_buys_rub": self.sum_buys_rub,
            "sum_buys_stars": self.sum_buys_stars,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner": self.owner.to_dict() if self.owner else None,
            "referral_profiles": [referral.to_dict() for referral in self.referral_profiles],
        }

class ChatSession(Base):
    """Класс представляет себя сессию чата (историю переписки с моделью)"""

    __tablename__ = "chat_session"

    id: Mapped[intpk]
    name: Mapped[str]
    ai_model_id: Mapped[str] = mapped_column(ForeignKey("ai_model.code", ondelete="CASCADE"),
                                                   nullable=True, default=None)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"),
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
    def to_dict(self):
        """Преобразует объект Profile в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "ai_model_id": self.ai_model_id,
            "profile_id": str(self.profile_id),
            "active_generation": self.active_generation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

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

class TariffAiModelAssociation(Base):
    """Лимиты моделей в тарифах."""
    __tablename__ = "tariff_ai_model_association"

    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariff.id", ondelete='CASCADE'), primary_key=True)
    ai_model_id: Mapped[int] = mapped_column(ForeignKey("ai_model.code", ondelete='CASCADE'), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(default=0)
    created_at: Mapped[created]
    updated_at: Mapped[updated]

class AiModelProfileAssociation(Base):
    """Остаток лимитов моделей пользователей."""
    __tablename__ = "aimodel_profile_association"

    profile_id: Mapped[int] = mapped_column(ForeignKey("profile.id", ondelete='CASCADE'), primary_key=True)
    ai_model_id: Mapped[int] = mapped_column(ForeignKey("ai_model.code", ondelete='CASCADE'), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(default=0)
    created_at: Mapped[created]
    updated_at: Mapped[updated]

class RefLinkProfileAssociation(Base):
    """Переходы по реферальным ссылкам."""
    __tablename__ = "reflink_profile_association"
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)
    ref_link_id: Mapped[int] = mapped_column(ForeignKey("ref_link.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[created]
    updated_at: Mapped[updated]