from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главная reply-клавиатура с основными командами."""
    buttons = [
        [KeyboardButton(text="📰 Последние новости")],
        [KeyboardButton(text="💰 Цена BTC"), KeyboardButton(text="😨 Индекс страха")],
        [KeyboardButton(text="🐋 Киты"), KeyboardButton(text="💥 Ликвидации")],
        [KeyboardButton(text="🔔 Подписки"), KeyboardButton(text="📊 Доминация")]
    ]
    
    # Если пользователь админ, добавляем кнопку админ-панели
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ панель")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def subscription_keyboard(user) -> InlineKeyboardMarkup:
    """Inline-клавиатура для управления подписками + кнопка Назад."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"{'✅' if user.subscribed_whales else '❌'} Киты",
        callback_data="sub_whales"
    ))
    builder.row(InlineKeyboardButton(
        text=f"{'✅' if user.subscribed_liquidations else '❌'} Ликвидации",
        callback_data="sub_liquidations"
    ))
    builder.row(InlineKeyboardButton(
        text=f"{'✅' if user.subscribed_triggered else '❌'} Триггерные новости",
        callback_data="sub_triggered"
    ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()

def admin_keyboard() -> InlineKeyboardMarkup:
    """Админская inline-клавиатура."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📡 Статус API", callback_data="admin_api_status")
    builder.button(text="⚙️ Настройки триггера", callback_data="admin_settings")
    builder.button(text="📢 Отправить в канал", callback_data="admin_broadcast_channel")
    builder.button(text="📣 Отправить всем", callback_data="admin_broadcast_all")
    builder.adjust(2)
    return builder.as_markup()