import asyncio
import logging
import sqlite3
from contextlib import closing

import sys
import subprocess

try:
    import aiogram
except ImportError:
    print("Библиотека aiogram не найдена. Пытаюсь установить...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram>=3.0.0"])

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8706332262:AAHiMu_NJ2Ta-qkW9RgFSYfIHBqi5s_tBq0"  # Вставьте сюда токен вашего бота
ADMIN_IDS = [7284857745]  # Вставьте сюда ваш Telegram ID
DB_NAME = "shop.db"

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- ТЕКСТЫ И ПЕРЕВОДЫ (МУЛЬТИЯЗЫЧНОСТЬ) ---
texts = {
    'choose_lang': "👋 <b>Добро пожаловать в 𝚂𝚃𝚁𝙰𝙽𝙸𝙺 𝚂𝙷𝙾𝙿 💎</b>\n\n🇷🇺 Выберите язык:\n🇹🇯 Забони худро интихоб кунед:\n\n👨‍💻 <b>Admins:</b> {}",
    'welcome': {
        'ru': "👋 <b>Добро пожаловать в 𝚂𝚃𝚁𝙰𝙽𝙸𝙺 𝚂𝙷𝙾𝙿 💎</b>\n\n✨ <i>Лучшие цены и быстрая доставка!</i>\n👇 <b>Выберите действие в меню:</b>",
        'tj': "👋 <b>Хуш омадед ба 𝚂𝚃𝚁𝙰𝙽𝙸𝙺 𝚂𝙷𝙾𝙿 💎</b>\n\n✨ <i>Нархҳои беҳтарин ва расонидани зуд!</i>\n👇 <b>Дар меню амалро интихоб кунед:</b>",
    },
    'main_menu': {
        'shop': {'ru': "🛍️ Магазин", 'tj': "🛍️ Мағоза"},
        'price': {'ru': "📄 Прайс-лист", 'tj': "📄 Нархнома"},
        'reviews': {'ru': "⭐️ Отзывы", 'tj': "⭐️ Отзывҳо"},
        'support': {'ru': "👨‍💻 Поддержка", 'tj': "👨‍💻 Дастгирӣ"},
        'faq': {'ru': "❓ FAQ / Инфо", 'tj': "❓ FAQ / Маълумот"},
        'change_lang': {'ru': "🌐 Язык / Забон", 'tj': "🌐 Язык / Забон"},
    },
    'shop_title': {'ru': "🛒 <b>Магазин</b>\n\n👇 <i>Выберите товар из списка:</i>", 'tj': "🛒 <b>Мағоза</b>\n\n👇 <i>Маҳсулотро аз рӯйхат интихоб кунед:</i>"},
    'price_title': {'ru': "📄 <b>Прайс-лист</b>", 'tj': "📄 <b>Нархнома</b>"},
    'admins_info': {
        'ru': "👨‍💻 <b>Техническая поддержка</b>\n\n📞 <i>По всем вопросам обращайтесь:</i>\n{}",
        'tj': "👨‍💻 <b>Дастгирии техникӣ</b>\n\n📞 <i>Барои ҳамаи саволҳо муроҷиат кунед:</i>\n{}",
    },
    'reviews_info': {
        'ru': "⭐️ <b>Отзывы</b>\n\n✍️ <i>Здесь вы можете оставить свой отзыв. После проверки он появится в канале.</i>",
        'tj': "⭐️ <b>Отзывҳо</b>\n\n✍️ <i>Дар ин ҷо шумо метавонед фикри худро нависед. Пас аз санҷиш он дар канал пайдо мешавад.</i>",
    },
    'faq_info': {
        'ru': "❓ <b>Частые вопросы</b>\n\n1️⃣ Выберите товар.\n2️⃣ Введите <b>Game ID</b>.\n3️⃣ Оплатите по реквизитам.\n4️⃣ Отправьте чек боту.\n5️⃣ Ждите зачисления! 🚀",
        'tj': "❓ <b>Саволҳои маъмул</b>\n\n1️⃣ Маҳсулотро интихоб кунед.\n2️⃣ <b>Game ID</b>-ро нависед.\n3️⃣ Бо реквизитҳо пардохт кунед.\n4️⃣ Чекро ба бот фиристед.\n5️⃣ Интизор шавед! 🚀",
    },
    'enter_game_id': {
        'ru': "🆔 <b>Введите ваш Game ID:</b>\n\n<i>Например:</i> <code>1234567890</code>",
        'tj': "🆔 <b>ID-и бозигарии худро ворид кунед:</b>\n\n<i>Масалан:</i> <code>1234567890</code>",
    },
    'payment_info': {
        'ru': " <b>Оформление заказа</b>\n\n💎 <b>Товар:</b> {}\n💰 <b>К оплате:</b> <code>{} {}</code>\n🆔 <b>Game ID:</b> <code>{}</code>\n\n📋 <b>Реквизиты для оплаты:</b>\n<code>{}</code>\n\n📸 <b>Нажмите кнопку ниже, чтобы отправить чек</b> 👇",
        'tj': "💳 <b>Барасмиятдарории фармоиш</b>\n\n💎 <b>Маҳсулот:</b> {}\n💰 <b>Маблағ:</b> <code>{} {}</code>\n🆔 <b>Game ID:</b> <code>{}</code>\n\n📋 <b>Реквизитҳо барои пардохт:</b>\n<code>{}</code>\n\n📸 <b>Барои фиристодани чек тугмаи поёнро пахш кунед</b> 👇",
    },
    'send_receipt_btn': {'ru': "📤 Отправить чек", 'tj': "📤 Фиристодани чек"},
    'send_receipt_request': {
        'ru': "📸 <b>Отправьте скриншот или фото чека:</b>",
        'tj': "📸 <b>Скриншот ё акси чекро фиристед:</b>"
    },
    'receipt_received_ask_confirm': {
        'ru': "✅ <b>Чек получен!</b>\n\nНажмите <b>«Я оплатил»</b> для завершения.",
        'tj': "✅ <b>Чек қабул шуд!</b>\n\nБарои анҷом тугмаи <b>«Ман пардохт кардам»</b>-ро пахш кунед."
    },
    'i_paid_btn': {'ru': "✅ Я оплатил", 'tj': "✅ Ман пардохт кардам"},
    'payment_success_final': {
        'ru': "🛍️ <b>Ваш заказ принят!</b>\n\n⏳ Ожидайте выполнения.\n🔔 <i>Вам придет уведомление, когда товар будет отправлен.</i>",
        'tj': "🛍️ <b>Дархости шумо қабул шуд!</b>\n\n⏳ Интизор шавед.\n🔔 <i>Вақте ки маҳсулот фиристода мешавад, ба шумо хабар меояд.</i>"
    },
    'waiting_for_receipt_error': {
        'ru': "⚠️ <b>Ошибка!</b> Отправьте изображение (скриншот/фото).",
        'tj': "⚠️ <b>Хатогӣ!</b> Тасвир (скриншот/акс) фиристед."
    },
    'admin_notification': {
        'ru': "🔔 <b>Новый заказ!</b>\n\n👤 <b>User:</b> @{}\n🆔 <b>User ID:</b> <code>{}</code>\n💎 <b>Товар:</b> {}\n🎮 <b>Game ID:</b> <code>{}</code>",
        'tj': "🔔 <b>Фармоиши нав!</b>\n\n👤 <b>User:</b> @{}\n🆔 <b>User ID:</b> <code>{}</code>\n💎 <b>Маҳсулот:</b> {}\n🎮 <b>Game ID:</b> <code>{}</code>",
    },
    'order_confirmed': {
        'ru': "✅ <b>Ваш заказ выполнен!</b> Спасибо за покупку.",
        'tj': "✅ <b>Фармоиши шумо иҷро шуд!</b> Ташаккур барои харид.",
    },
    'order_declined': {
        'ru': "❌ <b>Заказ отклонен.</b>",
        'tj': "❌ <b>Фармоиш рад карда шуд.</b>",
    },
    'admin_panel_title': {'ru': "🛠 <b>Панель администратора</b>", 'tj': "🛠 <b>Панели администратор</b>"},
    'admin_panel': {
        'change_prices': {'ru': "Изменить цены", 'tj': "Тағйир додани нархҳо"},
        'change_payment': {'ru': "Изменить реквизиты", 'tj': "Тағйир додани реквизитҳо"},
        'change_admins': {'ru': "Изменить админов (поддержка)", 'tj': "Тағйир додани администраторҳо (дастгирӣ)"},
        'change_welcome_admin': {'ru': "Изменить админа (приветствие)", 'tj': "Тағйир додани администратор (салом)"},
        'broadcast': {'ru': "Рассылка", 'tj': "Пахши паём"},
        'manage_products': {'ru': "🛍️ Управление товарами", 'tj': "🛍️ Идораи маҳсулот"},

    },
    'back': {'ru': "⬅️ Назад", 'tj': "⬅️ Бозгашт"},
    'confirm': {'ru': "✅ Подтвердить", 'tj': "✅ Тасдиқ кардан"},
    'decline': {'ru': "❌ Отклонить", 'tj': "❌ Рад кардан"},
    'enter_new_admins': {
        'ru': "Введите новые контакты администраторов через пробел (например, @admin1 @admin2):",
        'tj': "Алоқаҳои нави администраторҳоро бо фосила ворид кунед (масалан, @admin1 @admin2):"
    },
    'admins_updated': {
        'ru': "Контакты администраторов успешно обновлены!",
        'tj': "Алоқаҳои администраторҳо бомуваффақият нав карда шуданд!"
    },
    'enter_new_welcome_admin': {
        'ru': "Введите новый контакт админа для приветственного сообщения (например, @admin):",
        'tj': "Алоқаи нави администраторро барои паёми салом ворид кунед (масалан, @admin):"
    },
    'welcome_admin_updated': {
        'ru': "Контакт админа в приветствии успешно обновлен!",
        'tj': "Алоқаи администратор дар салом бомуваффақият нав карда шуд!"
    },
    'enter_review': {
        'ru': "Напишите ваш отзыв. Он будет отправлен на модерацию администраторам.",
        'tj': "Отзыви худро нависед. Он барои модератсия ба администраторҳо фиристода мешавад."
    },
    'confirm_send_review': {
        'ru': "Ваш отзыв:\n\n<i>{}</i>\n\nОтправить его на модерацию?",
        'tj': "Отзыви шумо:\n\n<i>{}</i>\n\nОнро барои модератсия мефиристед?"
    },
    'send_review_btn': {'ru': "✅ Отправить", 'tj': "✅ Фиристодан"},
    'cancel_review_btn': {'ru': "❌ Отменить", 'tj': "❌ Бекор кардан"},
    'review_sent_for_moderation': {
        'ru': "Спасибо за ваш отзыв! Он отправлен на модерацию и будет опубликован в канале в течение 1-2 часов.",
        'tj': "Ташаккур барои отзыви шумо! Он барои модератсия фиристода шуд ва дар давоми 1-2 соат дар канал нашр мешавад."
    },
    'review_canceled': {'ru': "Отправка отзыва отменена.", 'tj': "Фиристодани отзыв бекор карда шуд."},
    'admin_new_review_notification': {
        'ru': "🔔 <b>Новый отзыв от пользователя!</b>\n\n<b>Пользователь:</b> @{}\n<b>ID пользователя:</b> <code>{}</code>\n<b>Отзыв:</b>\n<i>{}</i>",
        'tj': "🔔 <b>Отзыви нав аз корбар!</b>\n\n<b>Истифодабаранда:</b> @{}\n<b>ID-и истифодабаранда:</b> <code>{}</code>\n<b>Отзыв:</b>\n<i>{}</i>"
    },
    'review_published_channel_msg': {'ru': "⭐️ Новый отзыв от пользователя @{}!\n\n<i>{}</i>", 'tj': "⭐️ Отзыви нав аз корбар @{}!\n\n<i>{}</i>"},
    'review_approved_user': {'ru': "✅ Ваш отзыв был одобрен и опубликован в нашем канале!", 'tj': "✅ Отзыви шумо тасдиқ ва дар канали мо нашр шуд!"},
    'review_declined_user': {'ru': "❌ Ваш отзыв был отклонен администратором.", 'tj': "❌ Отзыви шумо аз ҷониби администратор рад карда шуд."},
}
texts['admin_manage_products'] = {
    'title': {'ru': "Управление товарами", 'tj': "Идораи маҳсулот"},
    'add': {'ru': "➕ Добавить товар", 'tj': "➕ Илова кардани маҳсулот"},
    'delete': {'ru': "➖ Удалить товар", 'tj': "➖ Нест кардани маҳсулот"},
    'enter_name_ru': {'ru': "Введите название товара на русском:", 'tj': "Номи маҳсулотро бо забони русӣ ворид кунед:"},
    'enter_name_tj': {'ru': "Введите название товара на таджикском:", 'tj': "Номи маҳсулотро бо забони тоҷикӣ ворид кунед:"},
    'enter_price': {'ru': "Введите цену товара (число, например 150.5):", 'tj': "Нархи маҳсулотро ворид кунед (рақами, масалан 150.5):"},
    'product_added': {'ru': "✅ Товар '{}' успешно добавлен!", 'tj': "✅ Маҳсулоти '{}' бомуваффақият илова карда шуд!"},
    'choose_product_to_delete': {'ru': "Выберите товар для удаления:", 'tj': "Маҳсулотро барои нест кардан интихоб кунед:"},
    'confirm_delete': {'ru': "Вы уверены, что хотите удалить товар '{}'?", 'tj': "Оё шумо мутмаин ҳастед, ки мехоҳед маҳсулоти '{}'-ро нест кунед?"},
    'product_deleted': {'ru': "✅ Товар '{}' успешно удален.", 'tj': "✅ Маҳсулоти '{}' бомуваффақият нест карда шуд."},
    'delete_cancelled': {'ru': "Удаление отменено.", 'tj': "Несткунӣ бекор карда шуд."},
    'yes': {'ru': "Да", 'tj': "Ҳа"},
    'no': {'ru': "Нет", 'tj': "Не"},
}


# --- БАЗА ДАННЫХ (SQLITE) ---
def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'ru'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ru TEXT NOT NULL,
                    name_tj TEXT NOT NULL,
                    price REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    review_text TEXT NOT NULL
                )
            """)
            # Добавляем товары и настройки по умолчанию, если их нет
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                default_products = [
                    ('💎 100+5 Алмазов', '💎 100+5 Алмос', 10.0),
                    ('💎 310+16 Алмазов', '💎 310+16 Алмос', 26.0),
                    ('💎 520+26 Алмазов', '💎 520+26 Алмос', 48.0),
                    ('💎 1060+53 Алмазов', '💎 1060+53 Алмос', 95.0),
                    ('💎 2180+109 Алмазов', '💎 2180+109 Алмос', 190.0),
                    ('🎫 Ваучер на месяц (450)', '🎫 Ваучери моҳона (450)', 16.0),
                    ('🎫 Ваучер на месяц (2600)', '🎫 Ваучери моҳона (2600)', 95.0),
                    ('🎁 EVO пропуск (3 дня)', '🎁 EVO пропуск (3 рӯз)', 10.0),
                    ('🎁 EVO пропуск (7 дней)', '🎁 EVO пропуск (7 рӯз)', 14.0),
                    ('🎁 EVO пропуск (30 дней)', '🎁 EVO пропуск (30 рӯз)', 35.0),
                    ('📌 Пропуск прокачки', '📌 Пропуск прокачки', 40.0),
                ]
                cursor.executemany("INSERT INTO products (name_ru, name_tj, price) VALUES (?, ?, ?)", default_products)

            cursor.execute("SELECT value FROM settings WHERE key = 'payment_details'")
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('payment_details', 'Номер_телефона/карты'))

            cursor.execute("SELECT value FROM settings WHERE key = 'admin_contacts'")
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('admin_contacts', '@support_admin1 @support_admin2'))

            cursor.execute("SELECT value FROM settings WHERE key = 'welcome_admin_contact'")
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('welcome_admin_contact', '@main_admin'))
            
            cursor.execute("SELECT value FROM settings WHERE key = 'review_channel_id'")
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('review_channel_id', '@stranik_shop')) # Замените на ваш канал для отзывов

            conn.commit()

def db_execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()

def db_insert_get_id(query, params=()):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid


# --- FSM СОСТОЯНИЯ ---
class OrderState(StatesGroup):
    entering_game_id = State()
    waiting_for_receipt_intro = State()
    waiting_for_receipt = State()
    confirming_payment = State()

class AdminState(StatesGroup):
    changing_price_id = State()
    changing_price_value = State()
    changing_payment_details = State()
    changing_admin_contacts = State()
    changing_welcome_admin_contact = State()
    broadcasting = State()
    # Состояния для управления товарами
    adding_product_name_ru = State()
    adding_product_name_tj = State()
    adding_product_price = State()
    deleting_product_confirm = State()
    declining_order_reason = State()

class ReviewState(StatesGroup):
    waiting_for_text = State()
    confirming_send = State()

# --- КЛАВИАТУРЫ ---
def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"))
    builder.add(InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="set_lang_tj"))
    return builder.as_markup()

def get_main_menu_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['main_menu']['shop'][lang], callback_data="menu_shop"))
    builder.add(InlineKeyboardButton(text=texts['main_menu']['price'][lang], callback_data="menu_price"))
    builder.add(InlineKeyboardButton(text=texts['main_menu']['reviews'][lang], callback_data="menu_reviews"))
    builder.add(InlineKeyboardButton(text=texts['main_menu']['support'][lang], callback_data="menu_support"))
    builder.add(InlineKeyboardButton(text=texts['main_menu']['faq'][lang], callback_data="menu_faq"))
    builder.add(InlineKeyboardButton(text=texts['main_menu']['change_lang'][lang], callback_data="menu_change_lang"))
    builder.adjust(2)
    return builder.as_markup()

def get_shop_keyboard(lang: str):
    products = db_execute("SELECT id, name_ru, name_tj, price FROM products", fetchall=True)
    builder = InlineKeyboardBuilder()
    currency = "TJS" if lang == 'tj' else "RUB"
    for prod_id, name_ru, name_tj, price in products:
        name = name_tj if lang == 'tj' else name_ru
        builder.add(InlineKeyboardButton(text=f"{name} - {price} {currency}", callback_data=f"buy_{prod_id}"))
    builder.add(InlineKeyboardButton(text=texts['back'][lang], callback_data="back_to_main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_admin_order_keyboard(user_id: int, message_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['confirm']['ru'], callback_data=f"confirm_order_{user_id}_{message_id}"))
    builder.add(InlineKeyboardButton(text=texts['decline']['ru'], callback_data=f"decline_order_{user_id}_{message_id}"))
    return builder.as_markup()

def get_confirm_review_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['send_review_btn'][lang], callback_data="confirm_send_review"))
    builder.add(InlineKeyboardButton(text=texts['cancel_review_btn'][lang], callback_data="cancel_send_review"))
    return builder.as_markup()

def get_admin_panel_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['change_prices'][lang], callback_data="admin_change_prices"))
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['change_payment'][lang], callback_data="admin_change_payment"))
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['change_admins'][lang], callback_data="admin_change_admins"))
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['change_welcome_admin'][lang], callback_data="admin_change_welcome_admin"))
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['manage_products'][lang], callback_data="admin_manage_products"))
    builder.add(InlineKeyboardButton(text=texts['admin_panel']['broadcast'][lang], callback_data="admin_broadcast"))
    builder.adjust(1)
    return builder.as_markup()

def get_manage_products_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['admin_manage_products']['add'][lang], callback_data="admin_add_product"))
    builder.add(InlineKeyboardButton(text=texts['admin_manage_products']['delete'][lang], callback_data="admin_delete_product"))
    builder.add(InlineKeyboardButton(text=texts['back'][lang], callback_data="admin_panel_main"))
    builder.adjust(1)
    return builder.as_markup()

def get_delete_product_keyboard(lang: str):
    products = db_execute("SELECT id, name_ru FROM products", fetchall=True)
    builder = InlineKeyboardBuilder()
    for prod_id, name_ru in products:
        builder.add(InlineKeyboardButton(text=f"❌ {name_ru}", callback_data=f"delete_prod_{prod_id}"))
    builder.add(InlineKeyboardButton(text=texts['back'][lang], callback_data="admin_manage_products"))
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_delete_keyboard(lang: str, product_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['admin_manage_products']['yes'][lang], callback_data=f"confirm_delete_{product_id}"))
    builder.add(InlineKeyboardButton(text=texts['admin_manage_products']['no'][lang], callback_data="cancel_delete"))
    return builder.as_markup()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def get_user_lang(user_id: int) -> str:
    lang = db_execute("SELECT language FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return lang[0] if lang else 'ru'

# --- ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ (ПОЛЬЗОВАТЕЛЬ) ---
@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    
    user_exists = db_execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    
    # Получаем админа для приветствия
    welcome_admin_row = db_execute("SELECT value FROM settings WHERE key = 'welcome_admin_contact'", fetchone=True)
    welcome_admin = welcome_admin_row[0] if welcome_admin_row else ""

    if not user_exists:
        db_execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username), commit=True)
        await message.answer(texts['choose_lang'].format(welcome_admin), reply_markup=get_language_keyboard())
    else:
        lang = await get_user_lang(user_id)
        await message.answer(texts['welcome'][lang], reply_markup=get_main_menu_keyboard(lang))

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[-1]
    db_execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, callback.from_user.id), commit=True)
    await callback.message.edit_text(texts['welcome'][lang], reply_markup=get_main_menu_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(texts['welcome'][lang], reply_markup=get_main_menu_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data == "menu_shop")
async def show_shop(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(texts['shop_title'][lang], reply_markup=get_shop_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data == "menu_price")
async def show_price(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    currency = "TJS" if lang == 'tj' else "RUB"
    products = db_execute("SELECT name_ru, name_tj, price FROM products", fetchall=True)
    price_list = "\n".join([f"🔹 {name_tj if lang == 'tj' else name_ru} - {price} {currency}" for name_ru, name_tj, price in products])
    await callback.message.edit_text(f"<b>{texts['price_title'][lang]}</b>\n\n{price_list}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=texts['back'][lang], callback_data="back_to_main_menu")]]))
    await callback.answer()

@dp.callback_query(F.data == "menu_support")
async def show_support(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    admin_contacts = db_execute("SELECT value FROM settings WHERE key = 'admin_contacts'", fetchone=True)
    contacts = admin_contacts[0] if admin_contacts else "не указаны"
    await callback.message.edit_text(texts['admins_info'][lang].format(contacts), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=texts['back'][lang], callback_data="back_to_main_menu")]]))
    await callback.answer()

@dp.callback_query(F.data == "menu_faq")
async def show_faq(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(texts['faq_info'][lang], reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=texts['back'][lang], callback_data="back_to_main_menu")]]))
    await callback.answer()

@dp.callback_query(F.data == "menu_change_lang")
async def change_lang_menu(callback: CallbackQuery):
    welcome_admin_row = db_execute("SELECT value FROM settings WHERE key = 'welcome_admin_contact'", fetchone=True)
    welcome_admin = welcome_admin_row[0] if welcome_admin_row else ""
    await callback.message.edit_text(texts['choose_lang'].format(welcome_admin), reply_markup=get_language_keyboard())
    await callback.answer()

# --- ОБРАБОТЧИКИ ОТЗЫВОВ ---
@dp.callback_query(F.data == "menu_reviews")
async def start_review_process(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(ReviewState.waiting_for_text)
    await callback.message.edit_text(texts['enter_review'][lang])
    await callback.answer()

@dp.message(ReviewState.waiting_for_text)
async def receive_review_text(message: Message, state: FSMContext):
    review_text = message.text
    lang = await get_user_lang(message.from_user.id)
    await state.update_data(review_text=review_text)
    await state.set_state(ReviewState.confirming_send)
    await message.answer(texts['confirm_send_review'][lang].format(review_text), reply_markup=get_confirm_review_keyboard(lang))

@dp.callback_query(F.data == "confirm_send_review", ReviewState.confirming_send)
async def confirm_send_review(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    review_text = data.get('review_text')
    user_id = callback.from_user.id
    username = callback.from_user.username or f"id{user_id}"
    lang = await get_user_lang(user_id)

    if review_text:
        review_id = db_insert_get_id("INSERT INTO pending_reviews (user_id, username, review_text) VALUES (?, ?, ?)", (user_id, username, review_text))
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    texts['admin_new_review_notification']['ru'].format(username, user_id, review_text),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_review_{review_id}")],
                        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_review_{review_id}")]
                    ])
                )
            except Exception as e:
                logging.error(f"Could not send review notification to admin {admin_id}: {e}")
        await callback.message.edit_text(texts['review_sent_for_moderation'][lang])
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    lang = await get_user_lang(callback.from_user.id)
    await state.update_data(product_id=product_id)
    await state.set_state(OrderState.entering_game_id)
    await callback.message.edit_text(texts['enter_game_id'][lang])
    await callback.answer()

@dp.message(OrderState.entering_game_id)
async def enter_game_id(message: Message, state: FSMContext):
    game_id = message.text
    data = await state.get_data()
    product_id = data['product_id']
    
    product = db_execute("SELECT name_ru, name_tj, price FROM products WHERE id = ?", (product_id,), fetchone=True)
    payment_details = db_execute("SELECT value FROM settings WHERE key = 'payment_details'", fetchone=True)
    
    if not product or not payment_details:
        await message.answer("Произошла ошибка. Попробуйте позже.")
        await state.clear()
        return

    lang = await get_user_lang(message.from_user.id)
    currency = "TJS" if lang == 'tj' else "RUB"
    name = product[1] if lang == 'tj' else product[0]
    price = product[2]
    
    await state.update_data(game_id=game_id, product_name=name, price=price)
    await state.set_state(OrderState.waiting_for_receipt_intro)
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['send_receipt_btn'][lang], callback_data="start_send_receipt"))
    builder.add(InlineKeyboardButton(text=texts['back'][lang], callback_data="back_to_main_menu"))
    builder.adjust(1)
    
    await message.answer(
        texts['payment_info'][lang].format(name, price, currency, game_id, payment_details[0]),
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "start_send_receipt", OrderState.waiting_for_receipt_intro)
async def start_send_receipt(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(OrderState.waiting_for_receipt)
    await callback.message.answer(texts['send_receipt_request'][lang])
    await callback.answer()

@dp.message(OrderState.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    else:
        file_id = message.document.file_id
        file_type = 'document'
        
    await state.update_data(receipt_file_id=file_id, receipt_file_type=file_type, receipt_message_id=message.message_id)
    await state.set_state(OrderState.confirming_payment)
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=texts['i_paid_btn'][lang], callback_data="i_paid_confirm"))
    
    await message.answer(texts['receipt_received_ask_confirm'][lang], reply_markup=builder.as_markup())

@dp.callback_query(F.data == "i_paid_confirm", OrderState.confirming_payment)
async def i_paid_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = await get_user_lang(callback.from_user.id)
    user = callback.from_user

    notification_text = texts['admin_notification']['ru'].format(
        user.username or 'N/A',
        user.id,
        data.get('product_name', 'N/A'),
        data.get('game_id', 'N/A')
    )
    
    file_id = data.get('receipt_file_id')
    file_type = data.get('receipt_file_type')
    receipt_msg_id = data.get('receipt_message_id')

    # Отправляем уведомление каждому админу
    for admin_id in ADMIN_IDS:
        try:
            if file_type == 'photo':
                await bot.send_photo(
                    admin_id,
                    file_id,
                    caption=notification_text,
                    reply_markup=get_admin_order_keyboard(user.id, receipt_msg_id)
                )
            elif file_type == 'document':
                await bot.send_document(
                    admin_id,
                    file_id,
                    caption=notification_text,
                    reply_markup=get_admin_order_keyboard(user.id, receipt_msg_id)
                )
        except Exception as e:
            logging.error(f"Could not send message to admin {admin_id}: {e}")

    await callback.message.edit_text(texts['payment_success_final'][lang])
    await callback.answer()
    await state.clear()

@dp.message(OrderState.waiting_for_receipt)
async def process_receipt_invalid(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(texts['waiting_for_receipt_error'][lang])

# --- ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ ---
@dp.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_panel(message: Message):
    await message.answer(texts['admin_panel_title']['ru'], reply_markup=get_admin_panel_keyboard('ru')) # Админ панель всегда на русском

@dp.callback_query(F.data == "admin_panel_main", F.from_user.id.in_(ADMIN_IDS))
async def back_to_admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(texts['admin_panel_title']['ru'], reply_markup=get_admin_panel_keyboard('ru'))

@dp.callback_query(F.data == "cancel_send_review", ReviewState.confirming_send)
async def cancel_send_review(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    await callback.message.edit_text(texts['review_canceled'][lang])
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data.startswith("approve_review_") | F.data.startswith("decline_review_"), F.from_user.id.in_(ADMIN_IDS))
async def handle_review_moderation(callback: CallbackQuery):
    action_prefix, review_id_str = callback.data.rsplit('_', 1)
    review_id = int(review_id_str)
    
    review_data = db_execute("SELECT user_id, username, review_text FROM pending_reviews WHERE id = ?", (review_id,), fetchone=True)
    
    if not review_data:
        await callback.answer("Отзыв не найден или уже обработан.", show_alert=True)
        return
    
    user_id, username, review_text = review_data
    user_lang = await get_user_lang(user_id)
    
    if action_prefix == "approve_review":
        review_channel_id_row = db_execute("SELECT value FROM settings WHERE key = 'review_channel_id'", fetchone=True)
        review_channel_id = review_channel_id_row[0] if review_channel_id_row else None

        if review_channel_id:
            try:
                await bot.send_message(review_channel_id, texts['review_published_channel_msg']['ru'].format(username, review_text))
                await bot.send_message(user_id, texts['review_approved_user'][user_lang])
                await callback.message.edit_text(callback.message.text + "\n\n✅ ОТЗЫВ ОДОБРЕН И ОПУБЛИКОВАН")
            except Exception as e:
                await callback.answer(f"Ошибка публикации отзыва в канал или уведомления пользователя: {e}", show_alert=True)
                logging.error(f"Error publishing review {review_id} to channel or notifying user: {e}")
        else:
            await callback.answer("Не указан ID канала для отзывов в настройках!", show_alert=True)
            await callback.message.edit_text(callback.message.text + "\n\n❌ ОТЗЫВ НЕ ОПУБЛИКОВАН (нет ID канала)")
    elif action_prefix == "decline_review":
        try:
            await bot.send_message(user_id, texts['review_declined_user'][user_lang])
            await callback.message.edit_text(callback.message.text + "\n\n❌ ОТЗЫВ ОТКЛОНЕН")
        except Exception as e:
            await callback.answer(f"Не удалось уведомить пользователя: {e}", show_alert=True)
            logging.error(f"Error notifying user about declined review {review_id}: {e}")
            
    db_execute("DELETE FROM pending_reviews WHERE id = ?", (review_id,), commit=True)
    await callback.answer()

# Изменение реквизитов
@dp.callback_query(F.data == "admin_change_payment", F.from_user.id.in_(ADMIN_IDS))
async def change_payment_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.changing_payment_details)
    await callback.message.answer("Введите новые реквизиты для оплаты:")
    await callback.answer()

@dp.message(AdminState.changing_payment_details, F.from_user.id.in_(ADMIN_IDS))
async def change_payment_process(message: Message, state: FSMContext):
    db_execute("UPDATE settings SET value = ? WHERE key = 'payment_details'", (message.text,), commit=True)
    await message.answer("Реквизиты успешно обновлены!")
    await state.clear()

# Изменение контактов админов
@dp.callback_query(F.data == "admin_change_admins", F.from_user.id.in_(ADMIN_IDS))
async def change_admins_start(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminState.changing_admin_contacts)
    await callback.message.answer(texts['enter_new_admins'][lang])
    await callback.answer()

@dp.message(AdminState.changing_admin_contacts, F.from_user.id.in_(ADMIN_IDS))
async def change_admins_process(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    db_execute("UPDATE settings SET value = ? WHERE key = 'admin_contacts'", (message.text,), commit=True)
    await message.answer(texts['admins_updated'][lang])
    await state.clear()

# Изменение контакта админа в приветствии
@dp.callback_query(F.data == "admin_change_welcome_admin", F.from_user.id.in_(ADMIN_IDS))
async def change_welcome_admin_start(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(AdminState.changing_welcome_admin_contact)
    await callback.message.answer(texts['enter_new_welcome_admin'][lang])
    await callback.answer()

@dp.message(AdminState.changing_welcome_admin_contact, F.from_user.id.in_(ADMIN_IDS))
async def change_welcome_admin_process(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    db_execute("UPDATE settings SET value = ? WHERE key = 'welcome_admin_contact'", (message.text,), commit=True)
    await message.answer(texts['welcome_admin_updated'][lang])
    await state.clear()

# Изменение цен
@dp.callback_query(F.data == "admin_change_prices", F.from_user.id.in_(ADMIN_IDS))
async def change_prices_start(callback: CallbackQuery, state: FSMContext):
    products = db_execute("SELECT id, name_ru, price FROM products", fetchall=True)
    if not products:
        await callback.message.answer("Товары не найдены.")
        return
    
    text = "Выберите товар для изменения цены:\n" + "\n".join([f"/{i+1} - {name} ({price} RUB)" for i, (prod_id, name, price) in enumerate(products)])
    await state.update_data(products_map={i+1: prod_id for i, (prod_id, _, _) in enumerate(products)})
    await state.set_state(AdminState.changing_price_id)
    await callback.message.answer(text)
    await callback.answer()

@dp.message(AdminState.changing_price_id, F.from_user.id.in_(ADMIN_IDS))
async def change_price_id_process(message: Message, state: FSMContext):
    try:
        choice = int(message.text.replace('/', ''))
        data = await state.get_data()
        product_id = data['products_map'].get(choice)
        if not product_id:
            await message.answer("Неверный выбор. Попробуйте снова.")
            return
        
        await state.update_data(product_id_to_change=product_id)
        await state.set_state(AdminState.changing_price_value)
        await message.answer("Введите новую цену для этого товара:")
    except (ValueError, TypeError):
        await message.answer("Неверный формат. Введите номер товара, например /1")

@dp.message(AdminState.changing_price_value, F.from_user.id.in_(ADMIN_IDS))
async def change_price_value_process(message: Message, state: FSMContext):
    try:
        new_price = float(message.text)
        data = await state.get_data()
        product_id = data['product_id_to_change']
        
        db_execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id), commit=True)
        
        await message.answer("Цена успешно обновлена!")
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат. Введите число (например, 150.5).")

# --- УПРАВЛЕНИЕ ТОВАРАМИ ---
@dp.callback_query(F.data == "admin_manage_products", F.from_user.id.in_(ADMIN_IDS))
async def manage_products_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        texts['admin_manage_products']['title']['ru'],
        reply_markup=get_manage_products_keyboard('ru')
    )

# Добавление товара
@dp.callback_query(F.data == "admin_add_product", F.from_user.id.in_(ADMIN_IDS))
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.adding_product_name_ru)
    await callback.message.edit_text(texts['admin_manage_products']['enter_name_ru']['ru'])

@dp.message(AdminState.adding_product_name_ru, F.from_user.id.in_(ADMIN_IDS))
async def add_product_name_ru(message: Message, state: FSMContext):
    await state.update_data(name_ru=message.text)
    await state.set_state(AdminState.adding_product_name_tj)
    await message.answer(texts['admin_manage_products']['enter_name_tj']['ru'])

@dp.message(AdminState.adding_product_name_tj, F.from_user.id.in_(ADMIN_IDS))
async def add_product_name_tj(message: Message, state: FSMContext):
    await state.update_data(name_tj=message.text)
    await state.set_state(AdminState.adding_product_price)
    await message.answer(texts['admin_manage_products']['enter_price']['ru'])

@dp.message(AdminState.adding_product_price, F.from_user.id.in_(ADMIN_IDS))
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        data = await state.get_data()
        name_ru = data.get('name_ru')
        name_tj = data.get('name_tj')

        db_execute("INSERT INTO products (name_ru, name_tj, price) VALUES (?, ?, ?)", (name_ru, name_tj, price), commit=True)
        
        await message.answer(texts['admin_manage_products']['product_added']['ru'].format(name_ru))
        await state.clear()
        await admin_panel(message) # Возвращаемся в админ-панель
    except ValueError:
        await message.answer("Неверный формат цены. Попробуйте снова.")

# Удаление товара
@dp.callback_query(F.data == "admin_delete_product", F.from_user.id.in_(ADMIN_IDS))
async def delete_product_list(callback: CallbackQuery):
    await callback.message.edit_text(
        texts['admin_manage_products']['choose_product_to_delete']['ru'],
        reply_markup=get_delete_product_keyboard('ru')
    )

@dp.callback_query(F.data.startswith("delete_prod_"), F.from_user.id.in_(ADMIN_IDS))
async def delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    product = db_execute("SELECT name_ru FROM products WHERE id = ?", (product_id,), fetchone=True)
    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    
    await state.set_state(AdminState.deleting_product_confirm)
    await state.update_data(product_to_delete_id=product_id, product_to_delete_name=product[0])
    await callback.message.edit_text(
        texts['admin_manage_products']['confirm_delete']['ru'].format(product[0]),
        reply_markup=get_confirm_delete_keyboard('ru', product_id)
    )

@dp.callback_query(F.data.startswith("confirm_delete_"), AdminState.deleting_product_confirm, F.from_user.id.in_(ADMIN_IDS))
async def delete_product_execute(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    product_name = data.get('product_to_delete_name', 'Неизвестный товар')

    db_execute("DELETE FROM products WHERE id = ?", (product_id,), commit=True)
    await callback.message.edit_text(texts['admin_manage_products']['product_deleted']['ru'].format(product_name))
    await state.clear()

@dp.callback_query(F.data == "cancel_delete", AdminState.deleting_product_confirm, F.from_user.id.in_(ADMIN_IDS))
async def cancel_delete_product(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(texts['admin_manage_products']['delete_cancelled']['ru'])

@dp.callback_query(F.data.startswith("confirm_order_") | F.data.startswith("decline_order_"), F.from_user.id.in_(ADMIN_IDS))
async def handle_order_confirmation(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    action = parts[0]
    user_id_str = parts[2]
    message_id_str = parts[3]
    user_id = int(user_id_str)
    
    user_lang = await get_user_lang(user_id)
    
    if action == "confirm":
        try:
            await bot.send_message(user_id, texts['order_confirmed'][user_lang])
            
            current_text = callback.message.text or callback.message.caption or ""
            new_text = current_text + "\n\n✅ ЗАКАЗ ПОДТВЕРЖДЕН"
            if callback.message.content_type in [ContentType.PHOTO, ContentType.DOCUMENT]:
                await callback.message.edit_caption(caption=new_text)
            else:
                await callback.message.edit_text(text=new_text)
        except Exception as e:
            await callback.answer(f"Не удалось уведомить пользователя: {e}", show_alert=True)
    elif action == "decline":
        current_text = callback.message.text or callback.message.caption or ""
        await state.update_data(
            decline_user_id=user_id,
            decline_admin_message_id=callback.message.message_id,
            decline_admin_chat_id=callback.message.chat.id,
            decline_original_text=current_text,
            decline_content_type=callback.message.content_type
        )
        await state.set_state(AdminState.declining_order_reason)
        await callback.message.reply("✍️ Введите причину отказа для этого заказа:")
            
    await callback.answer()

@dp.message(AdminState.declining_order_reason, F.from_user.id.in_(ADMIN_IDS))
async def process_decline_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('decline_user_id')
    admin_message_id = data.get('decline_admin_message_id')
    chat_id = data.get('decline_admin_chat_id')
    original_text = data.get('decline_original_text')
    content_type = data.get('decline_content_type')
    reason = message.text
    
    user_lang = await get_user_lang(user_id)
    
    try:
        decline_msg = texts['order_declined'][user_lang] + f"\n\n💬 <b>Причина / Сабаб:</b> {reason}"
        await bot.send_message(user_id, decline_msg)
        
        new_text = original_text + f"\n\n❌ ЗАКАЗ ОТКЛОНЕН\n💬 Причина: {reason}"
        if content_type in [ContentType.PHOTO, ContentType.DOCUMENT]:
            await bot.edit_message_caption(chat_id=chat_id, message_id=admin_message_id, caption=new_text)
        else:
            await bot.edit_message_text(chat_id=chat_id, message_id=admin_message_id, text=new_text)
        await message.answer("✅ Заказ отклонен, пользователь уведомлен.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")
    
    await state.clear()

# Рассылка
@dp.callback_query(F.data == "admin_broadcast", F.from_user.id.in_(ADMIN_IDS))
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.broadcasting)
    await callback.message.answer("Введите текст для рассылки всем пользователям:")
    await callback.answer()

@dp.message(AdminState.broadcasting, F.from_user.id.in_(ADMIN_IDS))
async def broadcast_process(message: Message, state: FSMContext):
    users = db_execute("SELECT user_id FROM users", fetchall=True)
    count = 0
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, message.text)
            count += 1
            await asyncio.sleep(0.1) # Небольшая задержка, чтобы не попасть под лимиты TG
        except Exception as e:
            logging.warning(f"Could not send broadcast to {user_id}: {e}")
    
    await message.answer(f"Рассылка завершена. Сообщение отправлено {count} пользователям.")
    await state.clear()


# --- ТОЧКА ВХОДА ---
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
