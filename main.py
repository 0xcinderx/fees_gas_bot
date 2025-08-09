import asyncio
import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import threading
from keep_alive import keep_alive

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BlockchainFeesBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд и коллбэков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        keyboard = [
            [
                InlineKeyboardButton("🟣 TON", callback_data="ton"),
                InlineKeyboardButton("🟠 Bitcoin", callback_data="bitcoin")
            ],
            [
                InlineKeyboardButton("🔵 Ethereum", callback_data="ethereum"),
                InlineKeyboardButton("🟡 BSC", callback_data="bsc")
            ],
            [
                InlineKeyboardButton("🟢 Solana", callback_data="solana"),
                InlineKeyboardButton("🔴 Tron", callback_data="tron")
            ],
            [
                InlineKeyboardButton("🟪 Polygon", callback_data="polygon"),
                InlineKeyboardButton("🔷 Arbitrum", callback_data="arbitrum")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            "🤖 Добро пожаловать в бот мониторинга комиссий блокчейнов!\n\n"
            "Выберите блокчейн для просмотра текущих комиссий:"
        )

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн-кнопки"""
        query = update.callback_query
        await query.answer()

        blockchain = query.data

        try:
            fees_info = await self.get_blockchain_fees(blockchain)
            await query.edit_message_text(text=fees_info)
        except Exception as e:
            logger.error(f"Ошибка получения данных для {blockchain}: {e}")
            await query.edit_message_text(
                text=f"❌ Ошибка получения данных для {blockchain.upper()}. Попробуйте позже."
            )

    async def get_token_price(self, token_id: str) -> float:
        """Получение цены токена через CoinGecko API"""
        try:
            response = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd",
                timeout=10
            )
            data = response.json()
            return data[token_id]['usd']
        except Exception as e:
            logger.error(f"Ошибка получения цены {token_id}: {e}")
            return None

    async def get_blockchain_fees(self, blockchain: str) -> str:
        """Получение информации о комиссиях для выбранного блокчейна"""
        try:
            if blockchain == "ethereum":
                return await self.get_ethereum_fees()
            elif blockchain == "bsc":
                return await self.get_bsc_fees()
            elif blockchain == "bitcoin":
                return await self.get_bitcoin_fees()
            elif blockchain == "solana":
                return await self.get_solana_fees()
            elif blockchain == "ton":
                return await self.get_ton_fees()
            elif blockchain == "tron":
                return await self.get_tron_fees()
            elif blockchain == "polygon":
                return await self.get_polygon_fees()
            elif blockchain == "arbitrum":
                return await self.get_arbitrum_fees()
            else:
                return "❌ Неизвестный блокчейн"
        except Exception as e:
            logger.error(f"Ошибка получения данных для {blockchain}: {e}")
            raise

    async def get_ethereum_fees(self) -> str:
        """Получение комиссий Ethereum через Etherscan API"""
        try:
            response = requests.get(
                "https://api.etherscan.io/api?module=gastracker&action=gasoracle",
                timeout=10
            )
            data = response.json()

            if data['status'] == '1':
                safe = float(data['result']['SafeGasPrice'])
                standard = float(data['result']['ProposeGasPrice'])
                fast = float(data['result']['FastGasPrice'])

                # Получаем цену ETH
                eth_price = await self.get_token_price("ethereum")

                # Стандартная транзакция ETH ~21000 gas
                gas_limit = 21000

                if eth_price:
                    safe_usd = (safe * gas_limit * 0.000000001) * eth_price
                    standard_usd = (standard * gas_limit * 0.000000001) * eth_price
                    fast_usd = (fast * gas_limit * 0.000000001) * eth_price

                    return (
                        f"🔵 **Ethereum (ETH)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei (≈ ${fast_usd:.3f})\n"
                        f"📊 Стандартная: {standard} Gwei (≈ ${standard_usd:.3f})\n"
                        f"🐌 Безопасная: {safe} Gwei (≈ ${safe_usd:.3f})\n\n"
                        f"💡 Расчет для простого перевода (21k gas)\n"
                        f"📈 Курс ETH: ${eth_price:.2f}"
                    )
                else:
                    return (
                        f"🔵 **Ethereum (ETH)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei\n"
                        f"📊 Стандартная: {standard} Gwei\n"
                        f"🐌 Безопасная: {safe} Gwei\n\n"
                        f"💡 1 Gwei = 0.000000001 ETH"
                    )
            else:
                return "❌ Не удалось получить данные Ethereum"
        except Exception as e:
            logger.error(f"Ошибка API Ethereum: {e}")
            return "❌ Ошибка получения данных Ethereum"

    async def get_bsc_fees(self) -> str:
        """Получение комиссий BSC через BscScan API"""
        try:
            response = requests.get(
                "https://api.bscscan.com/api?module=gastracker&action=gasoracle",
                timeout=10
            )
            data = response.json()

            if data['status'] == '1':
                safe = float(data['result']['SafeGasPrice'])
                standard = float(data['result']['ProposeGasPrice'])
                fast = float(data['result']['FastGasPrice'])

                # Получаем цену BNB
                bnb_price = await self.get_token_price("binancecoin")

                # Стандартная транзакция BSC ~21000 gas
                gas_limit = 21000

                if bnb_price:
                    safe_usd = (safe * gas_limit * 0.000000001) * bnb_price
                    standard_usd = (standard * gas_limit * 0.000000001) * bnb_price
                    fast_usd = (fast * gas_limit * 0.000000001) * bnb_price

                    return (
                        f"🟡 **BSC (BNB)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei (≈ ${fast_usd:.4f})\n"
                        f"📊 Стандартная: {standard} Gwei (≈ ${standard_usd:.4f})\n"
                        f"🐌 Безопасная: {safe} Gwei (≈ ${safe_usd:.4f})\n\n"
                        f"💡 Расчет для простого перевода (21k gas)\n"
                        f"📈 Курс BNB: ${bnb_price:.2f}"
                    )
                else:
                    return (
                        f"🟡 **BSC (BNB)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei\n"
                        f"📊 Стандартная: {standard} Gwei\n"
                        f"🐌 Безопасная: {safe} Gwei\n\n"
                        f"💡 Обычно 5-10 Gwei для BSC"
                    )
            else:
                return "❌ Не удалось получить данные BSC"
        except Exception as e:
            logger.error(f"Ошибка API BSC: {e}")
            return "❌ Ошибка получения данных BSC"

    async def get_bitcoin_fees(self) -> str:
        """Получение комиссий Bitcoin через Mempool.space API"""
        try:
            response = requests.get(
                "https://mempool.space/api/v1/fees/recommended",
                timeout=10
            )
            data = response.json()

            fast = data['fastestFee']
            half_hour = data['halfHourFee']
            hour = data['hourFee']

            # Получаем цену BTC
            btc_price = await self.get_token_price("bitcoin")

            # Средняя транзакция Bitcoin ~250 байт
            tx_size = 250

            if btc_price:
                fast_btc = fast * tx_size * 0.00000001
                half_hour_btc = half_hour * tx_size * 0.00000001
                hour_btc = hour * tx_size * 0.00000001

                fast_usd = fast_btc * btc_price
                half_hour_usd = half_hour_btc * btc_price
                hour_usd = hour_btc * btc_price

                return (
                    f"🟠 **Bitcoin (BTC)**\n\n"
                    f"⚡ Быстрая (~10 мин): {fast} sat/vB (≈ ${fast_usd:.2f})\n"
                    f"📊 Средняя (~30 мин): {half_hour} sat/vB (≈ ${half_hour_usd:.2f})\n"
                    f"🐌 Медленная (~60 мин): {hour} sat/vB (≈ ${hour_usd:.2f})\n\n"
                    f"💡 Расчет для стандартной транзакции (250 bytes)\n"
                    f"📈 Курс BTC: ${btc_price:,.2f}"
                )
            else:
                return (
                    f"🟠 **Bitcoin (BTC)**\n\n"
                    f"⚡ Быстрая (~10 мин): {fast} sat/vB\n"
                    f"📊 Средняя (~30 мин): {half_hour} sat/vB\n"
                    f"🐌 Медленная (~60 мин): {hour} sat/vB\n\n"
                    f"💡 sat/vB = сатоши за виртуальный байт"
                )
        except Exception as e:
            logger.error(f"Ошибка API Bitcoin: {e}")
            return "❌ Ошибка получения данных Bitcoin"

    async def get_solana_fees(self) -> str:
        """Получение информации о комиссиях Solana"""
        try:
            # Получаем курс SOL
            sol_price = await self.get_token_price("solana")

            fee_sol = 0.000005

            if sol_price:
                fee_usd = fee_sol * sol_price

                return (
                    f"🟢 **Solana (SOL)**\n\n"
                    f"💰 Стандартная комиссия: {fee_sol:.6f} SOL (≈ ${fee_usd:.6f})\n"
                    f"📈 Курс SOL: ${sol_price:.2f}\n\n"
                    f"💡 Фиксированная комиссия для большинства транзакций"
                )
            else:
                return (
                    f"🟢 **Solana (SOL)**\n\n"
                    f"💰 Стандартная комиссия: {fee_sol:.6f} SOL\n\n"
                    f"💡 Фиксированная комиссия для большинства транзакций"
                )
        except Exception as e:
            logger.error(f"Ошибка получения данных Solana: {e}")
            return (
                f"🟢 **Solana (SOL)**\n\n"
                f"💰 Стандартная комиссия: 0.000005 SOL\n\n"
                f"💡 Фиксированная комиссия для большинства транзакций"
            )

    async def get_ton_fees(self) -> str:
        """Получение комиссий TON через Tonapi"""
        try:
            # Получаем цену TON
            ton_price = await self.get_token_price("the-open-network")

            fee_low = 0.005
            fee_standard = 0.01
            fee_high = 0.02

            if ton_price:
                fee_low_usd = fee_low * ton_price
                fee_standard_usd = fee_standard * ton_price
                fee_high_usd = fee_high * ton_price

                return (
                    f"🟣 **TON**\n\n"
                    f"💰 Простая транзакция: ~{fee_low} TON (≈ ${fee_low_usd:.4f})\n"
                    f"📊 Стандартная: ~{fee_standard} TON (≈ ${fee_standard_usd:.4f})\n"
                    f"⚡ Сложная транзакция: ~{fee_high} TON (≈ ${fee_high_usd:.4f})\n\n"
                    f"📈 Курс TON: ${ton_price:.3f}\n"
                    f"💡 Комиссия зависит от сложности транзакции"
                )
            else:
                return (
                    f"🟣 **TON**\n\n"
                    f"💰 Простая транзакция: ~0.005 TON\n"
                    f"📊 Стандартная: ~0.01 TON\n"
                    f"⚡ Сложная транзакция: ~0.02 TON\n\n"
                    f"💡 Очень низкие комиссии за счет архитектуры"
                )
        except Exception as e:
            logger.error(f"Ошибка API TON: {e}")
            return (
                f"🟣 **TON**\n\n"
                f"💰 Стандартная комиссия: ~0.01 TON\n"
                f"📊 Комиссия зависит от сложности транзакции\n\n"
                f"💡 Очень низкие комиссии за счет архитектуры"
            )

    async def get_tron_fees(self) -> str:
        """Получение информации о комиссиях Tron"""
        try:
            # Получаем курс TRX
            trx_price = await self.get_token_price("tron")

            bandwidth_fee = 0.001
            energy_fee = 15

            if trx_price:
                bandwidth_usd = bandwidth_fee * trx_price
                energy_usd = energy_fee * trx_price

                return (
                    f"🔴 **Tron (TRX)**\n\n"
                    f"📡 Обычный перевод: {bandwidth_fee} TRX (≈ ${bandwidth_usd:.6f})\n"
                    f"⚡ Смарт-контракт: ~{energy_fee} TRX (≈ ${energy_usd:.4f})\n\n"
                    f"📈 Курс TRX: ${trx_price:.4f}\n"
                    f"💡 Обычные переводы очень дешевые"
                )
            else:
                return (
                    f"🔴 **Tron (TRX)**\n\n"
                    f"📡 Обычный перевод: 0.001 TRX\n"
                    f"⚡ Смарт-контракт: ~15 TRX\n\n"
                    f"💡 Обычные переводы: очень дешево"
                )
        except Exception as e:
            logger.error(f"Ошибка получения данных Tron: {e}")
            return (
                f"🔴 **Tron (TRX)**\n\n"
                f"📡 Обычный перевод: 0.001 TRX\n"
                f"⚡ Смарт-контракт: ~15 TRX\n\n"
                f"💡 Обычные переводы: очень дешево"
            )

    async def get_polygon_fees(self) -> str:
        """Получение комиссий Polygon через PolygonScan API"""
        try:
            response = requests.get(
                "https://api.polygonscan.com/api?module=gastracker&action=gasoracle",
                timeout=10
            )
            data = response.json()

            if data['status'] == '1':
                safe = float(data['result']['SafeGasPrice'])
                standard = float(data['result']['ProposeGasPrice'])
                fast = float(data['result']['FastGasPrice'])

                # Получаем цену MATIC
                matic_price = await self.get_token_price("matic-network")

                # Стандартная транзакция Polygon ~21000 gas
                gas_limit = 21000

                if matic_price:
                    safe_usd = (safe * gas_limit * 0.000000001) * matic_price
                    standard_usd = (standard * gas_limit * 0.000000001) * matic_price
                    fast_usd = (fast * gas_limit * 0.000000001) * matic_price

                    return (
                        f"🟪 **Polygon (MATIC)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei (≈ ${fast_usd:.5f})\n"
                        f"📊 Стандартная: {standard} Gwei (≈ ${standard_usd:.5f})\n"
                        f"🐌 Безопасная: {safe} Gwei (≈ ${safe_usd:.5f})\n\n"
                        f"💡 Расчет для простого перевода (21k gas)\n"
                        f"📈 Курс MATIC: ${matic_price:.4f}"
                    )
                else:
                    return (
                        f"🟪 **Polygon (MATIC)**\n\n"
                        f"⚡ Быстрая: {fast} Gwei\n"
                        f"📊 Стандартная: {standard} Gwei\n"
                        f"🐌 Безопасная: {safe} Gwei\n\n"
                        f"💡 Обычно 30-150 Gwei для Polygon"
                    )
            else:
                return "❌ Не удалось получить данные Polygon"
        except Exception as e:
            logger.error(f"Ошибка API Polygon: {e}")
            return (
                f"🟪 **Polygon (MATIC)**\n\n"
                f"💰 Стандартная комиссия: ~50-100 Gwei\n"
                f"📊 Комиссия зависит от загрузки сети\n\n"
                f"💡 Намного дешевле Ethereum"
            )

    async def get_arbitrum_fees(self) -> str:
        """Получение комиссий Arbitrum через Arbiscan API"""
        try:
            response = requests.get(
                "https://api.arbiscan.io/api?module=gastracker&action=gasoracle",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == '1' and 'result' in data:
                    safe = int(data['result']['SafeGasPrice'])
                    standard = int(data['result']['ProposeGasPrice'])
                    fast = int(data['result']['FastGasPrice'])

                    # Получаем цену ETH
                    eth_price = await self.get_token_price("ethereum")

                    # Стандартная транзакция ~21000 gas
                    gas_limit = 21000

                    if eth_price:
                        safe_usd = (safe * gas_limit * 0.000000001) * eth_price
                        standard_usd = (standard * gas_limit * 0.000000001) * eth_price
                        fast_usd = (fast * gas_limit * 0.000000001) * eth_price

                        return (
                            f"🔷 **Arbitrum (ETH)**\n\n"
                            f"⚡ Быстрая: {fast} Gwei (≈ ${fast_usd:.5f})\n"
                            f"📊 Стандартная: {standard} Gwei (≈ ${standard_usd:.5f})\n"
                            f"🐌 Безопасная: {safe} Gwei (≈ ${safe_usd:.5f})\n\n"
                            f"💡 Расчет для простого перевода (21k gas)\n"
                            f"📈 Курс ETH: ${eth_price:.2f}"
                        )
                    else:
                        return (
                            f"🔷 **Arbitrum (ETH)**\n\n"
                            f"⚡ Быстрая: {fast} Gwei\n"
                            f"📊 Стандартная: {standard} Gwei\n"
                            f"🐌 Безопасная: {safe} Gwei\n\n"
                            f"💡 L2 решение с низкими комиссиями"
                        )
                else:
                    logger.warning(f"Неожиданный ответ API Arbitrum: {data}")
            else:
                logger.warning(f"HTTP {response.status_code} от API Arbitrum")

        except requests.RequestException as e:
            logger.error(f"Ошибка запроса к API Arbitrum: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка API Arbitrum: {e}")

        # Возвращаем фиксированную информацию при любой ошибке
        eth_price = await self.get_token_price("ethereum")

        if eth_price:
            # Типичные комиссии Arbitrum
            low_gwei = 0.1
            high_gwei = 2.0
            gas_limit = 21000

            low_usd = (low_gwei * gas_limit * 0.000000001) * eth_price
            high_usd = (high_gwei * gas_limit * 0.000000001) * eth_price

            return (
                f"🔷 **Arbitrum (ETH)**\n\n"
                f"💰 Типичная комиссия: 0.1-2 Gwei (≈ ${low_usd:.5f}-${high_usd:.4f})\n"
                f"📊 Очень низкие комиссии благодаря L2\n"
                f"⚡ Быстрые транзакции (~1-2 сек)\n\n"
                f"📈 Курс ETH: ${eth_price:.2f}\n"
                f"💡 Layer 2 решение для Ethereum\n"
                f"🔄 Данные API временно недоступны"
            )
        else:
            return (
                f"🔷 **Arbitrum (ETH)**\n\n"
                f"💰 Типичная комиссия: 0.1-2 Gwei\n"
                f"📊 Очень низкие комиссии благодаря L2\n"
                f"⚡ Быстрые транзакции (~1-2 сек)\n\n"
                f"💡 Layer 2 решение для Ethereum\n"
                f"🔄 Данные API временно недоступны"
            )

    def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        self.application.run_polling(drop_pending_updates=True)

def main():
    # Запускаем keep_alive в отдельном потоке
    threading.Thread(target=keep_alive, daemon=True).start()

    # Создаем и запускаем бота
    bot = BlockchainFeesBot()
    bot.run()

if __name__ == "__main__":
    main()