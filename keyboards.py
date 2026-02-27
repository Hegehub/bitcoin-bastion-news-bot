from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton(text="📊 BTC Price", callback_data="btc_price")],
        [InlineKeyboardButton(text="😨 Fear & Greed", callback_data="fear_greed")],
        [InlineKeyboardButton(text="📈 Dominance", callback_data="dominance")],
        [InlineKeyboardButton(text="💧 Liquidity", callback_data="liquidity")],
        [InlineKeyboardButton(text="📰 Analyze News", callback_data="analyze_news")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🔧 Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Post to Channel", callback_data="admin_post")],
        [InlineKeyboardButton(text="📊 Bot Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Subscribers", callback_data="admin_subs")],
    ])
