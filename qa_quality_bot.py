import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# === ЛОГИРОВАНИЕ ===
LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,  # INFO — нормальный уровень, можно поменять на DEBUG
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # дублируем вывод в консоль (видно на Render)
    ]
)
logger = logging.getLogger(__name__)

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
YOUR_CHAT_ID = 473798501
GROUP_CHAT_ID = -1003133537449

if not BOT_TOKEN:
    logger.error("❗ TELEGRAM_TOKEN не задан в переменных окружения. Завершаем работу.")
    raise SystemExit(1)

# === FSM Состояния ===
class ReportStates(StatesGroup):
    date_range = State()
    total = State()
    high = State()
    medium = State()
    low = State()
    reopened = State()
    prod = State()
    risk_zones = State()
    root_causes = State()
    qa_suggestions = State()
    positive_points = State()

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def start(message: types.Message):
    logger.info(f"/start от {message.from_user.full_name} (ID {message.from_user.id})")
    await message.answer("👋 Привет! Я QA Quality Bot.\nНапиши /report чтобы создать новый QA-отчёт.")

@dp.message(Command("report"))
async def report_start(message: types.Message, state: FSMContext):
    logger.info(f"/report от {message.from_user.full_name} (ID {message.from_user.id})")
    if message.chat.id != YOUR_CHAT_ID:
        await message.answer("⚠️ Этот режим доступен только в личном чате с ботом.")
        logger.warning(f"Попытка доступа к /report от чужого ID: {message.chat.id}")
        return

    await message.answer("📅 Укажи диапазон дат отчёта (например: 14–18 октября):")
    await state.set_state(ReportStates.date_range)

# === Остальные шаги FSM ===
@dp.message(ReportStates.date_range)
async def get_date_range(message: types.Message, state: FSMContext):
    await state.update_data(date_range=message.text)
    await message.answer("🪲 Сколько всего багов?")
    await state.set_state(ReportStates.total)

@dp.message(ReportStates.total)
async def get_total(message: types.Message, state: FSMContext):
    await state.update_data(total=message.text)
    await message.answer("🚨 Сколько High?")
    await state.set_state(ReportStates.high)

@dp.message(ReportStates.high)
async def get_high(message: types.Message, state: FSMContext):
    await state.update_data(high=message.text)
    await message.answer("🧩 Сколько Medium?")
    await state.set_state(ReportStates.medium)

@dp.message(ReportStates.medium)
async def get_medium(message: types.Message, state: FSMContext):
    await state.update_data(medium=message.text)
    await message.answer("🪶 Сколько Low?")
    await state.set_state(ReportStates.low)

@dp.message(ReportStates.low)
async def get_low(message: types.Message, state: FSMContext):
    await state.update_data(low=message.text)
    await message.answer("🔁 Сколько повторных?")
    await state.set_state(ReportStates.reopened)

@dp.message(ReportStates.reopened)
async def get_reopened(message: types.Message, state: FSMContext):
    await state.update_data(reopened=message.text)
    await message.answer("🧨 Сколько найдено на проде?")
    await state.set_state(ReportStates.prod)

@dp.message(ReportStates.prod)
async def get_prod(message: types.Message, state: FSMContext):
    await state.update_data(prod=message.text)
    await message.answer("⚠️ Опиши зоны риска:")
    await state.set_state(ReportStates.risk_zones)

@dp.message(ReportStates.risk_zones)
async def get_risk_zones(message: types.Message, state: FSMContext):
    await state.update_data(risk_zones=message.text)
    await message.answer("🧠 Основные причины?")
    await state.set_state(ReportStates.root_causes)

@dp.message(ReportStates.root_causes)
async def get_root_causes(message: types.Message, state: FSMContext):
    await state.update_data(root_causes=message.text)
    await message.answer("🧰 Предложения QA:")
    await state.set_state(ReportStates.qa_suggestions)

@dp.message(ReportStates.qa_suggestions)
async def get_suggestions(message: types.Message, state: FSMContext):
    await state.update_data(qa_suggestions=message.text)
    await message.answer("✅ Позитив недели:")
    await state.set_state(ReportStates.positive_points)

@dp.message(ReportStates.positive_points)
async def get_positive(message: types.Message, state: FSMContext):
    data = await state.get_data()

    report = f"""
📅 QA Quality Report — {data['date_range']}

📊 Статистика
🪲 Всего багов: {data['total']}
🚨 High: {data['high']} | 🧩 Medium: {data['medium']} | 🪶 Low: {data['low']}
🔁 Повторные: {data['reopened']} | 🧨 Прод: {data['prod']}

⚠️ Зоны риска
{data['risk_zones']}

🧠 Основные причины
{data['root_causes']}

🧰 Предложения QA
{data['qa_suggestions']}

✅ Позитив недели
{message.text}
"""

    await bot.send_message(GROUP_CHAT_ID, report)
    await message.answer("🚀 Отчёт успешно сформирован и отправлен в общий чат отдела!")
    await state.clear()
    logger.info(f"✅ Отчёт отправлен в группу {GROUP_CHAT_ID} от {message.from_user.full_name}")

# === Render Fix ===
if os.environ.get("RENDER"):
    import threading
    from http.server import SimpleHTTPRequestHandler, HTTPServer

    def _start_simple_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
        logger.info(f"✅ Fake HTTP server started on port {port} (for Render health check)")
        try:
            server.serve_forever()
        except Exception as e:
            logger.error(f"Fake server stopped: {e}")

    threading.Thread(target=_start_simple_server, daemon=True).start()

# === Запуск бота ===
async def main():
    logger.info("🤖 Бот запущен и готов к работе...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"❌ Ошибка во время работы бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())