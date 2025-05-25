import datetime
import asyncio
import random
import re
import aiohttp
import webbrowser
from urllib.parse import quote
import spacy
from textblob import TextBlob
import sqlite3
import pymorphy2

# Константы для цветов (ANSI)
COLORS = {
    "blue": "\033[94m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "bold": "\033[1m",
    "underline": "\033[4m",
    "end": "\033[0m",
}

# Загрузка spaCy модели
try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    print(f"{COLORS['yellow']}Загружаю модель ru_core_news_sm...{COLORS['end']}")
    from spacy.cli import download
    download("ru_core_news_sm")
    nlp = spacy.load("ru_core_news_sm")

# Конфигурация
API_KEY = "7dd0df264a23133ea2050760446d22d5"  # Замените на действительный ключ OpenWeatherMap

# Словарь шаблонов и ответов
RESPONSES = {
    r"как тебя зовут\??": [
        f"{COLORS['blue']}Я ваш виртуальный помощник — Бот-Ассистент!{COLORS['end']}",
        f"{COLORS['blue']}Меня зовут Бот, рад знакомству!{COLORS['end']}",
        f"{COLORS['blue']}Я — ваш цифровой помощник, просто называйте меня Бот.{COLORS['end']}"
    ],
    r"как дела\??": [
        f"{COLORS['green']}Всё отлично, спасибо что спросили! 😊{COLORS['end']}",
        f"{COLORS['green']}Работаю в штатном режиме, готов помочь!{COLORS['end']}",
        f"{COLORS['green']}Как у цифрового существа — прекрасно! А у вас?{COLORS['end']}"
    ],
    r"что ты умеешь\??": [
        f"""{COLORS['blue']}╔══════════════════════════════════╗
║  {COLORS['bold']}Мои возможности:{COLORS['end']}{COLORS['blue']}           ║
╠══════════════════════════════════╣
║ • Отвечать на вопросы            ║
║ • Искать информацию в интернете  ║
║ • Показывать погоду              ║
║ • Рассказывать интересные факты  ║
║ • Выполнять простые вычисления   ║
╚══════════════════════════════════╝{COLORS['end']}""",
        f"""{COLORS['blue']}Я могу:
  • {COLORS['underline']}Найти информацию{COLORS['end']}{COLORS['blue']} в интернете
  • {COLORS['underline']}Рассказать факты{COLORS['end']}{COLORS['blue']} о спорте, истории, космосе
  • {COLORS['underline']}Показать погоду{COLORS['end']}{COLORS['blue']} в любом городе
  • {COLORS['underline']}Решить примеры{COLORS['end']}{COLORS['blue']} типа 2+2 или 5*10{COLORS['end']}"""
    ],
    r"сколько сейчас время\??": lambda: f"{COLORS['yellow']}⏰ Текущее время: {datetime.datetime.now().strftime('%H:%M:%S')}{COLORS['end']}",
    r"какое сегодня число\??": lambda: f"{COLORS['yellow']}📅 Сегодня: {datetime.date.today().strftime('%d.%m.%Y')}{COLORS['end']}",
    r"расскажи интересную шутку": [
        f"""{COLORS['blue']}Выберите категорию:{COLORS['end']}
  • Технологии{COLORS['end']}
  • Животные{COLORS['end']}
  • Школа{COLORS['end']}
  • Работа{COLORS['end']}""",
        f"{COLORS['blue']}О какой сфере вам рассказать факт? (спорт/история/космос){COLORS['end']}"
    ],
    r"еще один факт": [
        f"{COLORS['blue']}Выберите категорию для нового факта: (спорт/история/космос){COLORS['end']}",
        f"{COLORS['blue']}Из какой области вам интересен факт?{COLORS['end']}"
    ],
    r"поиск\s(.+)": [
        f"{COLORS['yellow']}🔍 Выполняю поиск в интернете...{COLORS['end']}",
        f"{COLORS['yellow']}🌐 Запускаю поиск по вашему запросу...{COLORS['end']}"
    ],
    r"погода\s+(?:в|на)\s+(.+)": [
        f"{COLORS['yellow']}⛅ Запрашиваю данные о погоде...{COLORS['end']}",
        f"{COLORS['yellow']}🌤️ Узнаю текущие погодные условия...{COLORS['end']}"
    ],
    r"\bпривет\b": [
        f"{COLORS['green']}✨ Привет-привет! Как ваши дела?{COLORS['end']}",
        f"{COLORS['green']}👋 Здравствуйте! Чем могу помочь?{COLORS['end']}",
        f"{COLORS['green']}🌟 Йоу! Рад вас видеть!{COLORS['end']}"
    ],
    r"\bнастоящий\b|\bживой\b|\bчеловек\b": [
        f"{COLORS['blue']}🤖 Пока только виртуальный, но с большими амбициями!{COLORS['end']}",
        f"{COLORS['blue']}👾 Я цифровой помощник, но уже почти человек!{COLORS['end']}"
    ],
    r"\bспасибо\b|\bблагодарить\b": [
        f"{COLORS['green']}🌸 Всегда рад помочь! Обращайтесь ещё!{COLORS['end']}",
        f"{COLORS['green']}💖 Пожалуйста! Чем ещё могу быть полезен?{COLORS['end']}"
    ],
    r"\bпока\b|\bсвидания\b": [
        f"{COLORS['blue']}🌈 До новых встреч! Хорошего дня!{COLORS['end']}",
        f"{COLORS['blue']}👋 Пока-пока! Возвращайтесь скорее!{COLORS['end']}"
    ],
    r"\bдело\b|\bновый\b": [
        f"{COLORS['green']}☀️ Всё прекрасно, спасибо что интересуетесь!{COLORS['end']}",
        f"{COLORS['green']}🚀 Всё отлично! Готов к новым задачам!{COLORS['end']}"
    ],
    r"\bуметь\b": [
        f"""{COLORS['blue']}Мои основные навыки:
  • {COLORS['underline']}Поиск информации{COLORS['end']}{COLORS['blue']} в интернете
  • {COLORS['underline']}Ответы на вопросы{COLORS['end']}{COLORS['blue']}
  • {COLORS['underline']}Математические вычисления{COLORS['end']}{COLORS['blue']}
  • {COLORS['underline']}Погодные сводки{COLORS['end']}{COLORS['blue']}
  • {COLORS['underline']}Интересные факты{COLORS['end']}{COLORS['blue']}{COLORS['end']}"""
    ],
}

# Словарь фактов по категориям
JOKES = {
    "технологии": [
        f"💻 Почему программисты любят тишину? Потому что в ней нет багов.{COLORS['end']}",
        f"🖱️ Компьютер говорит с человеком только на одном языке — языке ошибок.{COLORS['end']}",
        f"🔋 Мой телефон живёт дольше меня… только когда я его не трогаю.{COLORS['end']}"
    ],
    "животные": [
        f"🐶 Почему собака сидит у компьютера? Она ищет кота в интернете.{COLORS['end']}",
        f"🐱 Кот проснулся, посмотрел на будильник и снова лёг… мудрость в чистом виде.{COLORS['end']}",
        f"🦜 Попугай выучил «Скорую помощь» и теперь звонит туда каждый раз, когда хочет яблоко.{COLORS['end']}"
    ],
    "работа": [
        f"📅 Я не ленивый — я просто в режиме энергосбережения.{COLORS['end']}",
        f"🕘 Я люблю дедлайны. Особенно звук, с которым они пролетают мимо.{COLORS['end']}",
        f"💼 Когда я говорил, что могу работать под давлением, я не имел в виду весь отдел кадров.{COLORS['end']}"
    ],
    "школа": [
        f"📚 Учил географию и узнал, что я далеко не в центре мира.{COLORS['end']}",
        f"🧪 Химия — это магия, но с двойкой.{COLORS['end']}",
        f"📝 Экзамен — это способ доказать, что ты всё равно ничего не запомнил.{COLORS['end']}"
    ]
}

class Database:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    city TEXT
                )
            ''')
            conn.commit()

    def add_user(self, name: str, city: str):
        """Добавление нового пользователя"""
        with self._get_connection() as conn:
            conn.execute('INSERT INTO users (name, city) VALUES (?, ?)', (name, city))
            conn.commit()

    def get_all_users(self):
        """Получение всех пользователей"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, city FROM users')
            return cursor.fetchall()

    def update_user(self, user_id=1, name=None, city=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO users (id, name, city) VALUES (?, ?, ?)',
                             (user_id, name or '', city or ''))
            else:
                updates = []
                params = []
                if name is not None:
                    updates.append('name = ?')
                    params.append(name)
                if city is not None:
                    updates.append('city = ?')
                    params.append(city)
                if updates:
                    query = 'UPDATE users SET ' + ', '.join(updates) + ' WHERE id = ?'
                    params.append(user_id)
                    cursor.execute(query, params)
            conn.commit()

    def get_user(self, user_id=1):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, city FROM users WHERE id = ?', (user_id,))
            return cursor.fetchone()

def print_welcome():
    print(f"""{COLORS['blue']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                 🤖 {COLORS['bold']}ПРИВЕТ! Я ТВОЙ УМНЫЙ ПОМОЩНИК-ЧАТ-БОТ{COLORS['end']}{COLORS['blue']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                                📌 Вот что я умею:

   • Показать текущую погоду в твоём или любом городе - "погода в (город)"
   • Запомнить твоё имя и город - "(имя) живёт в (город)"
   • Вывести список всех пользователей - "Список пользователей"
   • Найти информацию в интернете - "поиск (информация)
   • Рассказать интересный факт - "Расскажи факт"
   • Выполнить простые вычисления - "Введи выражение"

🛑                    {COLORS['green']}Введи "выход" чтобы завершить разговор {COLORS['blue']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COLORS['end']}""")
def calculate_expression(expr: str) -> str:
    """Безопасное вычисление математического выражения"""
    try:
        expr = expr.replace('x', '*').replace('×', '*').replace('÷', '/')
        result = eval(expr, {"__builtins__": {}}, {"__builtins__": {}})
        return f"{COLORS['green']}🧮 Результат: {expr} = {result}{COLORS['end']}"
    except (SyntaxError, ZeroDivisionError, ValueError):
        return f"{COLORS['red']}❌ Неверное или небезопасное выражение.{COLORS['end']}"

def search_internet(query: str) -> str:
    """Поиск в интернете через Google"""
    try:
        url = f"https://www.google.com/search?q={quote(query)}"
        webbrowser.open(url)
        return f"{COLORS['blue']}🌍 Выполнен поиск в Google: '{query}'."
    except Exception as e:
        return f"{COLORS['red']}⚠ Не удалось открыть браузер: {str(e)}{COLORS['end']}"

async def analyze_mood(text: str) -> str:
    """Асинхронный анализ настроения с переводом"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                'q': text,
                'langpair': 'ru|en',
                'de': 'example@example.com'
            }
            async with session.get('https://api.mymemory.translated.net/get', params=params) as response:
                if response.status != 200:
                    return f"{COLORS['yellow']}🤔 Ошибка при переводе текста.{COLORS['end']}"
                data = await response.json()
                translated = data['responseData']['translatedText']

        analysis = TextBlob(translated).sentiment
        if analysis.polarity > 0.3:
            return f"{COLORS['green']}😊 Вы звучите позитивно!{COLORS['end']}"
        elif analysis.polarity < -0.3:
            return f"{COLORS['blue']}😔 Кажется, у вас трудный день.{COLORS['end']}"
        return f"{COLORS['yellow']}😐 Нейтральное настроение.{COLORS['end']}"
    except Exception as e:
        return f"{COLORS['yellow']}🤔 Не могу определить настроение: {str(e)}{COLORS['end']}"

class WeatherAssistant:
    async def get_weather(self, city: str) -> str:
        """Асинхронное получение погоды"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={quote(city)}&appid={API_KEY}&units=metric&lang=ru"
                async with session.get(url) as response:
                    if response.status != 200:
                        return f"{COLORS['red']}⚠ Город '{city}' не найден или ошибка API.{COLORS['end']}"
                    data = await response.json()
                    temp = data["main"]["temp"]
                    weather_desc = data["weather"][0]["description"]
                    return f"{COLORS['blue']}⛅ В {city.capitalize()} сейчас {weather_desc}, температура {temp}°C{COLORS['end']}"
        except Exception as e:
            return f"{COLORS['red']}⚠ Ошибка получения погоды: {str(e)}{COLORS['end']}"

def log_conversation(user_input: str, bot_response: str):
    """Логирование диалога в файл"""
    try:
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
            f.write(f"Пользователь: {user_input}\n")
            f.write(f"Бот: {bot_response}\n")
            f.write("-" * 60 + "\n")
    except Exception as e:
        print(f"{COLORS['red']}⚠ Ошибка логирования: {str(e)}{COLORS['end']}")

async def process_user_input(user_input: str, current_category: str = None, db: Database = None) -> tuple:
    """Асинхронная обработка ввода пользователя"""
    user_input = user_input.lower().strip()

    # Выход
    if user_input in ("выход", "стоп"):
        return None, f"{COLORS['blue']}👋 До свидания!{COLORS['end']}", False

    morph = pymorphy2.MorphAnalyzer()
    def to_nominative(word: str) -> str:
        parses = morph.parse(word)
        for p in parses:
            if 'nomn' in p.tag:
                return p.word
        # Если нормальной формы в nomn нет — возвращаем normal_form
        return parses[0].normal_form

    user_match = re.match(r"(\w+)\s+жив[ёе]т\s+в\s+(.+)", user_input, re.IGNORECASE)
    if user_match:
        name = user_match.group(1).capitalize()
        city_raw = user_match.group(2).rstrip('.,!?')
        city_parts = city_raw.split()
        city_lemmas = [to_nominative(word).capitalize() for word in city_parts]
        city = ' '.join(city_lemmas)

        await asyncio.to_thread(db.add_user, name, city)
        return None, f"{COLORS['green']}✅ Пользователь {name} из {city} добавлен!{COLORS['end']}", False

    # Показать всех пользователей
    if re.fullmatch(r"(список|показать)\s+пользователей", user_input, re.IGNORECASE):
        users = await asyncio.to_thread(db.get_all_users)
        if not users:
            return None, f"{COLORS['yellow']}📭 Список пользователей пуст.{COLORS['end']}", False

        weather = WeatherAssistant()

        # Собираем данные асинхронно
        async def get_user_data(user):
            user_id, name, city = user
            try:
                weather_info = await weather.get_weather(city)
                temp = re.search(r'температура ([\d-]+)', weather_info).group(1)
                desc = re.search(r'сейчас (.*?),', weather_info).group(1)
                return (user_id, name, city, f"{desc}, {temp}°C")
            except:
                return (user_id, name, city, "Нет данных")

        tasks = [get_user_data(user) for user in users]
        user_data = await asyncio.gather(*tasks)

        # Форматирование таблицы
        def format_users_table(user_data):
            headers = ["ID", "Имя", "Город", "Погода"]
            col_widths = [4, 12, 18, 60]

            top_border = f"┌{'─' * col_widths[0]}┬{'─' * col_widths[1]}┬{'─' * col_widths[2]}┬{'─' * col_widths[3]}┐"
            header_sep = f"├{'─' * col_widths[0]}┼{'─' * col_widths[1]}┼{'─' * col_widths[2]}┼{'─' * col_widths[3]}┤"
            bottom_border = f"└{'─' * col_widths[0]}┴{'─' * col_widths[1]}┴{'─' * col_widths[2]}┴{'─' * col_widths[3]}┘"

            header_line = (
                f"│{COLORS['bold']}{headers[0]:^{col_widths[0]}}{COLORS['end']}│"
                f"{COLORS['bold']}{headers[1]:^{col_widths[1]}}{COLORS['end']}│"
                f"{COLORS['bold']}{headers[2]:^{col_widths[2]}}{COLORS['end']}│"
                f"{COLORS['bold']}{headers[3]:^{col_widths[3]}}{COLORS['end']}│"
            )

            rows = []
            for data in user_data:
                row = (
                    f"│{str(data[0]):^{col_widths[0]}}│"
                    f"{data[1]:<{col_widths[1]}}│"
                    f"{data[2]:<{col_widths[2]}}│"
                    f"{data[3]:<{col_widths[3]}}│"
                )
                rows.append(row)

            return "\n".join([top_border, header_line, header_sep] + rows + [bottom_border])

        table = format_users_table(user_data)
        return None, f"\n{COLORS['blue']}📊 Список пользователей:\n{table}{COLORS['end']}", False

    user_match = re.match(r"(\w+)\s+жив[ёе]т\s+в\s+(.+)", user_input, re.IGNORECASE)
    if user_match:
        name = user_match.group(1).capitalize()
        city_raw = user_match.group(2).rstrip('.,!?')
        # Приводим каждое слово в названии города к нормальной форме
        city_parts = city_raw.split()
        city_lemmas = [morph.parse(word)[0].normal_form for word in city_parts]
        city = ' '.join([w.capitalize() for w in city_lemmas])

        await asyncio.to_thread(db.add_user, name, city)
        return None, f"{COLORS['green']}✅ Пользователь {name} из {city} добавлен!{COLORS['end']}", False

        # Показать мои данные
    if re.fullmatch(r"мои данные", user_input, re.IGNORECASE):
        user_data = await asyncio.to_thread(db.get_user)
        if user_data:
            name = user_data[0] or "не указано"
            city = user_data[1] or "не указан"
            response = f"{COLORS['blue']}📝 Ваши данные:\nИмя: {name}\nГород: {city}{COLORS['end']}"
        else:
            response = f"{COLORS['yellow']}⚠ Данные не найдены.{COLORS['end']}"
        return None, response, False

        # Обработка погоды
        weather_match = re.match(r"погода(?:\s+(?:в|на)\s+(.+))?$", user_input, re.IGNORECASE)
        if weather_match:
            city = weather_match.group(1)
            if not city:
                user_data = await asyncio.to_thread(db.get_user)
                city = user_data[1] if user_data else None
                if not city:
                    return None, f"{COLORS['red']}⚠ Укажите город или сохраните его командой 'мой город ...'.{COLORS['end']}", False
            weather = WeatherAssistant()
            weather_result = await weather.get_weather(city)
            return None, weather_result, False

    # Обработка категорий шуток
    if current_category:
        if user_input in JOKES:
            return None, random.choice(JOKES[user_input]), False
        return None, f"{COLORS['red']}🚫 Неизвестная категория. Попробуйте: технологии, животные, работа, школа.{COLORS['end']}", False



    # Проверка математических выражений
    math_expr = re.search(r"([-+]?\d*\.?\d+\s*[+\-*/x×÷]\s*[-+]?\d*\.?\d+)", user_input)
    if math_expr:
        return None, calculate_expression(math_expr.group(0)), False

    # Поиск в интернете
    search_match = re.search(r"поиск\s+(.+)", user_input)
    if search_match:
        query = search_match.group(1)
        return None, search_internet(query), False

    # Погода
    weather_match = re.search(r"погода\s+(?:в|на)\s+(.+)", user_input)
    if weather_match:
        city_raw = weather_match.group(1).rstrip('.,!?')
        city_parts = city_raw.split()
        city_lemmas = [to_nominative(word).capitalize() for word in city_parts]
        city = ' '.join(city_lemmas)
        weather = WeatherAssistant()
        weather_result = await weather.get_weather(city)
        return None, weather_result, False

    # Факты
    if "шутк" in user_input:
        return "fact_category", random.choice(RESPONSES[r"расскажи интересную шутку"]), True

    # Обработка специальных команд
    for pattern, response in RESPONSES.items():
        if re.search(pattern, user_input):
            if callable(response):
                return None, response(), False
            elif isinstance(response, list):
                return None, random.choice(response), False
            return None, response, False

    # Анализ настроения для неизвестных фраз
    return None, await analyze_mood(user_input), False


async def main():
    """Основная асинхронная функция"""
    db = Database()
    db._create_table()  # Создаём таблицу при запуске
    print_welcome()
    current_category = None

    while True:
        try:
            user_input = await asyncio.to_thread(input, f"{COLORS['bold']}Вы:{COLORS['end']} ")
            new_category, response, set_category = await process_user_input(user_input, current_category, db)

            if response is None:
                break

            print(f"\n{COLORS['blue']}Бот:{COLORS['end']} {response}\n")
            log_conversation(user_input, response)

            current_category = new_category if set_category else None

        except (KeyboardInterrupt, asyncio.CancelledError):
            print(f"\n{COLORS['red']}🛑 Диалог прерван.{COLORS['end']}")
            break
            break
        except Exception as e:
            print(f"{COLORS['red']}⚠ Ошибка: {str(e)}{COLORS['end']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{COLORS['red']}🛑 Программа завершена.{COLORS['end']}")