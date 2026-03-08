start_message = 👋 Привет! Я бот крипто-аналитики.\n\nЯ получаю новости в реальном времени и определяю, какие из них вызвали движение цены. Такие новости публикуются в канале.\n\n📊 Доступные команды:\n/btc — цена BTC, страх/жадность, доминация\n/whales — последние китовые транзакции\n/liquidations — последние ликвидации\n/funding — ставки фандинга\n/latest — последние 5 новостей\n/historical BTC — архив новостей по Bitcoin\n/international ko — новости из Кореи\n/ask Что с ETF? — вопрос AI\n/factcheck [текст] — проверка фактов\n/summarize [url] — краткое содержание\n/entities [текст] — извлечение сущностей\n/gainers — топ роста\n/losers — топ падения\n/coin ethereum — информация о монете\n/heatmap — тепловая карта\n/options — данные по опционам\n/orderbook BTC/USD — стакан ордеров\n/feargreed — индекс страха и жадности\n/dominance — доминация BTC и ETH\n/subscribe — управление подписками\n/language — смена языка

btc_price = 💰 <b>Bitcoin (BTC)</b>\nЦена: <code>${price:,.2f}</code>\n\n😨 Индекс страха и жадности: <b>{fear}</b> ({fear_class})\n📊 Доминация BTC: <b>{btc_dom:.2f}%</b>\n📊 Доминация ETH: <b>{eth_dom:.2f}%</b>

whales_title = 🐋 <b>Последние китовые транзакции:</b>\n\n
whale_entry = • <code>{amount:.2f} {coin}</code> (${value:,.0f})\n  From: <code>{from_addr}</code> → To: <code>{to_addr}</code>\n  <a href='{url}'>Транзакция</a>\n\n

liquidations_title = 💥 <b>Последние ликвидации:</b>\n\n
liquidation_entry = {emoji} {side} <code>{amount:,.0f}$</code> на {pair}\n

funding_title = 💰 <b>Funding Rates (8h):</b>\n\n
funding_entry = {emoji} {pair}: <code>{rate}%</code>\n

latest_news_title = 📰 <b>Последние новости:</b>\n\n
news_entry = • <a href='{url}'>{title}</a> — <i>{source}</i>  <code>#{tickers}</code>\n

historical_news_title = 📚 <b>Архив новостей по {ticker}:</b>\n\n

international_news_title = 🌍 <b>Международные новости ({lang}):</b>\n\n

ask_response = 🤖 <b>Ответ AI:</b>\n\n<blockquote>{response}</blockquote>
ask_prompt = Что вы хотите спросить о криптовалютах?

summarize_prompt = Отправьте URL новости для краткого содержания:
summary_result = 📝 <b>Краткое содержание:</b>\n\n<blockquote>{summary}</blockquote>

factcheck_prompt = Отправьте утверждение для проверки фактов:
factcheck_result = 🔍 <b>Результат проверки фактов:</b>\n\n{result}

entities_prompt = Отправьте текст для извлечения сущностей:
entities_result = 🔬 <b>Извлеченные сущности:</b>\n\n{entities}

movers_title = 📈 <b>Топ {type}:</b>\n\n
mover_entry = {emoji} <code>{symbol}</code>: {change:+.2f}% (${price})\n

coin_prompt = Введите название монеты (например: bitcoin, ethereum):
coin_info = 🪙 <b>{name} ({symbol})</b>\n💰 Цена: <code>${price:,.2f}</code>\n📊 Рыночная капитализация: <code>${market_cap:,.0f}</code>\n📈 Объем (24ч): <code>${volume:,.0f}</code>\n🔄 Циркулирующее предложение: <code>{circulating_supply:,.0f}</code>\n🏆 Рыночный ранг: <code>#{rank}</code>\n\n{description}

heatmap_title = 🔥 <b>Тепловая карта рынка</b>\n(зеленый = рост, красный = падение)

options_title = 📊 <b>Данные по опционам</b>\n\n{data}

orderbook_prompt = Введите торговую пару (например: BTC/USD):
orderbook_title = 📚 <b>Стакан ордеров {pair}</b>\n\nПокупка (Bids):\n{bids}\n\nПродажа (Asks):\n{asks}

feargreed = 😨 Индекс страха и жадности: <b>{value}</b> — {classification}

dominance = 📊 Доминация BTC: <b>{btc:.2f}%</b>\n📊 Доминация ETH: <b>{eth:.2f}%</b>

subscribe_menu = 🔔 <b>Управление подписками:</b>\n\nВыберите типы уведомлений:

language_selected = ✅ Язык изменен на русский

error_occurred = ❌ Произошла ошибка. Пожалуйста, попробуйте позже.

no_data = ❌ Не удалось получить данные.

historical_prompt = Введите тикер (например: BTC, ETH):