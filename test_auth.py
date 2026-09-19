# -*- coding: utf-8 -*-
"""Вход по email и паролю: весь цикл на sqlite in-memory, без сети.

Запуск: python3 -m pytest test_auth.py -q
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
from db.models import AuthSession, Base, User


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_password_hash_round_trip():
    h = auth.hash_password("верный-конь-скрепка")
    assert auth.verify_password("верный-конь-скрепка", h)
    assert not auth.verify_password("другой-пароль", h)


def test_password_hash_is_salted():
    """Один и тот же пароль дважды — разные хэши: соль своя на каждый вызов."""
    assert auth.hash_password("одинаковый") != auth.hash_password("одинаковый")


def test_verify_password_rejects_malformed_hash():
    assert not auth.verify_password("что угодно", "не-похоже-на-хэш")
    assert not auth.verify_password("что угодно", None)


def test_register_creates_user_with_lowercase_email(session):
    user, err = auth.register_user(session, "Юрист@Фирма.ру", "надёжный-пароль", "Юрист Юристов")
    assert err is None and user is not None
    assert user.email == "юрист@фирма.ру"
    assert session.query(User).count() == 1


def test_register_rejects_bad_email(session):
    user, err = auth.register_user(session, "not-an-email", "надёжный-пароль", "Тест Тестов")
    assert user is None and "почта" in err


def test_register_rejects_short_password(session):
    user, err = auth.register_user(session, "a@b.ru", "коротк", "Тест Тестов")
    assert user is None and "пароль" in err


def test_register_rejects_duplicate_email(session):
    auth.register_user(session, "a@b.ru", "первый-пароль-123", "Тест Тестов")
    user, err = auth.register_user(session, "a@b.ru", "второй-пароль-456", "Тест Тестов")
    assert user is None and "уже зарегистрирована" in err


def test_register_rejects_missing_full_name(session):
    """До 2 августа роль записывалась всем подряд как individual без выбора —
    теперь ФИО и тип аккаунта обязательны, а не тихая заглушка."""
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "")
    assert user is None and "имя" in err


def test_register_rejects_unknown_role(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Тест Тестов", role="начальник")
    assert user is None and "тип аккаунта" in err


def test_register_stores_full_name_company_position_and_role(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Иван Иванов",
                                    company="ООО Ромашка", position="Партнёр", role="firm")
    assert err is None
    assert user.full_name == "Иван Иванов"
    assert user.company == "ООО Ромашка"
    assert user.position == "Партнёр"
    assert user.role.value == "firm"


def test_register_defaults_role_to_individual_and_allows_empty_company(session):
    user, err = auth.register_user(session, "a@b.ru", "надёжный-пароль", "Иван Иванов")
    assert err is None
    assert user.role.value == "individual"
    assert user.company is None and user.position is None


def test_authenticate_accepts_correct_password(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "a@b.ru", "правильный-пароль")
    assert err is None and user is not None and user.email == "a@b.ru"


def test_authenticate_is_case_insensitive_on_email(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "A@B.RU", "правильный-пароль")
    assert err is None and user is not None


def test_authenticate_rejects_wrong_password(session):
    auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    user, err = auth.authenticate(session, "a@b.ru", "неверный-пароль")
    assert user is None and err is not None


def test_authenticate_unknown_email_gives_same_error_as_wrong_password(session):
    """Один и тот же отказ на обе причины — иначе по разнице ответов можно
    перечислять зарегистрированные адреса."""
    auth.register_user(session, "known@firm.ru", "правильный-пароль", "Тест Тестов")
    _, err_unknown = auth.authenticate(session, "unknown@firm.ru", "что-угодно")
    _, err_wrong = auth.authenticate(session, "known@firm.ru", "неверный-пароль")
    assert err_unknown == err_wrong


def test_session_cookie_round_trip(session):
    user, err = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    assert err is None
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie).id == user.id
    assert auth.current_user(session, "не-та-кука") is None
    assert auth.current_user(session, None) is None


def test_revoked_session_stops_working(session):
    user, _ = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    cookie = auth.create_session(session, user)
    assert auth.current_user(session, cookie) is not None
    auth.revoke_session(session, cookie)
    assert auth.current_user(session, cookie) is None


def test_expired_session_stops_working(session):
    user, _ = auth.register_user(session, "a@b.ru", "правильный-пароль", "Тест Тестов")
    session.add(AuthSession(user_id=user.id, token="stale-session",
                             expires_at=datetime.utcnow() - timedelta(days=1)))
    session.commit()
    assert auth.current_user(session, "stale-session") is None


@pytest.mark.parametrize("bad", ["", "not-an-email", "a@b", "a b@c.ru", "a" * 301])
def test_invalid_emails_are_rejected(bad):
    assert not auth.valid_email(bad)


@pytest.mark.parametrize("ok", ["a@b.ru", "Юрист.Консультант@firma.legal"])
def test_valid_emails_pass(ok):
    assert auth.valid_email(ok)


@pytest.mark.parametrize("bad", ["", "коротк", "1234567"])
def test_invalid_passwords_are_rejected(bad):
    assert not auth.valid_password(bad)


def test_valid_password_passes():
    assert auth.valid_password("восемь-символов-и-больше")


# ==================== Вход по заявке (ACCESS_GATE) ====================

def test_register_user_can_be_created_as_a_pending_request(session):
    """При включённом гейте регистрация — заявка: аккаунт есть, approved=False.
    По умолчанию (и при выключенном гейте) аккаунт одобрен сразу — так же
    ведут себя все аккаунты, заведённые до появления гейта."""
    pending, err = auth.register_user(session, "заявка@firm.ru", "надёжный-пароль", "Иван Иванов", approved=False)
    assert err is None and pending.approved is False
    plain, err = auth.register_user(session, "обычный@firm.ru", "надёжный-пароль", "Пётр Петров")
    assert err is None and plain.approved is True


def test_pending_request_is_not_a_duplicate_and_password_still_checks(session):
    """Повторная заявка тем же адресом — тот же отказ «уже зарегистрирована»
    (дубля нет), а authenticate() по-прежнему отвечает за пароль, не за
    одобрение: решение «пускать или нет» принимает эндпоинт входа."""
    auth.register_user(session, "заявка@firm.ru", "надёжный-пароль", "Иван Иванов", approved=False)
    again, err = auth.register_user(session, "заявка@firm.ru", "другой-пароль-1", "Иван Иванов", approved=False)
    assert again is None and "уже зарегистрирована" in err
    assert session.query(User).filter_by(email="заявка@firm.ru").count() == 1
    user, err = auth.authenticate(session, "заявка@firm.ru", "надёжный-пароль")
    assert err is None and user.approved is False


# ============ СМЕНА ПАРОЛЯ И ПОЧТЫ (19 сентября 2026) ============
# Артём: «Нужна возможность менять пароль». Ксюша: «И в идеале почту».
# До этого дня на вкладке «Аккаунт» не было ни того, ни другого.

def _user(session, email="kseniya@example.com", password="исходный-пароль-1"):
    user, err = auth.register_user(session, email, password, "Ксения Збышевская")
    assert err is None, err
    return user


def test_password_changes_and_the_old_one_stops_working(session):
    user = _user(session)
    ok, err = auth.change_password(session, user, "исходный-пароль-1", "новый-пароль-2")
    assert (ok, err) == (True, None)
    assert auth.authenticate(session, user.email, "новый-пароль-2")[0] is user
    assert auth.authenticate(session, user.email, "исходный-пароль-1")[0] is None


def test_password_change_requires_the_current_one(session):
    """Сессия живёт 30 дней. Без этой проверки чужой человек за
    незаблокированным компьютером забрал бы аккаунт, не зная старого пароля."""
    user = _user(session)
    ok, err = auth.change_password(session, user, "не-тот-пароль", "новый-пароль-2")
    assert ok is False and err == "неверный текущий пароль"
    assert auth.authenticate(session, user.email, "исходный-пароль-1")[0] is user


def test_password_change_closes_every_other_login(session):
    """Пароль меняют в том числе потому, что его кто-то узнал. Оставить чужую
    сессию живой — сделать половину работы."""
    user = _user(session)
    phone = auth.create_session(session, user)
    laptop = auth.create_session(session, user)
    assert auth.current_user(session, phone) is user
    auth.change_password(session, user, "исходный-пароль-1", "новый-пароль-2")
    assert auth.current_user(session, phone) is None
    assert auth.current_user(session, laptop) is None


def test_new_password_must_be_long_enough_and_actually_new(session):
    user = _user(session)
    assert auth.change_password(session, user, "исходный-пароль-1", "корот")[1] \
        == "новый пароль — от 8 символов"
    assert auth.change_password(session, user, "исходный-пароль-1", "исходный-пароль-1")[1] \
        == "новый пароль совпадает с текущим"


def test_email_changes_and_becomes_the_new_login(session):
    user = _user(session)
    ok, err = auth.change_email(session, user, "исходный-пароль-1", "  Novaya@Example.COM ")
    assert (ok, err) == (True, None)
    # Адрес приводится к нижнему регистру и без пробелов — как при регистрации.
    assert user.email == "novaya@example.com"
    assert auth.authenticate(session, "novaya@example.com", "исходный-пароль-1")[0] is user
    assert auth.authenticate(session, "kseniya@example.com", "исходный-пароль-1")[0] is None


def test_email_change_is_confirmed_by_password(session):
    user = _user(session)
    ok, err = auth.change_email(session, user, "не-тот-пароль", "novaya@example.com")
    assert ok is False and err == "неверный пароль"
    assert user.email == "kseniya@example.com"


def test_email_cannot_be_taken_from_another_account(session):
    """Иначе двое оказались бы с одним логином, и второй потерял бы вход."""
    _user(session, "zanyato@example.com")
    user = _user(session)
    ok, err = auth.change_email(session, user, "исходный-пароль-1", "zanyato@example.com")
    assert ok is False and err == "эта почта уже зарегистрирована"


def test_email_change_rejects_nonsense_and_the_same_address(session):
    user = _user(session)
    assert auth.change_email(session, user, "исходный-пароль-1", "без-собаки")[1] == "некорректная почта"
    assert auth.change_email(session, user, "исходный-пароль-1", "KSENIYA@example.com")[1] \
        == "это та же почта, что и сейчас"


def test_email_change_keeps_you_logged_in(session):
    """Почта меняется, сессия остаётся: вход опознаётся по токену, а не по
    адресу, и выкидывать человека из браузера не за что."""
    user = _user(session)
    token = auth.create_session(session, user)
    auth.change_email(session, user, "исходный-пароль-1", "novaya@example.com")
    assert auth.current_user(session, token) is user
