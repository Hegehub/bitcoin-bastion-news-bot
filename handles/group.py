from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bibabot_client import BibabotAPIClient
from bibabot_client import BibabotAPIClient

client = BibabotAPIClient()
router = Router()
client = BibabotAPIClient()

@router.message(Command("btc"))
async def btc_group(message: Message):
    price = await client.get_btc_price_coindesk()
    if price:
        await message.reply(f"💰 BTC Price: ${price:,.0f}")
    else:
        await message.reply("Не удалось получить цену.")

@router.message(Command("feargreed"))
async def feargreed_group(message: Message):
    fg = await client.get_fear_greed()
    if fg:
        await message.reply(f"😨 Fear & Greed: {fg['value']} — {fg['value_classification']}")
    else:
        await message.reply("Не удалось получить индекс.")

# Аналогично для /dominance, /liquidations, /whales, /latest, /search, /analyze
