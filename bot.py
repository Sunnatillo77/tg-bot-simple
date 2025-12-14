import os
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import httpx
from telegram.request import HTTPXRequest

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from telegram.constants import ParseMode

# Настройки прокси (если требуется)
PROXY_URL = None  # или "socks5://user:pass@host:port"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8290382177:AAEglg5yxQe2Q1oTjEj1ui1IyO7YNFHdaxc"

# Состояния для ConversationHandler
CHOOSING, TYPING_NAME, TYPING_PHONE, TYPING_ADDRESS = range(4)

PRODUCTS = {
    1: {
        "name": "Современный фасад",
        "price": "850",
        "description": "Современный дизайн с использованием инновационных материалов. Идеально для загородных домов.",
        "category": "Фасады",
        "photo_url": "https://i.pinimg.com/originals/04/f9/65/04f9652c3c0f47fd3d98bb89054b7b02.jpg"
    },
    2: {
        "name": "Классический фасад",
        "price": "720",
        "description": "Традиционный дизайн с элементами классической архитектуры. Вызывает чувство прочности и надежности.",
        "category": "Фасады",
        "photo_url": "https://avatars.mds.yandex.net/i?id=1db35a6aecc7aba6f0a9936d996d3ab086f3ffee-5883245-images-thumbs&ref=rim&n=33&w=469&h=250"
    },
    3: {
        "name": "Деревянный фасад",
        "price": "980",
        "description": "Натуральное дерево с защитным покрытием. Придает дому теплый и уютный вид, идеально для загородных домов.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1513584684374-8bab748fbf90?w=800&auto=format&fit=crop"
    },
    4: {
        "name": "Минималистичный фасад",
        "price": "780",
        "description": "Четкие линии, простые формы и лаконичность. Для тех, кто ценит современный стиль и функциональность.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=800&auto=format&fit=crop"
    },
    5: {
        "name": "Европейский фасад",
        "price": "920",
        "description": "Современный дизайн в лучших традициях европейской архитектуры.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1494522358652-c549345d2c9e?w=800&auto=format&fit=crop"
    },
    6: {
        "name": "Скандинавский фасад",
        "price": "820",
        "description": "Сдержанный дизайн в скандинавском стиле с использованием натуральных материалов.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1513584684374-8bab748fbf90?w=800&auto=format&fit=crop"
    },
    7: {
        "name": "Кирпичный фасад",
        "price": "1050",
        "description": "Классический кирпич с современными технологиями монтажа.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&auto=format&fit=crop"
    },
    8: {
        "name": "Каменный фасад",
        "price": "1280",
        "description": "Натуральный или искусственный камень для солидного и представительного внешнего вида.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&auto=format&fit=crop"
    },
    9: {
        "name": "Стеклянный фасад",
        "price": "1360",
        "description": "Современные стеклянные панели для максимального естественного освещения и современного внешнего вида.",
        "category": "Фасады",
        "photo_url": "https://avatars.mds.yandex.net/i?id=97db83771c2060e257cf534a2592b5a4_l-4434285-images-thumbs&n=13"
    },
    10: {
        "name": "Фасад из сэндвич-панелей",
        "price": "890",
        "description": "Энергоэффективное решение с отличной теплоизоляцией.",
        "category": "Фасады",
        "photo_url": "https://avatars.mds.yandex.net/get-altay/14398723/2a000001934d5f8bb69d9b30d979fffc6eea/XXL_height"
    },
    11: {
        "name": "Фасад из гипсокартона",
        "price": "740",
        "description": "Классическое решение с современными материалами.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&auto=format&fit=crop"
    },
    12: {
        "name": "Вентилируемый фасад",
        "price": "960",
        "description": "Современная система с воздушным зазором для оптимального влажностного режима и дополнительной теплоизоляции.",
        "category": "Фасады",
        "photo_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&auto=format&fit=crop"
    }
}

# Контактная информация
CONTACT_INFO = {
    "address": "Яккабогский район, Кайрагоч МФЙ",
    "phone": "+998 88 111 11 22 33",
    "email": "info@karooch-fasad.uz",
    "whatsapp": "https://wa.me/79036660426",
    "telegram": "https://t.me/M_S0426",
    "work_hours": "Пн-Пт: 8:00-18:00, Сб: 9:00-16:00"
}

# Файл для хранения корзин
CART_FILE = "user_carts.json"


class KaroochBot:
    def __init__(self):
        self.user_carts = self.load_carts()

    def load_carts(self) -> Dict:
        """Загрузка корзин из файла"""
        if os.path.exists(CART_FILE):
            try:
                with open(CART_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки корзин: {e}")
                return {}
        return {}

    def save_carts(self):
        """Сохранение корзин в файл"""
        try:
            with open(CART_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_carts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения корзин: {e}")

    def get_cart(self, user_id: int) -> Dict:
        """Получить корзину пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_carts:
            self.user_carts[user_id_str] = {}
        return self.user_carts[user_id_str]

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        """Добавить товар в корзину"""
        cart = self.get_cart(user_id)
        product_id_str = str(product_id)

        if product_id_str in cart:
            cart[product_id_str]["quantity"] += quantity
        else:
            if product_id not in PRODUCTS:
                return False
            product = PRODUCTS[product_id]
            cart[product_id_str] = {
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "added_at": datetime.now().isoformat()
            }

        self.user_carts[str(user_id)] = cart
        self.save_carts()
        return True

    def remove_from_cart(self, user_id: int, product_id: int):
        """Удалить товар из корзины"""
        cart = self.get_cart(user_id)
        product_id_str = str(product_id)

        if product_id_str in cart:
            del cart[product_id_str]
            self.user_carts[str(user_id)] = cart
            self.save_carts()
            return True
        return False

    def clear_cart(self, user_id: int):
        """Очистить корзину"""
        self.user_carts[str(user_id)] = {}
        self.save_carts()

    def get_cart_total(self, user_id: int) -> str:
        """Получить общую сумму корзины"""
        cart = self.get_cart(user_id)
        total = 0

        for item in cart.values():
            try:
                price = int(item["price"])
                total += price * item["quantity"]
            except (ValueError, KeyError):
                logger.warning(f"Не удалось распарсить цену: {item.get('price', 'N/A')}")
                continue

        return f"{total:,} рублей".replace(",", " ")


# Создаем экземпляр бота
bot_manager = KaroochBot()


async def start(update: Update, context) -> None:
    user = update.effective_user
    welcome_text = f"""
🏠 *Здравствуйте {user.first_name}!*

Добро пожаловать в Telegram-бот компании *Karooch Fasad*!

Мы предоставляем услуги производства и установки качественных фасадов.

*📊 Наша статистика:*
• 1+ год опыта
• 100+ завершенных проектов
• 100+ довольных клиентов
• 24/7 поддержка

Что вы хотите сделать?
"""

    keyboard = [
        [InlineKeyboardButton("🛍️ Каталог товаров", callback_data='catalog')],
        [InlineKeyboardButton("🛒 Моя корзина", callback_data='cart')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
        [InlineKeyboardButton("🏢 О нас", callback_data='about')],
        [InlineKeyboardButton("💰 Оформить заказ", callback_data='order')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def show_catalog(update: Update, context) -> None:
    """Показать каталог товаров"""
    query = update.callback_query
    await query.answer()

    page = context.user_data.get('catalog_page', 0)
    products_per_page = 4
    start_idx = page * products_per_page
    end_idx = start_idx + products_per_page

    product_ids = list(PRODUCTS.keys())
    page_products = product_ids[start_idx:end_idx]

    if not page_products:
        await query.edit_message_text("Товары не найдены.")
        return

    text = f"🏗️ *Наши фасады*\n\n"

    for product_id in page_products:
        product = PRODUCTS[product_id]
        text += f"*{product_id}. {product['name']}*\n"
        text += f"💰 *Цена:* от {product['price']} руб/м²\n"
        text += f"📝 {product['description'][:100]}...\n\n"

    text += f"*Страница {page + 1}/{((len(PRODUCTS) - 1) // products_per_page) + 1}*"

    keyboard = []

    # Кнопки для товаров
    for product_id in page_products:
        product = PRODUCTS[product_id]
        keyboard.append([
            InlineKeyboardButton(
                f"➕ {product['name'][:20]}",
                callback_data=f'view_{product_id}'
            )
        ])

    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'page_{page - 1}'))

    nav_buttons.append(InlineKeyboardButton("🛒 Корзина", callback_data='cart'))

    if end_idx < len(PRODUCTS):
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'page_{page + 1}'))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("🏠 Главная", callback_data='back_to_main'),
        InlineKeyboardButton("📞 Контакты", callback_data='contact')
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def change_catalog_page(update: Update, context) -> None:

    query = update.callback_query
    await query.answer()

    page = int(query.data.split('_')[1])
    context.user_data['catalog_page'] = page
    await show_catalog(update, context)


async def view_product(update: Update, context) -> None:
    """Просмотр деталей товара"""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split('_')[1])

    if product_id not in PRODUCTS:
        await query.edit_message_text("Товар не найден.")
        return

    product = PRODUCTS[product_id]

    text = f"""
*🏗️ {product['name']}*

📝 *Описание:*
{product['description']}

💰 *Цена:* {product['price']} руб/м²
📦 *Категория:* {product['category']}

*📞 Для заказа:*
Телефон: {CONTACT_INFO['phone']}
WhatsApp: {CONTACT_INFO['whatsapp']}
Telegram: {CONTACT_INFO['telegram']}
"""

    keyboard = [
        [
            InlineKeyboardButton("🛒 В корзину", callback_data=f'add_{product_id}'),
            InlineKeyboardButton("💰 Заказать", callback_data=f'order_{product_id}')
        ],
        [
            InlineKeyboardButton("📚 В каталог", callback_data='catalog'),
            InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def add_to_cart_handler(update: Update, context) -> None:
    """Добавить товар в корзину"""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split('_')[1])
    user_id = query.from_user.id

    if bot_manager.add_to_cart(user_id, product_id):
        product_name = PRODUCTS[product_id]["name"]
        await query.message.reply_text(f"✅ *{product_name}* добавлен в корзину!", parse_mode=ParseMode.MARKDOWN)
    else:
        await query.message.reply_text("❌ Произошла ошибка!", parse_mode=ParseMode.MARKDOWN)


async def show_cart_handler(update: Update, context) -> None:
    """Показать корзину"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cart = bot_manager.get_cart(user_id)

    if not cart:
        text = "🛒 *Ваша корзина пуста*"

        keyboard = [
            [InlineKeyboardButton("🛍️ Смотреть товары", callback_data='catalog')],
            [InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')]
        ]
    else:
        text = "🛒 *Ваша корзина*\n\n"
        total_items = 0

        for idx, (product_id, item) in enumerate(cart.items(), 1):
            text += f"*{idx}. {item['name']}*\n"
            text += f"   Количество: {item['quantity']} шт\n"
            text += f"   Цена: {item['price']} руб/м²\n\n"
            total_items += item["quantity"]

        total_price = bot_manager.get_cart_total(user_id)
        text += f"*Всего товаров:* {total_items} шт\n"
        text += f"*Общая сумма:* {total_price}\n\n"
        text += "*📝 Примечание:* Цена фасада указана за квадратный метр"

        keyboard = [
            [InlineKeyboardButton("🗑️ Очистить корзину", callback_data='clear_cart')],
            [InlineKeyboardButton("💰 Оформить заказ", callback_data='checkout')],
            [InlineKeyboardButton("🛍️ В каталог", callback_data='catalog')],
            [InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def clear_cart_handler(update: Update, context) -> None:
    """Очистить корзину"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot_manager.clear_cart(user_id)

    await query.edit_message_text("🗑️ *Корзина очищена!*", parse_mode=ParseMode.MARKDOWN)


async def checkout_handler(update: Update, context) -> int:
    """Начало оформления заказа"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cart = bot_manager.get_cart(user_id)

    if not cart:
        await query.edit_message_text("Ваша корзина пуста!")
        return ConversationHandler.END

    text = """
💰 *Оформление заказа*

Введите ваше ФИО:
"""

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    return TYPING_NAME


async def received_name(update: Update, context) -> int:
    """Получено имя"""
    user_name = update.message.text.strip()
    context.user_data['order_name'] = user_name

    text = f"✅ *Имя принято:* {user_name}\n\nВведите ваш номер телефона (пример: +998901234567):"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return TYPING_PHONE


async def received_phone(update: Update, context) -> int:
    """Получен телефон"""
    user_phone = update.message.text.strip()
    context.user_data['order_phone'] = user_phone

    text = f"✅ *Номер телефона принят:* {user_phone}\n\nВведите адрес доставки:"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return TYPING_ADDRESS


async def received_address(update: Update, context) -> int:
    """Получен адрес и завершение заказа"""
    address = update.message.text.strip()
    context.user_data['order_address'] = address

    user_name = context.user_data.get('order_name', 'Неизвестно')
    user_phone = context.user_data.get('order_phone', 'Неизвестно')
    user_id = update.effective_user.id
    cart = bot_manager.get_cart(user_id)

    order_text = f"""
✅ *Заказ принят!*

👤 *Клиент:* {user_name}
📞 *Телефон:* {user_phone}
📍 *Адрес:* {address}

📦 *Состав заказа:*
"""

    total_items = 0
    for item in cart.values():
        order_text += f"• {item['name']} - {item['quantity']} шт\n"
        total_items += item["quantity"]

    total_price = bot_manager.get_cart_total(user_id)
    order_text += f"\n📊 *Итого:* {total_items} шт товаров"
    order_text += f"\n💰 *Общая сумма:* {total_price}"

    order_text += f"""

📝 *Номер заказа:* ORD{datetime.now().strftime('%Y%m%d%H%M%S')}
📅 *Дата:* {datetime.now().strftime('%d.%m.%Y %H:%M')}

Ваш заказ принят. В ближайшее время наш менеджер свяжется с вами для уточнения деталей.

*📞 Для связи:*
Телефон: {CONTACT_INFO['phone']}
WhatsApp: {CONTACT_INFO['whatsapp']}
Telegram: {CONTACT_INFO['telegram']}

Спасибо, что выбрали нас! 🏠
"""

    bot_manager.clear_cart(user_id)

    keyboard = [
        [InlineKeyboardButton("🛍️ Новый заказ", callback_data='catalog')],
        [InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        order_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    logger.info(f"Новый заказ от {user_name} ({user_phone}). Сумма: {total_price}")
    return ConversationHandler.END


async def cancel(update: Update, context) -> int:
    """Отмена оформления заказа"""
    await update.message.reply_text("❌ Заказ отменен.")
    return ConversationHandler.END


async def show_contact_info(update: Update, context) -> None:
    """Контактная информация"""
    query = update.callback_query
    await query.answer()

    text = f"""
🏢 *Karooch Fasad* - КАЧЕСТВЕННЫЕ ФАСАДЫ ДЛЯ ВАШЕЙ ЖИЗНИ

*📞 Контактная информация:*
📍 Адрес: {CONTACT_INFO['address']}
📞 Телефон: {CONTACT_INFO['phone']}
📧 Email: {CONTACT_INFO['email']}
🕐 Время работы: {CONTACT_INFO['work_hours']}

*📱 Социальные сети:*
WhatsApp: {CONTACT_INFO['whatsapp']}
Telegram: {CONTACT_INFO['telegram']}
"""

    keyboard = [
        [
            InlineKeyboardButton("📱 WhatsApp", url=CONTACT_INFO['whatsapp']),
            InlineKeyboardButton("📲 Telegram", url=CONTACT_INFO['telegram'])
        ],
        [
            InlineKeyboardButton("🏠 На главную", callback_data='back_to_main'),
            InlineKeyboardButton("🛍️ Каталог", callback_data='catalog')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def show_about(update: Update, context) -> None:
    """О компании"""
    query = update.callback_query
    await query.answer()

    text = """
🏢 *О компании*

Компания "Karooch Fasad" более 1 года предоставляет услуги по производству и установке высококачественных фасадов.

*✨ Наши преимущества:*
✅ *Качество* - Строгий контроль качества
✅ *Профессионализм* - Опытные специалисты
✅ *Экологичность* - Безопасные материалы
✅ *Гарантия* - Гарантия на все продукты

*📊 Статистика:*
• 1+ год опыта
• 100+ проектов
• 100+ клиентов
• 24/7 поддержка
"""

    keyboard = [
        [InlineKeyboardButton("🛍️ Каталог", callback_data='catalog')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
        [InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def back_to_main(update: Update, context) -> None:
    """Вернуться на главную"""
    query = update.callback_query
    await query.answer()
    await start(update, context)


async def order_product(update: Update, context) -> None:
    """Быстрый заказ"""
    query = update.callback_query
    await query.answer()

    if '_' in query.data and query.data.startswith('order_'):
        product_id = int(query.data.split('_')[1])
        product = PRODUCTS[product_id]
        text = f"🚀 *Быстрый заказ: {product['name']}*\n\nЦена: {product['price']} руб/м²"
    else:
        text = "💰 *Оформить заказ*"

    keyboard = [
        [
            InlineKeyboardButton("📱 WhatsApp", url=CONTACT_INFO['whatsapp']),
            InlineKeyboardButton("📲 Telegram", url=CONTACT_INFO['telegram'])
        ],
        [
            InlineKeyboardButton("🛍️ Каталог", callback_data='catalog'),
            InlineKeyboardButton("🏠 На главную", callback_data='back_to_main')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def help_command(update: Update, context) -> None:
    """Команда /help"""
    help_text = """
🤖 *Команды бота:*

/start - Начать
/help - Помощь
/catalog - Каталог
/cart - Корзина
/contact - Контакты
/about - О компании

*📱 Контакты:*
📞 +998 88 111 22 33
WhatsApp: https://wa.me/79036660426
Telegram: https://t.me/M_S0426
"""

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def message_handler(update: Update, context) -> None:
    """Обработчик неизвестных сообщений"""
    await update.message.reply_text(
        "Я не понимаю вас. Начните с /start или посмотрите /help."
    )


def main() -> None:
    """Запуск бота с настройкой прокси"""
    request_kwargs = {}

    if PROXY_URL:
        request_kwargs['proxy'] = PROXY_URL

    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
        **request_kwargs
    )

    application = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .build()
    )

    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout_handler, pattern='^checkout$')],
        states={
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            TYPING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_phone)],
            TYPING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_address)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(show_catalog, pattern='^catalog$'))
    application.add_handler(CallbackQueryHandler(change_catalog_page, pattern='^page_'))
    application.add_handler(CallbackQueryHandler(view_product, pattern='^view_'))
    application.add_handler(CallbackQueryHandler(add_to_cart_handler, pattern='^add_'))
    application.add_handler(CallbackQueryHandler(show_cart_handler, pattern='^cart$'))
    application.add_handler(CallbackQueryHandler(clear_cart_handler, pattern='^clear_cart$'))
    application.add_handler(CallbackQueryHandler(checkout_handler, pattern='^checkout$'))
    application.add_handler(CallbackQueryHandler(order_product, pattern='^order'))
    application.add_handler(CallbackQueryHandler(show_contact_info, pattern='^contact$'))
    application.add_handler(CallbackQueryHandler(show_about, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))

    # ConversationHandler
    application.add_handler(conv_handler)

    # Последний обработчик
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("=" * 60)
    print("🤖 Telegram-бот Karooch Fasad v21.4 запущен!")
    print(f"🔑 Токен: {TOKEN[:10]}...")
    print("=" * 60)
    print("✅ Функционал: Каталог | Корзина | Заказы | Контакты")
    print("👉 /start для запуска")
    print("=" * 60)

    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    os.makedirs('photos', exist_ok=True)
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.exception("Критическая ошибка")