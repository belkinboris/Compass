"""Схема БД — компании/консультанты с алиасами для идентификации сущностей,
сделки с нормализованными суммами, и аккаунты: вход по ссылке на почту,
подписки на алерты (SavedFilter) и комментарии под сделками.

Зачем алиасы (CompanyAlias/AdvisorAlias), а не просто уникальное имя:
в сырых данных одна и та же фирма встречается под разными строками
("Softline" и "Softline Venture Partners", "ООО «Софтлайн»" и "Софтлайн") —
без таблицы алиасов их нельзя надёжно свести в одну сущность для статистики.
Дедуп через алиасы делаем консервативно (см. pipeline/migrate_to_db.py) —
лучше временно посчитать одну фирму за две, чем ошибочно слить два разных
юрлица в одно.

Зачем amount_confidence, а не просто amount: сумму на карте показываем
только если она достоверно известна; если это оценка аналитиков/СМИ —
это отдельный статус, а не то же самое, что официальное раскрытие.

Зачем enrichment_tier: разница между "полноценной картой" и "записью,
до которой пока не дошли руки" — рабочий статус пайплайна, а не то,
что должен видеть пользователь как отдельный тип карточки.
"""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    # datetime.utcnow() устарел, но колонки здесь — наивный DateTime (без
    # часового пояса): .replace(tzinfo=None) даёт то же самое значение, что
    # и раньше, без предупреждения и без смены формата хранения.
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------- компании ---

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    legal_name: Mapped[str | None] = mapped_column(String(400), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    kpi_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    aliases: Mapped[list["CompanyAlias"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    legal_entities: Mapped[list["LegalEntity"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class CompanyAlias(Base):
    __tablename__ = "company_aliases"
    __table_args__ = (UniqueConstraint("alias", name="uq_company_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"))
    alias: Mapped[str] = mapped_column(String(300))  # нормализованная (lower, без орг.-правовой формы)

    company: Mapped[Company] = relationship(back_populates="aliases")


# ---------------------------------------------- юридические лица / ФНС ---

class LegalEntityMatchStatus(str, enum.Enum):
    confirmed = "confirmed"      # ИНН подтверждён источником или редактором
    probable = "probable"        # найден вероятный кандидат, ещё не публикуем
    unmapped = "unmapped"        # юридическое лицо не установлено


class LegalEntity(Base):
    """Конкретное российское юридическое лицо, связанное с публичным профилем.

    Company — бренд/группа/участник сделки. LegalEntity — именно ООО/АО с ИНН.
    Это разделение не позволяет случайно показать отчётность одного общества как
    показатели всей группы компаний.
    """
    __tablename__ = "legal_entities"
    __table_args__ = (
        UniqueConstraint("inn", name="uq_legal_entity_inn"),
        UniqueConstraint("ogrn", name="uq_legal_entity_ogrn"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="RU")
    legal_name: Mapped[str] = mapped_column(String(500))
    short_name: Mapped[str | None] = mapped_column(String(350), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    kpp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    legal_form: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str | None] = mapped_column(String(160), nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    okved_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    okved_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    charter_capital_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    director_name: Mapped[str | None] = mapped_column(String(350), nullable=True)
    director_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    director_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_provider: Mapped[str] = mapped_column(String(40), default="api-fns")
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    match_status: Mapped[LegalEntityMatchStatus] = mapped_column(
        Enum(LegalEntityMatchStatus), default=LegalEntityMatchStatus.unmapped
    )
    match_confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    manually_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_egr_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped[Company | None] = relationship(back_populates="legal_entities")
    financial_reports: Mapped[list["FinancialReport"]] = relationship(
        back_populates="legal_entity", cascade="all, delete-orphan"
    )
    registry_events: Mapped[list["RegistryEvent"]] = relationship(
        back_populates="legal_entity", cascade="all, delete-orphan"
    )
    ownership_snapshots: Mapped[list["OwnershipSnapshot"]] = relationship(
        back_populates="legal_entity", cascade="all, delete-orphan"
    )


class LegalEntityCandidate(Base):
    """Очередь ручного сопоставления профиля «Компаса» с результатами поиска ФНС."""
    __tablename__ = "legal_entity_candidates"
    __table_args__ = (UniqueConstraint("company_id", "inn", name="uq_company_inn_candidate"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"))
    inn: Mapped[str] = mapped_column(String(12))
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    legal_name: Mapped[str] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(160), nullable=True)
    score: Mapped[float] = mapped_column(Numeric, default=0)
    reasons_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="new")
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class FinancialReport(Base):
    """Нормализованная БФО. Суммы хранятся в рублях, хотя API отдаёт тыс. руб."""
    __tablename__ = "financial_reports"
    __table_args__ = (UniqueConstraint("legal_entity_id", "year", name="uq_entity_report_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_entity_id: Mapped[int] = mapped_column(ForeignKey("legal_entities.id"))
    year: Mapped[int] = mapped_column()
    reporting_standard: Mapped[str] = mapped_column(String(20), default="РСБУ")
    revenue_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gross_profit_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    operating_profit_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    profit_before_tax_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    net_profit_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    assets_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    non_current_assets_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    current_assets_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    cash_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    receivables_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    inventory_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    equity_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    long_term_liabilities_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    short_term_liabilities_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    borrowings_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    payables_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    raw_lines_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    legal_entity: Mapped[LegalEntity] = relationship(back_populates="financial_reports")


class RegistryEvent(Base):
    __tablename__ = "registry_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_entity_id: Mapped[int] = mapped_column(ForeignKey("legal_entities.id"))
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(160), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    legal_entity: Mapped[LegalEntity] = relationship(back_populates="registry_events")


class OwnershipSnapshot(Base):
    """Состав участников общества на конкретную дату.

    API-ФНС возвращает действующих участников в методе egr и исторические
    срезы в changes. Храним именно срезы, а не заранее придуманные события:
    так интерфейс может честно показать состояние «до» и «после», а алгоритм
    сравнения можно улучшать без повторной загрузки исходных данных.
    """
    __tablename__ = "ownership_snapshots"
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "snapshot_date", "source_kind", name="uq_ownership_snapshot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_entity_id: Mapped[int] = mapped_column(ForeignKey("legal_entities.id"))
    snapshot_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_kind: Mapped[str] = mapped_column(String(30), default="changes")  # current | changes
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    legal_entity: Mapped[LegalEntity] = relationship(back_populates="ownership_snapshots")
    stakes: Mapped[list["OwnershipStake"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class OwnershipStake(Base):
    """Один участник в одном историческом срезе состава участников."""
    __tablename__ = "ownership_stakes"
    __table_args__ = (UniqueConstraint("snapshot_id", "owner_key", name="uq_snapshot_owner"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("ownership_snapshots.id"))
    owner_key: Mapped[str] = mapped_column(String(520))
    owner_name: Mapped[str] = mapped_column(String(500))
    owner_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    country: Mapped[str | None] = mapped_column(String(160), nullable=True)
    share_percent: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    nominal_value_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot: Mapped[OwnershipSnapshot] = relationship(back_populates="stakes")


class FnsSyncRun(Base):
    __tablename__ = "fns_sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str] = mapped_column(String(30), default="sync")
    companies_total: Mapped[int] = mapped_column(default=0)
    matched: Mapped[int] = mapped_column(default=0)
    candidates: Mapped[int] = mapped_column(default=0)
    errors: Mapped[int] = mapped_column(default=0)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)


# ------------------------------------------------------------ консультанты ---

class AdvisorKind(str, enum.Enum):
    legal = "legal"
    investment = "investment"


class Advisor(Base):
    __tablename__ = "advisors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    kind: Mapped[AdvisorKind] = mapped_column(Enum(AdvisorKind), default=AdvisorKind.legal)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    aliases: Mapped[list["AdvisorAlias"]] = relationship(back_populates="advisor", cascade="all, delete-orphan")


class AdvisorAlias(Base):
    __tablename__ = "advisor_aliases"
    __table_args__ = (UniqueConstraint("alias", name="uq_advisor_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    advisor_id: Mapped[int] = mapped_column(ForeignKey("advisors.id"))
    alias: Mapped[str] = mapped_column(String(300))

    advisor: Mapped[Advisor] = relationship(back_populates="aliases")


# ---------------------------------------------------------------- аккаунты ---

class UserRole(str, enum.Enum):
    individual = "individual"
    corporate = "corporate"
    firm = "firm"  # юрфирма/консультант с верифицированным профилем


class UserTier(str, enum.Enum):
    free = "free"
    paid = "paid"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(300), unique=True)
    # Пусто у аккаунтов старой схемы (вход по ссылке, до 2 августа 2026) —
    # таких в базе не было ни одного на момент перехода, но поле nullable
    # на случай, если где-то в проде такая запись всё же появилась: у неё
    # просто не будет пароля, и войти можно только новой регистрацией.
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.individual)
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier), default=UserTier.free)
    firm_id: Mapped[int | None] = mapped_column(ForeignKey("advisors.id"), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # бейдж «подтверждено фирмой»
    # Добавлены 2 августа вместе с выбором типа аккаунта при регистрации —
    # до этого регистрация жёстко писала role=individual всем подряд, и
    # профиль показывал сырое значение поля без перевода на русский.
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    position: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Вход по заявке (2 сентября 2026, этап закрытого тестирования, см.
    # ACCESS_GATE в main.py): при включённом гейте регистрация создаёт
    # аккаунт с approved=False, и войти он не может, пока владелец или
    # партнёр не нажмёт «Одобрить» в Telegram-консоли. По умолчанию True —
    # аккаунты, заведённые до гейта (и при выключенном гейте), входят как
    # раньше; для уже существующей таблицы то же делает миграция в main.py.
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    saved_filters: Mapped[list["SavedFilter"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class SavedFilter(Base):
    """Подписка на алерт: «сообщи о сделках в отрасли X от суммы Y»."""
    __tablename__ = "saved_filters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    keyword: Mapped[str | None] = mapped_column(String(200), nullable=True)
    min_amount_mln_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User] = relationship(back_populates="saved_filters")


class AuthSession(Base):
    """Серверная сессия за обычной httponly-кукой — без стороннего сервиса
    аутентификации и без подписи токена сторонней библиотекой: opaque-токен
    проверяется прямым запросом к этой таблице."""
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Comment(Base):
    """Комментарий под сделкой. Виден сразу: писать может только вошедший по
    почте пользователь, и это уже даёт проверенный e-mail — планка выше, чем
    у анонимного интернета. Модерация (жалоба/скрытие) — следующий шаг, не
    блокирующий первую версию; поле status оставлено под неё заранее."""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(String(80))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="approved")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Карточки сделок пока канонически живут в JSON, поэтому внешний ключ на
    # SQL-таблицу deals здесь недопустим: в PostgreSQL комментарий к JSON-карточке
    # иначе отклоняется, даже если карточка существует в интерфейсе.
    user: Mapped[User] = relationship()


class CorrectionRequest(Base):
    """Сообщение редакции по карточке сделки или общее обращение.

    Это не публичный комментарий: сообщение видит только команда продукта.
    Вход не обязателен — иначе человек, который заметил ошибку, чаще закроет
    форму, чем станет заводить аккаунт. Для вошедшего пользователя сохраняем
    user_id и подставляем его почту; анонимный посетитель может оставить любой
    удобный контакт или отправить сообщение без контакта.
    """
    __tablename__ = "correction_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Строковый id без внешнего ключа: карточки пока живут прежде всего в JSON,
    # поэтому редакционная форма должна работать и до миграции конкретной
    # карточки в SQL-таблицу deals. None означает общее сообщение из футера.
    deal_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped[User | None] = relationship()


# --------------------------------------- уведомления / экспорт / ассистент ---

class DealSeen(Base):
    """Когда карточка впервые появилась НА САЙТЕ.

    Это не дата сделки и не дата статьи: карточка, добавленная сегодня, может
    описывать сделку 2022 года. Для рассылки по подпискам важно именно «когда
    она у нас появилась» — иначе подписавшийся сегодня получил бы всю историю
    рынка одним залпом.

    Запись живёт в базе, а не в файле рядом с кодом: файл на Timeweb
    переписывается при каждом деплое, и состояние «о чём уже сообщали»
    обнулялось бы — читатель получал бы одни и те же уведомления снова.
    """

    __tablename__ = "deals_seen"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(String(80), unique=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DealWatch(Base):
    __tablename__ = "deal_watches"
    __table_args__ = (UniqueConstraint("user_id", "deal_id", name="uq_user_deal_watch"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    deal_id: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telegram_connect_token: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(40), default="deal_update")
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(String(600), nullable=True)
    deal_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    telegram_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AssistantThread(Base):
    __tablename__ = "assistant_threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    context_type: Mapped[str] = mapped_column(String(30), default="general")
    context_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("assistant_threads.id"))
    role: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(20), default="base")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    thread: Mapped[AssistantThread] = relationship(back_populates="messages")


class AssistantFeedback(Base):
    """«Полезно / не помогло» под ответом ассистента — начало петли улучшения,
    о которой договорились с владельцем 31 августа 2026: плохой ответ раньше
    просто пропадал, никто о нём не узнавал. Храним вопрос и ответ целиком:
    через неделю их уже не восстановить из диалога анонимного посетителя."""
    __tablename__ = "assistant_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    thread_id: Mapped[int | None] = mapped_column(ForeignKey("assistant_threads.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(10))          # up | down
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default="base")
    intent: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Webinar(Base):
    __tablename__ = "webinars"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    speaker: Mapped[str | None] = mapped_column(String(300), nullable=True)
    registration_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ------------------------------------------------------------------ сделки ---

class AmountConfidence(str, enum.Enum):
    disclosed = "disclosed"      # официально раскрыта сторонами/консультантами
    estimated = "estimated"      # оценка СМИ/аналитиков, не подтверждена сторонами
    undisclosed = "undisclosed"  # суммы нет вообще


class EnrichmentTier(str, enum.Enum):
    full = "full"   # собрана из нескольких источников, есть эко/юр-разбор
    stub = "stub"   # одна запись с одним источником, до обогащения руки не дошли


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    date_raw: Mapped[str | None] = mapped_column(String(20), nullable=True)  # как в источнике, вкл. "unknown"
    date_value: Mapped[date | None] = mapped_column(Date, nullable=True)     # то же самое, распарсенное — для сортировки/фильтра
    title: Mapped[str] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    deal_type: Mapped[str | None] = mapped_column(String(200), nullable=True)  # исходный текст типа сделки
    kind: Mapped[str | None] = mapped_column(String(30), nullable=True)  # acquisition/jv/financing/credit/structured/ipo
    status: Mapped[str | None] = mapped_column(String(60), nullable=True)

    buyer_company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    target_company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), nullable=True)

    amount_raw: Mapped[str | None] = mapped_column(String(300), nullable=True)  # исходная строка — всегда сохраняем текст
    amount_value_mln_rub: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    amount_confidence: Mapped[AmountConfidence] = mapped_column(Enum(AmountConfidence), default=AmountConfidence.undisclosed)

    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)   # eco.rationale
    context: Mapped[str | None] = mapped_column(Text, nullable=True)     # eco.context
    structure: Mapped[str | None] = mapped_column(Text, nullable=True)   # law.struct
    approvals: Mapped[str | None] = mapped_column(Text, nullable=True)   # law.appr
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)       # law.terms

    enrichment_tier: Mapped[EnrichmentTier] = mapped_column(Enum(EnrichmentTier), default=EnrichmentTier.stub)
    verified_by_firm_id: Mapped[int | None] = mapped_column(ForeignKey("advisors.id"), nullable=True)  # Шаг 2, пока пусто
    source_batch: Mapped[str | None] = mapped_column(String(60), nullable=True)  # какой файл/прогон породил запись — для отладки миграции
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    advisors: Mapped[list["DealAdvisor"]] = relationship(back_populates="deal", cascade="all, delete-orphan")
    sources: Mapped[list["DealSource"]] = relationship(back_populates="deal", cascade="all, delete-orphan")


class DealAdvisor(Base):
    """Консультант на сделке. advisor_id может быть пустым, если имя из
    текста не удалось надёжно сопоставить ни с одной сущностью в Advisor —
    тогда raw_name остаётся единственным источником правды, ничего не теряем."""
    __tablename__ = "deal_advisors"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"))
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("advisors.id"), nullable=True)
    raw_name: Mapped[str] = mapped_column(String(300))
    side: Mapped[str | None] = mapped_column(String(120), nullable=True)  # "за покупателя" и т.п.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="advisors")
    advisor: Mapped[Advisor | None] = relationship()


class DealSource(Base):
    __tablename__ = "deal_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"))
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(600))

    deal: Mapped[Deal] = relationship(back_populates="sources")


class AppSetting(Base):
    """Мелкая настройка, которую сайт УЗНАЁТ САМ и которая нужна рутине.

    Сегодня в ней ровно одно значение — числовой адрес телеграм-канала.
    4 сентября 2026 канал сделали приватным, и старое @имя перестало
    существовать для всех, кроме самого Telegram: постить можно только по
    числовому id, а услышать его больше неоткуда. Telegram называет его в
    посте канала — то есть узнаёт САЙТ (у него вебхук), а нужен он РУТИНЕ
    публикации, у которой доступа к этой базе нет. Тот же мост, что и у
    решений модерации: сайт пишет сюда, рутина читает по токену.

    Почему не переменная окружения и не константа в коде: репозиторий
    публичный, а адрес закрытого канала в нём публиковать незачем; в
    окружении же значение живёт до первой правки переменных (публикация уже
    молчала трое суток, когда оно оттуда пропало) и не доезжает до давно
    работающих сессий рутин.
    """
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ModerationDecision(Base):
    """Решение владельца/партнёра по черновику карточки, пришедшее из Telegram.

    Зачем таблица, а не файл: решение принимает человек в Telegram, вебхук
    приходит на САЙТ, а применяет решение рутина публикации в одноразовом
    контейнере, у которого нет доступа к базе сайта напрямую (она в приватной
    сети хостинга). Таблица + API `/api/moderation/decisions` — единственный
    мост между ними: сайт пишет сюда, рутина читает по публичному адресу.
    """
    __tablename__ = "moderation_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 80, не 40: у вехи deal_id несёт "<id сделки>~<вид этапа>" (раздел A,
    # 22 августа), длиннее одного голого id сделки.
    deal_id: Mapped[str] = mapped_column(String(80), index=True)
    verdict: Mapped[str] = mapped_column(String(16))          # approve | hold
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str] = mapped_column(String(80))       # chat_id решившего
    consumed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    # Добавлены 22 августа для заметок (verdict='note'): рутина обязана
    # ОТВЕТИТЬ реплаем на то же сообщение, где владелец оставил заметку —
    # для этого нужны chat_id группы/чата и id самого сообщения-заметки
    # (Telegram API: sendMessage(..., reply_to_message_id=reply_message_id)).
    # Для остальных вердиктов (approve/hold/…) оба поля остаются NULL — их
    # решения уже подтверждаются прямо в сообщении с кнопками (_mark_decided).
    chat_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reply_message_id: Mapped[int | None] = mapped_column(nullable=True)
