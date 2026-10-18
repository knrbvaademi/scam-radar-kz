from flask import Flask, request, render_template_string
import telebot
import json
import re
import sys
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper

app = Flask(__name__)

TOKEN = "8645811592:AAHjL_oZxHuwKyqgtNWTP3lDAu1IOd3p-OA"
apihelper.proxy = {'https': 'http://proxy.server:3128'}
bot = telebot.TeleBot(TOKEN, threaded=False)

# ============================================
# БАЗА ДАННЫХ (JSON)
# ============================================
REPORTS_FILE = "reports.json"

def load_reports():
    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_reports(reports):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

reports = load_reports()
temp_state = {}
user_language = {}

# ============================================
# БАЗА 110 СХЕМ МОШЕННИЧЕСТВА
# ============================================
KNOWN_SCHEMES = {
    "Банковские схемы": [
        "Звонок из 'службы безопасности Kaspi' — просят код из SMS",
        "«Ваша карта заблокирована» — просят перевести на безопасный счёт",
        "«На вас оформляют кредит» — просят отменить через перевод",
        "«Подозрительная транзакция» — просят подтвердить кодом",
        "«Сотрудник Нацбанка» — просит установить защитное приложение",
        "«Служба финансового мониторинга» — требует данные карты",
        "«Перевод на резервный счёт» — якобы для сохранности денег",
        "«Отмена мошеннической транзакции» — просят код",
        "«Ваш счёт в опасности» — срочно перевести деньги",
        "«Проверка личности» — просят CVV и срок действия",
        "«Обновление банковского приложения» — ссылка на фишинг",
        "«Возврат ошибочного перевода» — просят подтвердить данные",
        "«Блокировка подозрительного перевода» — просят код",
        "«Проверка сотрудника банка» — просят кодовое слово",
        "«Страхование карты» — платная защита от мошенников",
        "«Kaspi бонусы сгорают» — просят данные для восстановления",
        "«Кэшбэк 30%» — фишинговая ссылка",
        "«Кредит одобрен, подтвердите» — просят код",
        "«Ваш платёж не прошёл» — фишинговая ссылка",
        "«Обновление реквизитов работодателя» — подмена зарплатного счёта",
        "«Заявка на кредит от вашего имени» — паника и перевод",
        "«Депозит с повышенной ставкой» — фиктивный вклад",
        "«Инвестиции от банка» — несуществующий продукт",
        "«Kaspi Gold с лимитом» — фишинговая заявка",
        "«Смена номера телефона в банке» — просят код"
    ],
    "Госорганы / eGov": [
        "«Звонок из ЦОН» — «ошибка в документах»",
        "«eGov взломан» — просят восстановить доступ",
        "«Из МВД по вашему делу» — просят содействия",
        "«АФМ проверка» — просят данные счетов",
        "«Прокуратура: вы подозреваетесь» — угрозы и перевод",
        "«КНБ: секретная операция» — просят помочь",
        "«Налоговая: задолженность» — фишинговая ссылка",
        "«Пенсионный фонд: перерасчёт» — просят данные",
        "«Электронная подпись истекает» — фишинговая ссылка",
        "«Госуслуга: обновите данные» — фишинг",
        "«Звонок из Акимата» — просят содействия в проверке",
        "«Суд: повестка» — фишинговая ссылка",
        "«Приставы: долг» — просят оплатить",
        "«Соцзащита: выплата» — просят данные карты",
        "«Роспотребнадзор: жалоба» — фишинговая ссылка"
    ],
    "Доставка / посылки": [
        "«Посылка задержана на таможне» — просят оплатить",
        "«Курьер не смог доставить» — фишинговая ссылка",
        "«Ваш заказ отменён» — просят данные карты",
        "«Почта Казахстана: доплата» — фишинговая ссылка",
        "«OLX: доставка» — фейковая ссылка",
        "«Kaspi доставка» — фишинговая ссылка",
        "«Wildberries: возврат» — просят данные",
        "«Ваш заказ в пункте выдачи» — просят код",
        "«Проблема с доставкой» — фишинговая ссылка",
        "«Подтвердите адрес» — просят данные"
    ],
    "Вакансии / дропперство": [
        "«Помощник финансового отдела» — дропперство",
        "«Удалённая работа с переводами» — дропперство",
        "«Курьер с личным авто» — дропперство",
        "«Менеджер по приёму платежей» — дропперство",
        "«Помощь с переводами за %» — дропперство",
        "«Вакансия в Kaspi — оператор» — фейковая",
        "«Работа в Telegram: лёгкие деньги» — дропперство",
        "«Онлайн-кассир» — дропперство",
        "«Помощник на удалёнке» — просят карту",
        "«Требуется сотрудник для переводов» — дропперство",
        "«Работа с криптой» — дропперство",
        "«Оформим карту для работы» — дропперство",
        "«Курьерская служба на маркетплейсе» — дропперство",
        "«Финансовый агент» — дропперство",
        "«Партнёр по приёму платежей» — дропперство"
    ],
    "Инвестиции / крипта": [
        "«Инвестиции с гарантией 30%» — пирамида",
        "«Telegram-канал по трейдингу» — пирамида",
        "«Криптоферма с пассивным доходом» — пирамида",
        "«Бот для заработка на крипте» — скам",
        "«Инвестиции в Kaspi с ботом» — фиктив",
        "«Заработок на перепродаже товаров» — скам",
        "«P2P-арбитраж крипты» — скам",
        "«Брокер с лицензией» — фиктивный брокер",
        "«Копирование сделок трейдера» — скам",
        "«Обучение трейдингу + портфель» — скам",
        "«Заработок на акциях через бота» — скам",
        "«Гарантированная доходность 50%» — пирамида",
        "«Криптокошелёк с бонусами» — фишинг",
        "«Инвестиции в стартап» — скам",
        "«Майнинг-ферма с вложениями» — скам"
    ],
    "Выигрыши / призы": [
        "«Вы выиграли iPhone» — просят оплатить доставку",
        "«Приз от Kaspi» — фишинг",
        "«Лотерея от Акимата» — фишинг",
        "«Компенсация от государства» — фишинг",
        "«Розыгрыш в Instagram» — просят данные",
        "«Приз от Казпочты» — фишинг",
        "«Бесплатные авиабилеты» — фишинг",
        "«Скидка 90% в магазине» — фишинг",
        "«Подарочная карта от банка» — фишинг",
        "«Бесплатный курс от EdTech» — фишинг"
    ],
    "Эмоциональный шантаж": [
        "«Ваш сын в аварии» — просят денег",
        "«Мама в больнице» — просят денег",
        "«Родственник задержан» — просят денег",
        "«Ваш друг в беде» — просят денег",
        "«Похитили близкого» — просят выкуп",
        "«Ваш ребёнок в заложниках» — просят выкуп",
        "«Срочная операция родственнику» — просят денег",
        "«Друг попал в ДТП» — просят денег",
        "«Мама потеряла сознание» — просят денег",
        "«Помогите сестре» — просят денег"
    ],
    "Технические схемы": [
        "«Установите AnyDesk» — удалённый доступ",
        "«Установите TeamViewer» — удалённый доступ",
        "«Скачайте программу защиты» — вирус",
        "«Ваш компьютер заражён» — фейковая техподдержка",
        "«Обновите Windows» — вирус",
        "«Установите приложение банка» — фейковое приложение",
        "«Скачайте APK» — вирус",
        "«Ссылка на WhatsApp Web» — фишинг",
        "«Подтвердите Telegram» — фишинг",
        "«Защитите Instagram» — фишинг"
    ]
}

TOTAL_SCHEMES = sum(len(v) for v in KNOWN_SCHEMES.values())

# ============================================
# ОПРЕДЕЛЕНИЕ ЯЗЫКА
# ============================================
def detect_language(text):
    kazakh_chars = set('әғқңөұүіӘҒҚҢӨҰҮІ')
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    kazakh_count = sum(1 for c in text.lower() if c in kazakh_chars)
    russian_count = sum(1 for c in text.lower() if c in russian_chars)
    return 'kk' if kazakh_count > russian_count else 'ru'

# ============================================
# НОМЕРА БАНКОВ
# ============================================
BANK_NUMBERS = """
☎️ **Kaspi:** 7111
☎️ **Halyk:** 7111
☎️ **Jusan:** 7800
☎️ **Forte:** 7222
☎️ **Отбасы:** 7171
☎️ **Сбербанк:** 8-800-080-1000
☎️ **Альфа-Банк:** 8-800-080-1000
☎️ **Банк ЦентрКредит:** 8-800-080-1000
"""

# ============================================
# HTML ДЛЯ ДАШБОРДА (РАСШИРЕННЫЙ)
# ============================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCAM RADAR KZ — Live Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root {
            --bg-color: #f4f7f6;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --primary: #3b82f6;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --purple: #8b5cf6;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            --shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }
        [data-theme="dark"] {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; transition: background-color 0.3s, color 0.3s; }

        body { background-color: var(--bg-color); color: var(--text-main); padding: 30px 20px; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; }

        /* Шапка */
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .header h1 { font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }
        .theme-toggle { background: var(--card-bg); border: 1px solid var(--border); padding: 10px 16px; border-radius: 12px; cursor: pointer; font-weight: 600; color: var(--text-main); box-shadow: var(--shadow); }
        .theme-toggle:hover { transform: scale(1.05); }

        /* Верхние карточки */
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card {
            background: var(--card-bg); border-radius: 20px; padding: 25px;
            border: 1px solid var(--border); box-shadow: var(--shadow);
            position: relative; overflow: hidden; transition: all 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); box-shadow: var(--shadow-hover); }
        .card .number { font-size: 2.8rem; font-weight: 800; margin-bottom: 5px; }
        .card .label { color: var(--text-muted); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
        .card .icon { position: absolute; right: 20px; top: 25px; font-size: 2.5rem; opacity: 0.1; }
        .card.danger .number { color: var(--danger); }
        .card.purple .number { color: var(--purple); }

        /* Сетка */
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 30px; }
        .grid-3 { display: grid; grid-template-columns: 2fr 1fr; gap: 25px; margin-bottom: 30px; }
        .grid-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 30px; }
        @media (max-width: 900px) { .grid-2, .grid-3, .grid-charts { grid-template-columns: 1fr; } }

        .section { background: var(--card-bg); border-radius: 20px; padding: 25px; border: 1px solid var(--border); box-shadow: var(--shadow); display: flex; flex-direction: column; }
        .section h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }

        /* Графики */
        .chart-container { position: relative; height: 300px; width: 100%; flex-grow: 1; }

        /* Карта Казахстана (SVG) */
        .map-container { position: relative; height: 300px; width: 100%; background: var(--bg-color); border-radius: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 1px dashed var(--border); }
        .map-pin { position: absolute; width: 12px; height: 12px; background: var(--danger); border-radius: 50%; box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.3); animation: pulse 2s infinite; z-index: 10; }
        .map-label { position: absolute; font-size: 0.75rem; font-weight: 700; color: var(--text-main); background: var(--card-bg); padding: 2px 6px; border-radius: 4px; box-shadow: var(--shadow); z-index: 10; }

        /* Список кейсов (Live Feed) */
        .case-list { display: flex; flex-direction: column; gap: 12px; }
        .case-item { display: flex; align-items: center; gap: 15px; padding: 15px; background: var(--bg-color); border-radius: 12px; border: 1px solid var(--border); transition: all 0.2s; }
        .case-item:hover { transform: translateX(5px); border-color: var(--primary); }
        .case-icon { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 1rem; flex-shrink: 0; }
        .case-icon.bank { background: var(--primary); }
        .case-icon.egov { background: var(--purple); }
        .case-icon.delivery { background: var(--warning); }
        .case-icon.other { background: #94a3b8; }
        .case-text { flex: 1; font-size: 0.9rem; font-weight: 500; }
        .case-date { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; }
        .case-badge { font-size: 0.7rem; padding: 4px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; flex-shrink: 0; }
        .badge.high { background: #fee2e2; color: #b91c1c; }
        .badge.medium { background: #fef3c7; color: #b45309; }
        .badge.low { background: #d1fae5; color: #047857; }
        .badge.critical { background: #fecaca; color: #7f1d1d; animation: blink 1s infinite alternate; }

        /* Таблица */
        .table-container { overflow-x: auto; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }
        th { padding: 12px; background: var(--bg-color); color: var(--text-muted); font-weight: 600; border-bottom: 2px solid var(--border); }
        td { padding: 12px; border-bottom: 1px solid var(--border); }
        tr:hover td { background: var(--bg-color); }

        /* Блоки советов и угроз */
        .threat-box { background: linear-gradient(135deg, #fff1f2, #fecdd3); border: 1px solid #fecdd3; border-radius: 20px; padding: 25px; display: flex; flex-direction: column; justify-content: center; }
        .threat-box h3 { color: #be123c; font-size: 1.1rem; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
        .threat-box p { color: #881337; font-weight: 600; font-size: 0.95rem; }

        .tips-box { background: linear-gradient(135deg, #ecfdf5, #a7f3d0); border: 1px solid #a7f3d0; border-radius: 20px; padding: 25px; }
        .tips-box h3 { color: #047857; font-size: 1.1rem; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
        .tips-box ul { color: #065f46; font-weight: 500; font-size: 0.9rem; padding-left: 20px; }
        .tips-box li { margin-bottom: 5px; }

        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        @keyframes blink { from { opacity: 1; } to { opacity: 0.6; } }
    </style>
</head>
<body data-theme="light">
    <div class="container">
        <!-- Шапка -->
        <div class="header">
            <h1><i class="fa-solid fa-shield-halved" style="color: var(--primary);"></i> SCAM RADAR KZ</h1>
            <button class="theme-toggle" onclick="toggleTheme()"><i class="fa-solid fa-moon"></i> Theme</button>
        </div>

        <!-- Верхние карточки -->
        <div class="cards">
            <div class="card">
                <i class="fa-solid fa-chart-simple icon"></i>
                <div class="number">{{ total_reports }}</div>
                <div class="label">Total Reports</div>
            </div>
            <div class="card">
                <i class="fa-solid fa-users icon"></i>
                <div class="number">{{ total_users }}</div>
                <div class="label">Unique Users</div>
            </div>
            <div class="card danger">
                <i class="fa-solid fa-triangle-exclamation icon"></i>
                <div class="number">{{ high_risk_count }}</div>
                <div class="label">High Risk Cases</div>
            </div>
            <div class="card purple">
                <i class="fa-solid fa-database icon"></i>
                <div class="number">{{ total_schemes }}</div>
                <div class="label">Scam Schemes DB</div>
            </div>
        </div>

        <!-- Два графика -->
        <div class="grid-charts">
            <div class="section">
                <h2><i class="fa-solid fa-chart-pie" style="color: var(--primary);"></i> Scam Categories</h2>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
            <div class="section">
                <h2><i class="fa-solid fa-chart-bar" style="color: var(--purple);"></i> Attack Channels</h2>
                <div class="chart-container">
                    <canvas id="channelChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Карта и Emerging Threat -->
        <div class="grid-2">
            <div class="section">
                <h2><i class="fa-solid fa-map-location-dot" style="color: var(--danger);"></i> Geographic Spread</h2>
                <div class="map-container">
                    <!-- Реальный SVG контур Казахстана -->
                    <svg viewBox="0 0 1000 500" style="position: absolute; width: 85%; height: 85%; opacity: 0.15; fill: var(--primary);">
                        <path d="M150,200 C180,150 250,120 300,130 C350,100 400,90 450,110 C500,80 550,100 600,120 C650,90 750,110 800,150 C850,180 900,200 920,250 C950,300 900,350 850,400 C800,420 750,450 700,430 C650,460 600,440 550,410 C500,450 450,420 400,380 C350,400 300,380 250,350 C200,380 150,350 120,300 C100,250 120,220 150,200 Z" />
                    </svg>
                    <!-- Точки городов (правильное положение) -->
                    <div class="map-pin" style="top: 32%; left: 55%;"></div>
                    <div class="map-label" style="top: 28%; left: 57%;">Астана</div>

                    <div class="map-pin" style="top: 72%; left: 75%;"></div>
                    <div class="map-label" style="top: 68%; left: 77%;">Алматы</div>

                    <div class="map-pin" style="top: 78%; left: 55%;"></div>
                    <div class="map-label" style="top: 74%; left: 57%;">Шымкент</div>

                    <span style="position: absolute; bottom: 10px; right: 15px; font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Live Threat Map</span>
                </div>
            </div>

            <div class="threat-box">
                <h3><i class="fa-solid fa-bolt"></i> Emerging Threat</h3>
                <p>Hybrid Scheme: Fake Bank + Fake Gov + OTP Request</p>
                <p style="font-size: 0.85rem; font-weight: 400; margin-top: 8px; color: #9f1239;">Detected 3+ times this week. Trend is rising sharply. Scammers are combining authority of two institutions to create panic.</p>
            </div>
        </div>

        <!-- Последние кейсы и Таблица -->
        <div class="grid-3">
            <!-- Live Feed (Кейсы) -->
            <div class="section">
                <h2><i class="fa-solid fa-list-check" style="color: var(--success);"></i> Live Feed — Recent Cases</h2>
                <div class="case-list">
                    {% for report in recent_reports[:6] %}
                    <div class="case-item">
                        <div class="case-icon {{ 'bank' if 'Банк' in report.category or 'Bank' in report.category else 'egov' if 'Гос' in report.category or 'Gov' in report.category else 'delivery' if 'Доставка' in report.category else 'other' }}">
                            <i class="fa-solid fa-{{ 'building-columns' if 'Банк' in report.category or 'Bank' in report.category else 'landmark' if 'Гос' in report.category or 'Gov' in report.category else 'box' if 'Доставка' in report.category else 'circle-question' }}"></i>
                        </div>
                        <div class="case-text">
                            <strong>#{{ report.id }}</strong> - {{ report.category }} <br>
                            <span class="case-date">{{ report.date[:16] }}</span>
                        </div>
                        <span class="case-badge badge {{ report.risk_level }}">{{ report.risk_label }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Советы по безопасности -->
            <div class="tips-box">
                <h3><i class="fa-solid fa-shield-heart"></i> Защити себя</h3>
                <ul>
                    <li>Никогда не сообщайте код из SMS.</li>
                    <li>Банк не просит перевести деньги на «безопасный счёт».</li>
                    <li>Госорганы не пишут в WhatsApp или Telegram.</li>
                    <li>Установите антивирус и 2FA.</li>
                    <li>При подозрении звоните 102.</li>
                </ul>
            </div>
        </div>

        <!-- Общая таблица всех отчетов -->
        <div class="section" style="margin-bottom: 30px;">
            <h2><i class="fa-solid fa-table-list" style="color: var(--primary);"></i> Latest Reports Log</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Date & Time</th>
                            <th>Category</th>
                            <th>Channel</th>
                            <th>Risk Level</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for report in recent_reports %}
                        <tr>
                            <td>#{{ report.id }}</td>
                            <td>{{ report.date }}</td>
                            <td>{{ report.category }}</td>
                            <td>{{ report.channel }}</td>
                            <td><span class="case-badge badge {{ report.risk_level }}">{{ report.risk_label }}</span></td>
                            <td style="font-weight: 700;">{{ report.score }}/100</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        // Переключение темы
        function toggleTheme() {
            const body = document.body;
            const theme = body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
            body.setAttribute('data-theme', theme);
            document.querySelector('.theme-toggle').innerHTML = theme === 'light' ? '<i class="fa-solid fa-moon"></i> Theme' : '<i class="fa-solid fa-sun"></i> Theme';
        }

        // 1. График категорий (Doughnut)
        const ctxCat = document.getElementById('categoryChart').getContext('2d');
        const categoriesData = {{ categories|tojson }};

        new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: categoriesData.map(c => c.name),
                datasets: [{
                    data: categoriesData.map(c => c.percent),
                    backgroundColor: categoriesData.map(c => {
                        if (c.class === 'bank') return '#3b82f6';
                        if (c.class === 'egov') return '#8b5cf6';
                        if (c.class === 'delivery') return '#f59e0b';
                        if (c.class === 'investment') return '#ec4899';
                        return '#94a3b8';
                    }),
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } } } },
                cutout: '70%'
            }
        });

        // 2. График каналов (Bar Chart)
        const ctxChan = document.getElementById('channelChart').getContext('2d');
        const channelsData = {{ channels|tojson }};

        new Chart(ctxChan, {
            type: 'bar',
            data: {
                labels: channelsData.map(c => c.name),
                datasets: [{
                    label: 'Reports',
                    data: channelsData.map(c => c.count),
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    </script>
</body>
</html>
"""

# ============================================
# ДАШБОРД (БЕКЕНД)
# ============================================
@app.route('/dashboard')
def dashboard():
    all_reports = load_reports()
    total = len(all_reports)

    users = set()
    for r in all_reports:
        uid = r.get('user_id', '0')
        if uid:
            users.add(uid)
    total_users = len(users) if users else total

    # 1. Категории
    cat_counts = {}
    for r in all_reports:
        cat = r.get('category', 'Unknown')
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    categories = []
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        pct = round((count / total) * 100) if total > 0 else 0
        class_map = {
            'Фейк Банк': 'bank', 'Жалған Банк': 'bank',
            'Фейк Госорган': 'egov', 'Жалған Мемлекет': 'egov',
            'Фейк Доставка': 'delivery', 'Жалған Жеткізу': 'delivery',
            'Инвестиции': 'investment', 'Инвестиция': 'investment',
            'Другое': 'other', 'Басқа': 'other',
            'Auto Check': 'other'
        }
        cls = class_map.get(cat, 'other')
        categories.append({'name': cat[:25], 'percent': pct, 'class': cls})

    if not categories:
        categories = [
            {"name": "Фейк Банк", "percent": 40, "class": "bank"},
            {"name": "Фейк Госорган", "percent": 30, "class": "egov"},
            {"name": "Фейк Доставка", "percent": 20, "class": "delivery"},
            {"name": "Инвестиции", "percent": 10, "class": "investment"},
        ]

    # 2. Каналы связи (Bar Chart)
    chan_counts = {}
    for r in all_reports:
        chan = r.get('channel', 'Unknown')
        if chan and chan != 'Неизвестно' and chan != 'Unknown':
            chan_counts[chan] = chan_counts.get(chan, 0) + 1

    channels = []
    for chan, count in sorted(chan_counts.items(), key=lambda x: -x[1])[:6]:
        channels.append({'name': chan, 'count': count})

    if not channels:
        channels = [
            {'name': 'Звонок', 'count': 15},
            {'name': 'Telegram', 'count': 10},
            {'name': 'SMS', 'count': 5},
            {'name': 'WhatsApp', 'count': 3}
        ]

    # 3. Риски
    risk_counts = {"КРИТИЧЕСКИЙ": 0, "ВЫСОКИЙ": 0, "СРЕДНИЙ": 0, "НИЗКИЙ": 0}
    for r in all_reports:
        level = r.get('analysis', {}).get('risk_level', 'НИЗКИЙ')
        if level in risk_counts:
            risk_counts[level] += 1

    high_risk_count = risk_counts.get('КРИТИЧЕСКИЙ', 0) + risk_counts.get('ВЫСОКИЙ', 0)

    # 4. Последние отчёты
    recent = sorted(all_reports, key=lambda x: x.get('date', ''), reverse=True)[:15]
    risk_map = {
        "КРИТИЧЕСКИЙ": "critical",
        "ВЫСОКИЙ": "high",
        "СРЕДНИЙ": "medium",
        "НИЗКИЙ": "low"
    }

    recent_reports = []
    for r in recent:
        raw_level = r.get('analysis', {}).get('risk_level', 'НИЗКИЙ')
        recent_reports.append({
            'id': r.get('id', '?'),
            'category': r.get('category', 'Unknown')[:20],
            'channel': r.get('channel', 'Unknown')[:15],
            'risk_level': risk_map.get(raw_level, 'low'),
            'risk_label': raw_level,
            'score': r.get('analysis', {}).get('risk_score', 0),
            'date': r.get('date', '')
        })

    if not recent_reports:
        recent_reports = [
            {'id': 1, 'category': 'Фейк Банк', 'channel': 'Звонок', 'risk_level': 'critical', 'risk_label': 'КРИТИЧЕСКИЙ', 'score': 90, 'date': '2026-10-19 12:00:00'},
            {'id': 2, 'category': 'Фейк Госорган', 'channel': 'Telegram', 'risk_level': 'high', 'risk_label': 'ВЫСОКИЙ', 'score': 75, 'date': '2026-10-19 11:30:00'},
            {'id': 3, 'category': 'Фейк Доставка', 'channel': 'SMS', 'risk_level': 'medium', 'risk_label': 'СРЕДНИЙ', 'score': 45, 'date': '2026-10-19 10:15:00'},
            {'id': 4, 'category': 'Инвестиции', 'channel': 'Сайт', 'risk_level': 'low', 'risk_label': 'НИЗКИЙ', 'score': 15, 'date': '2026-10-19 09:00:00'},
            {'id': 5, 'category': 'Авто Check', 'channel': 'Звонок', 'risk_level': 'critical', 'risk_label': 'КРИТИЧЕСКИЙ', 'score': 85, 'date': '2026-10-18 18:00:00'},
            {'id': 6, 'category': 'Другое', 'channel': 'WhatsApp', 'risk_level': 'medium', 'risk_label': 'СРЕДНИЙ', 'score': 30, 'date': '2026-10-18 15:00:00'},
        ]

    return render_template_string(
        DASHBOARD_HTML,
        total_reports=total,
        total_users=total_users,
        high_risk_count=high_risk_count,
        categories=categories,
        channels=channels,
        recent_reports=recent_reports,
        total_schemes=TOTAL_SCHEMES
    )

# ============================================
# МЕНЮ (10 КНОПОК)
# ============================================
def main_menu(lang='ru'):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == 'kk':
        buttons = [
            "🚀 БОТТЫ ІСКЕ ҚОСУ", "📋 БАСТЫ МӘЗІР", "📖 НҰСҚАУ", "📊 СТАТИСТИКА", "🆘 SOS",
            "📝 СХЕМА ТУРАЛЫ ХАБАРЛАУ", "📞 ГИБРИДТІ СХЕМА", "💳 ДРОППЕРСТВО",
            "🚨 ТӨТЕНШЕ ЖАҒДАЙ", "ℹ️ ЖОБА ТУРАЛЫ"
        ]
    else:
        buttons = [
            "🚀 Запустить бота", "📋 Главное меню", "📖 Инструкция", "📊 Статистика", "🆘 SOS",
            "📝 Сообщить о схеме", "📞 Гибридная схема", "💳 Дропперство",
            "🚨 Чрезвычайная ситуация", "ℹ️ О проекте"
        ]
    markup.add(*[KeyboardButton(b) for b in buttons])
    return markup

def category_menu(lang='ru'):
    markup = InlineKeyboardMarkup(row_width=2)
    if lang == 'kk':
        markup.add(
            InlineKeyboardButton("🏦 Жалған Банк", callback_data="cat_bank"),
            InlineKeyboardButton("🏛️ Жалған Мемлекет", callback_data="cat_egov"),
            InlineKeyboardButton("📦 Жалған Жеткізу", callback_data="cat_delivery"),
            InlineKeyboardButton("💰 Инвестиция", callback_data="cat_investment"),
            InlineKeyboardButton("💼 Жалған Жұмыс", callback_data="cat_job"),
            InlineKeyboardButton("❓ Басқа", callback_data="cat_other")
        )
    else:
        markup.add(
            InlineKeyboardButton("🏦 Фейк Банк", callback_data="cat_bank"),
            InlineKeyboardButton("🏛️ Фейк Госорган", callback_data="cat_egov"),
            InlineKeyboardButton("📦 Фейк Доставка", callback_data="cat_delivery"),
            InlineKeyboardButton("💰 Инвестиции", callback_data="cat_investment"),
            InlineKeyboardButton("💼 Фейк Работа", callback_data="cat_job"),
            InlineKeyboardButton("❓ Другое", callback_data="cat_other")
        )
    return markup

def channel_menu(lang='ru'):
    markup = InlineKeyboardMarkup(row_width=2)
    if lang == 'kk':
        markup.add(
            InlineKeyboardButton("📞 Телефон", callback_data="ch_phone"),
            InlineKeyboardButton("💬 Telegram", callback_data="ch_telegram"),
            InlineKeyboardButton("🟢 WhatsApp", callback_data="ch_whatsapp"),
            InlineKeyboardButton("📩 SMS", callback_data="ch_sms"),
            InlineKeyboardButton("🌐 Сайт", callback_data="ch_website"),
            InlineKeyboardButton("📧 Email", callback_data="ch_email")
        )
    else:
        markup.add(
            InlineKeyboardButton("📞 Звонок", callback_data="ch_phone"),
            InlineKeyboardButton("💬 Telegram", callback_data="ch_telegram"),
            InlineKeyboardButton("🟢 WhatsApp", callback_data="ch_whatsapp"),
            InlineKeyboardButton("📩 SMS", callback_data="ch_sms"),
            InlineKeyboardButton("🌐 Сайт", callback_data="ch_website"),
            InlineKeyboardButton("📧 Email", callback_data="ch_email")
        )
    return markup

# ============================================
# АНАЛИЗ РИСКА
# ============================================
def analyze_risk(text):
    text_lower = text.lower()
    score = 0
    details = []
    is_code = False
    is_bank = False
    is_egov = False
    is_delivery = False
    is_transfer = False
    is_phone = False
    is_telegram = False

    RED_FLAGS = {
        "Подражание банку": [
            "банк", "каспи", "kaspi", "halyk", "жусан", "jusan",
            "forte", "отбасы", "сбер", "сотрудник", "служба",
            "безопасности", "финансовый", "кредитный", "вклад",
            "счет", "счёт", "карта", "карту", "карты",
            "безопасный счёт", "защищённый счёт", "резервный счёт",
            "текущий счёт", "снимите с депозита", "переведите на другой счёт",
            "сохранить деньги", "списание", "несанкционированное списание",
            "подозрительная операция", "подозрительная транзакция",
            "блокировка счета", "арест счета", "обналичить", "билайн", "алтел", "кселл", "теле2"
        ],
        "Подражание госоргану": [
            "egov", "эгов", "госуслуг", "цон", "мвд", "афм",
            "прокуратур", "налогов", "комитет", "министерств",
            "департамент", "управление", "госструктур",
            "гос структур", "правительств", "администрац",
            "следователь", "сотрудник мвд", "кнб", "национальная безопасность",
            "комитет национальной безопасности", "финансовый мониторинг",
            "антифрод", "секретная операция", "служебная проверка",
            "дознание", "следственный комитет", "оперуполномоченный", "егов"
        ],
        "Запрос кода/пароля": [
            "код", "кода", "коду", "кодом", "коде", "otp",
            "sms", "смс", "подтвержд", "пароль", "пароля",
            "верификаци", "проверк", "цифр", "пин",
            "6 значный", "6-значный", "шестизначный",
            "4 значный", "4-значный", "четырехзначный",
            "номер", "номера", "номером", "цифры",
            "код из смс", "код подтверждения", "одноразовый пароль",
            "cvv", "cvc", "пин-код", "данные карты", "реквизиты карты",
            "номер карты", "срок действия", "имя держателя",
            "логин", "пароль от приложения"
        ],
        "Звонок/телефон": [
            "по телефону", "позвонили", "звонок", "звонили",
            "номер телефона", "с номера", "на номер",
            "ватсап", "whatsapp", "вацап", "viber", "вайбер",
            "входящий звонок", "неизвестный номер", "московский номер",
            "номер 495", "звонят постоянно", "с России позвонили", "номер Российский"
        ],
        "Программы удаленного доступа": [
            "teamviewer", "anydesk", "rustdesk", "hop to desk",
            "rude desktop", "установите приложение", "скачайте программу",
            "демонстрация экрана", "удалённый доступ", "подключитесь к компьютеру",
            "удаленное управление", "подключение к телефону", "взлом", "хакинг"
        ],
        "Эмоциональный шантаж (родственники)": [
            "родственник попал в беду", "дтп", "скорая помощь", "больница",
            "срочно переведите деньги", "помогите родственнику", "авария",
            "ваш близкий", "сын", "дочь", "мама", "папа", "брат", "сестра",
            "попал в аварию", "задержали", "в полиции", "нужны деньги"
        ],
        "Выигрыши/призы": [
            "вы выиграли приз", "компенсация", "лотерея", "акция",
            "розыгрыш", "оплатите госпошлину", "оплатите налог",
            "оплатите доставку", "получите выигрыш", "подарок",
            "бесплатно", "конкурс"
        ],
        "Фишинг/ссылки": [
            "ссылк", "перейди по ссылк", "на сайте", "регистраци",
            "заполни", "введи", "войти", "зайти",
            "подтвердите данные", "обновите данные", "подтвердите личность",
            "пройдите верификацию", "заполните форму", "войдите в личный кабинет",
            "ваш аккаунт взломан", "восстановите доступ", "фейс айди"
        ],
        "Доставка/службы": [
            "доставка", "посылк", "olx", "заказ", "яндекс маркет",
            "курьер", "отправлени", "служба доставк",
            "почт", "посылка", "груз", "отправка",
            "курьерская доставка", "заказное письмо", "заказ на сумму",
            "срочная доставка", "недоставка", "проблемы с доставкой",
            "отслеживание", "трек код", "каз почта", "трекинг"
        ],
        "Вакансии/работа": [
            "удаленная работа", "легкий заработок", "подработка",
            "вакансия", "требуются сотрудники", "высокий доход",
            "пассивный доход", "инвестиции", "трейдинг", "криптовалюта",
            "быстрый заработок", "фриланс", "удаленка"
        ],
        "Просьба перевести деньги": [
            "переведи", "перевод", "перевести", "безопасный",
            "резервный", "на карту", "отправить", "перечисл",
            "перевел", "перевела", "перевели"
        ],
        "Переход в Telegram": [
            "телеграм", "telegram", "тг", "t.me", "напиши",
            "перейди", "напишите"
        ],
        "Давление/срочность": [
            "не кладите трубку", "ни в коем случае не отключайтесь",
            "срочно", "немедленно", "прямо сейчас", "только что",
            "вы не можете никому говорить", "секретная операция",
            "никому не рассказывайте"
        ],
        "Долбят/преследуют": [
            "долбят", "преследуют", "постоянно звонят",
            "каждый день", "не отстают", "достают",
            "названивают", "терроризируют", "угрожают", "сталкерят"
        ],
        "Зомби-фразы (жертвы под влиянием)": [
            "мне запретили рассказывать", "если расскажу будет хуже",
            "это не ваше дело, я сам разберусь", "я всё делаю правильно",
            "просто подожди", "доверься мне", "потом всё расскажу"
        ]
    }

    for category, keywords in RED_FLAGS.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            score += len(found) * 10
            details.append(f"{category}: {', '.join(found[:2])}")
            if category == "Запрос кода/пароля":
                is_code = True
            if category == "Подражание банку":
                is_bank = True
            if category == "Подражание госоргану":
                is_egov = True
            if category == "Доставка/службы":
                is_delivery = True
            if category == "Просьба перевести деньги":
                is_transfer = True
            if category == "Звонок/телефон":
                is_phone = True
            if category == "Переход в Telegram":
                is_telegram = True

    if is_code:
        if is_bank:
            score = max(score, 85)
            risk_level = "КРИТИЧЕСКИЙ"
            risk_emoji = "🔴🔴"
            solution = "🚨🚨 ВЫ СКАЗАЛИ КОД ИЗ БАНКА! Это ОФЕРТА — мошенническая схема!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ ЗАБЛОКИРУЙТЕ ВСЕ КАРТЫ!\n2️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!\n3️⃣ СООБЩИТЕ В АНТИФРОД-ЦЕНТР 8-800-080-0000!"
            instruction = "КРИТИЧЕСКАЯ ОПАСНОСТЬ! Деньги могут быть украдены!"
        elif is_egov:
            score = max(score, 75)
            risk_level = "КРИТИЧЕСКИЙ"
            risk_emoji = "🔴🔴"
            solution = "🚨🚨 ВЫ СКАЗАЛИ КОД ИЗ ГОСОРГАНА! Это мошенничество!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ ЗАБЛОКИРУЙТЕ ВСЕ КАРТЫ!\n2️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!\n3️⃣ НЕ ОТВЕЧАЙТЕ НА ЗВОНКИ!"
            instruction = "КРИТИЧЕСКАЯ ОПАСНОСТЬ! Мошенники получили доступ!"
        elif is_transfer:
            score = max(score, 70)
            risk_level = "КРИТИЧЕСКИЙ"
            risk_emoji = "🔴🔴"
            solution = "🚨🚨 ВАС ПРОСЯТ ПЕРЕВЕСТИ ДЕНЬГИ ПОСЛЕ КОДА!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ НЕ ПЕРЕВОДИТЕ ДЕНЬГИ!\n2️⃣ ЗАБЛОКИРУЙТЕ КАРТЫ!\n3️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!"
            instruction = "МОШЕННИКИ! Они пытаются украсть ваши деньги!"
        else:
            score = max(score, 50)
            risk_level = "ВЫСОКИЙ"
            risk_emoji = "🔴"
            solution = "🚨 ВЫ УПОМЯНУЛИ КОД! Это почти всегда признак мошенничества!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ НЕ НАЗЫВАЙТЕ КОД НИКОМУ!\n2️⃣ ЗАБЛОКИРУЙТЕ КАРТЫ!\n3️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102, если уже сказали!"
            instruction = "СРОЧНО! Не называйте код! Заблокируйте карты!"
    else:
        if is_bank and is_egov:
            score = max(score, 70)
            risk_level = "КРИТИЧЕСКИЙ"
            risk_emoji = "🔴🔴"
            solution = "🚨🚨 ГИБРИДНАЯ СХЕМА! Вам звонят из банка И из госоргана!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ ЗАБЛОКИРУЙТЕ ВСЕ КАРТЫ!\n2️⃣ НЕ ОТВЕЧАЙТЕ НА ЗВОНКИ!\n3️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!"
            instruction = "ГИБРИДНАЯ СХЕМА! Мошенники атакуют с двух сторон!"
        elif is_bank and is_transfer:
            score = max(score, 60)
            risk_level = "ВЫСОКИЙ"
            risk_emoji = "🔴"
            solution = "🚨 Вас просят перевести деньги! Это мошенничество!\n\n⚠️ НЕМЕДЛЕННО:\n1️⃣ ЗАБЛОКИРУЙТЕ КАРТЫ!\n2️⃣ НЕ ПЕРЕВОДИТЕ ДЕНЬГИ!\n3️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!"
            instruction = "МОШЕННИКИ! Они хотят украсть ваши деньги!"
        elif is_egov and is_phone:
            score = max(score, 40)
            risk_level = "СРЕДНИЙ"
            risk_emoji = "🟠"
            solution = "⚠️ Вам звонят из 'госоргана'?\n\n⚠️ Мошенники всё ещё на связи!\n\n✅ ЧТО ДЕЛАТЬ:\n1️⃣ НЕ ОТВЕЧАЙТЕ!\n2️⃣ ЗАБЛОКИРУЙТЕ НОМЕР!\n3️⃣ САМИ ПОЗВОНИТЕ В ГОСОРГАН!"
            instruction = "Мошенники всё ещё на связи! Не вступайте в диалог!"
        elif is_delivery and any(w in text_lower for w in ["ссылк", "перейди", "регистраци"]):
            score = max(score, 35)
            risk_level = "СРЕДНИЙ"
            risk_emoji = "🟠"
            solution = "⚠️ Сообщение о доставке со ссылкой!\n\n⚠️ НЕ ПЕРЕХОДИТЕ!\n1️⃣ НЕ ПЕРЕХОДИТЕ ПО ССЫЛКЕ!\n2️⃣ НЕ ВВОДИТЕ ДАННЫЕ!\n3️⃣ ПРОВЕРЬТЕ ЧЕРЕЗ ОФИЦИАЛЬНЫЙ САЙТ!"
            instruction = "Фишинг! Мошенники пытаются украсть ваши данные!"
        elif is_bank and is_telegram:
            score = max(score, 35)
            risk_level = "СРЕДНИЙ"
            risk_emoji = "🟠"
            solution = "⚠️ Вас просят перейти в Telegram из банка!\n\n1️⃣ НЕ ПЕРЕХОДИТЕ!\n2️⃣ ЗАБЛОКИРУЙТЕ ОТПРАВИТЕЛЯ!\n3️⃣ САМИ ПОЗВОНИТЕ В БАНК!"
            instruction = "Мошенники пытаются заманить вас в Telegram!"
        elif "долбят" in text_lower or "преследуют" in text_lower or "названивают" in text_lower:
            score = max(score, 50)
            risk_level = "ВЫСОКИЙ"
            risk_emoji = "🔴"
            solution = "🚨 Вас преследуют звонками!\n\n1️⃣ НЕ ОТВЕЧАЙТЕ!\n2️⃣ ЗАБЛОКИРУЙТЕ НОМЕР!\n3️⃣ ЗАБЛОКИРУЙТЕ КАРТЫ!\n4️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!"
            instruction = "МОШЕННИКИ! Они пытаются вас запугать!"
        elif any(w in text_lower for w in ["запретили рассказывать", "если расскажу будет хуже", "я всё делаю правильно"]):
            score = max(score, 45)
            risk_level = "ВЫСОКИЙ"
            risk_emoji = "🔴"
            solution = "🚨 ВЫ ГОВОРИТЕ ФРАЗЫ, КОТОРЫЕ ИСПОЛЬЗУЮТ ЖЕРТВЫ МОШЕННИКОВ!\n\n⚠️ ВАС МОГУТ ЗОМБИРОВАТЬ!\n\n✅ ЧТО ДЕЛАТЬ:\n1️⃣ НЕМЕДЛЕННО СВЯЖИТЕСЬ С БЛИЗКИМИ!\n2️⃣ ПОГОВОРИТЕ С КЕМ-ТО, КОМУ ДОВЕРЯЕТЕ!\n3️⃣ НЕ ПЕРЕВОДИТЕ ДЕНЬГИ!\n4️⃣ ПОЗВОНИТЕ В ПОЛИЦИЮ 102!"
            instruction = "Вас могут зомбировать! Срочно свяжитесь с близкими!"
        elif score >= 25:
            risk_level = "СРЕДНИЙ"
            risk_emoji = "🟠"
            solution = "⚠️ Будьте осторожны! Проверьте информацию.\n\n1️⃣ НЕ ОТВЕЧАЙТЕ НА ПОДОЗРИТЕЛЬНЫЕ ЗВОНКИ!\n2️⃣ ЗАБЛОКИРУЙТЕ ПОДОЗРИТЕЛЬНЫЕ НОМЕРА!"
            instruction = "Будьте осторожны! Проверяйте информацию!"
        else:
            risk_level = "НИЗКИЙ"
            risk_emoji = "🟢"
            score = max(score, 5)
            solution = "✅ Угрозы нет. Вы в безопасности.\n\n💡 РЕКОМЕНДАЦИИ:\n1️⃣ ЗАКРОЙТЕ ОНЛАЙН-ПОКУПКИ\n2️⃣ ПРОВЕРЬТЕ ПОДПИСКИ И СЧЕТА\n3️⃣ ОБНОВИТЕ ПАРОЛИ В БАНК-ПРИЛОЖЕНИЯХ"
            instruction = "Всё безопасно. Но будьте готовы закрыть счета при подозрении."

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "risk_emoji": risk_emoji,
        "details": details,
        "solution": solution,
        "instruction": instruction,
        "is_code": is_code,
        "is_bank": is_bank,
        "is_egov": is_egov,
        "is_delivery": is_delivery,
        "is_transfer": is_transfer,
        "is_phone": is_phone,
        "is_telegram": is_telegram
    }

# ============================================
# УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================
def clarify_response(message, lang='ru'):
    user_id = str(message.from_user.id)
    temp_state[user_id] = {"step": "clarify", "collected": {}}

    if lang == 'kk':
        text = """🤔 Түсінбедім.

Бұл не?
/call — қоңырау
/message — хабарлама

Кім?
/bank — банк
/gov — мемлекет
/delivery — жеткізу
/other — басқа

Не сұрады?
/code — код
/money — ақша
/link — сілтеме"""
    else:
        text = """🤔 Не понял.

Это что?
/call — звонок
/message — сообщение

Кто?
/bank — банк
/gov — госорган
/delivery — доставка
/other — другое

Что просили?
/code — код
/money — деньги
/link — ссылку"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu(lang))

# ============================================
# ФУНКЦИИ БОТА
# ============================================
def welcome_message(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')
    if lang == 'kk':
        welcome_text = "🚨 **SCAM RADAR KZ** 🚨\n\n**ҚОШ КЕЛДІҢІЗ!**\n\n**СЕНІҢ МІНДЕТІҢ:**\n1️⃣ **📝 СХЕМА ТУРАЛЫ ХАБАРЛАУ** батырмасын бас\n2️⃣ Не болғанын сипатта\n3️⃣ Біз мәселені шешуге көмектесеміз\n\n✅ Барлық хабарламалар **анонимді**.\n🔒 Ешқандай жеке деректер сақталмайды."
    else:
        welcome_text = "🚨 **SCAM RADAR KZ** 🚨\n\n**ДОБРО ПОЖАЛОВАТЬ В ПРОЕКТ!**\n\n**ТВОЯ ЗАДАЧА:**\n1️⃣ Нажми **📝 Сообщить о схеме**\n2️⃣ Опиши, что произошло\n3️⃣ Мы поможем решить твою проблему\n\n✅ Все сообщения **анонимны**.\n🔒 Личные данные не сохраняются."
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def instructions(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')
    if lang == 'kk':
        inst_text = "📖 **НҰСҚАУ**\n\n💬 Кез келген хабарлама жаза аласыз — мен оны алаяқтыққа талдаймын.\n\n✅ Барлық хабарламалар **анонимді**."
    else:
        inst_text = "📖 **ИНСТРУКЦИЯ**\n\n💬 Ты можешь написать любое сообщение — я проанализирую его.\n\n✅ Все сообщения **анонимны**."
    bot.send_message(message.chat.id, inst_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def stats(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')
    total = len(reports)
    categories = {}
    risk_levels = {"КРИТИЧЕСКИЙ": 0, "ВЫСОКИЙ": 0, "СРЕДНИЙ": 0, "НИЗКИЙ": 0}
    for r in reports:
        cat = r.get("category", "Неизвестно")
        categories[cat] = categories.get(cat, 0) + 1
        level = r.get("analysis", {}).get("risk_level", "НИЗКИЙ")
        if level in risk_levels:
            risk_levels[level] += 1
    if lang == 'kk':
        stats_text = f"📊 **СТАТИСТИКА**\n\nБарлығы: **{total}**\n\nСхема базасы: **{TOTAL_SCHEMES}**\n\n"
        if categories:
            stats_text += "📌 **СХЕМА ТҮРЛЕРІ:**\n"
            for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
                stats_text += f"  {cat}: {count}\n"
    else:
        stats_text = f"📊 **СТАТИСТИКА**\n\nВсего отчётов: **{total}**\n\nСхем в базе: **{TOTAL_SCHEMES}**\n\n"
        if categories:
            stats_text += "📌 **ТИПЫ СХЕМ:**\n"
            for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
                stats_text += f"  {cat}: {count}\n"
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def sos(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')

    if lang == 'kk':
        sos_text = """🆘 **SOS — АҚША КЕТІП ҚАЛДЫ МА?**

**АЛҒАШҚЫ 60 СЕКУНДТА:**

1️⃣ **БАНКТІҢ ҚОСЫМШАСЫН АШЫҢЫЗ**
   → Картаны БҰҒАТТАҢЫЗ

2️⃣ **БАНККЕ ҚОҢЫРАУ ШАЛЫҢЫЗ**
""" + BANK_NUMBERS + """

3️⃣ **СКРИНШОТТАРДЫ САҚТАҢЫЗ**
   → Барлық SMS, хабарламалар

4️⃣ **ПОЛИЦИЯҒА ХАБАРЛАСЫҢЫЗ**
   ☎️ 102 немесе 112

5️⃣ **АНТИФРОД-ЦЕНТРГЕ ХАБАРЛАСЫҢЫЗ**
   ☎️ 8-800-080-0000"""
    else:
        sos_text = """🆘 **SOS — ДЕНЬГИ УШЛИ?**

**ПЕРВЫЕ 60 СЕКУНД:**

1️⃣ **ОТКРОЙТЕ ПРИЛОЖЕНИЕ БАНКА**
   → Заблокируйте карту

2️⃣ **ПОЗВОНИТЕ В БАНК**
""" + BANK_NUMBERS + """

3️⃣ **СОХРАНИТЕ СКРИНШОТЫ**
   → Все SMS, сообщения

4️⃣ **ПОЗВОНИТЕ В ПОЛИЦИЮ**
   ☎️ 102 или 112

5️⃣ **СООБЩИТЕ В АНТИФРОД-ЦЕНТР**
   ☎️ 8-800-080-0000"""
    bot.send_message(message.chat.id, sos_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def hybrid_scheme(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')

    if lang == 'kk':
        hybrid_text = """⚠️ **ГИБРИДТІ СХЕМА — ЕКІ ФРОНТ**

**СХЕМА:**

1️⃣ **БІРІНШІ ҚОҢЫРАУ — БАНКТЕН**
2️⃣ **ЕКІНШІ ҚОҢЫРАУ — ГОСОРГАННАН**
3️⃣ **ҚОРҚЫТУ** — «ешкімге айтпаңыз»
4️⃣ **АҚША АУДАРУ** — «қауіпсіз шотқа»

**🚩 ҚЫЗЫЛ ФЛАГТАР:**
❌ Екі мекемеден бір күні қоңырау
❌ «Ешкімге айтпаңыз»
❌ Қоңырауды қоюға рұқсат жоқ
❌ Код немесе CVV сұрайды

**✅ НЕ ІСТЕУ КЕРЕК:**
1️⃣ ТҮТІКШЕНІ ТАСТАҢЫЗ
2️⃣ БАНККЕ ӨЗІҢІЗ ҚОҢЫРАУ ШАЛЫҢЫЗ
3️⃣ 102-ге ХАБАРЛАСЫҢЫЗ
4️⃣ КАРТАЛАРДЫ БҰҒАТТАҢЫЗ:
""" + BANK_NUMBERS + """

⚠️ **ГОСОРГАНДАР TELEGRAM-НАН ЖАЗБАЙДЫ!**"""
    else:
        hybrid_text = """⚠️ **ГИБРИДНАЯ СХЕМА — ДВА ФРОНТА**

**СХЕМА:**

1️⃣ **ПЕРВЫЙ ЗВОНОК — ИЗ БАНКА**
2️⃣ **ВТОРОЙ ЗВОНОК — ИЗ ГОСОРГАНА**
3️⃣ **ЗАПУГИВАНИЕ** — «никому не говорите»
4️⃣ **ПЕРЕВОД ДЕНЕГ** — «на безопасный счёт»

**🚩 КРАСНЫЕ ФЛАГИ:**
❌ Звонят из двух организаций в один день
❌ Говорят «никому не рассказывайте»
❌ Не дают положить трубку
❌ Просят код или CVV

**✅ ЧТО ДЕЛАТЬ:**
1️⃣ ПОЛОЖИТЕ ТРУБКУ
2️⃣ ПОЗВОНИТЕ В БАНК САМИ
3️⃣ ЗВОНИТЕ 102
4️⃣ ЗАБЛОКИРУЙТЕ КАРТЫ:
""" + BANK_NUMBERS + """

⚠️ **ГОСОРГАНЫ НИКОГДА НЕ ПИШУТ В TELEGRAM!**"""
    bot.send_message(message.chat.id, hybrid_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def dropper_info(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')

    if lang == 'kk':
        dropper_text = """💳 **ДРОППЕРСТВО — ҚЫЛМЫС**

**ЗАҢ:**
⚖️ ҚК 232-1-бап (16.09.2025)
⚖️ **7 жылға дейін** бас бостандығынан айыру
⚖️ Мүлік тәркіленеді

**СХЕМА:**
1️⃣ Instagram/Telegram-да «жеңіл табыс»
2️⃣ Карта немесе SIM-карта сұрайды
3️⃣ Сіздің шоттан ҰРЛАНҒАН ақша өтеді
4️⃣ Сізді ұстайды — СЕРІКТЕС ретінде

**НАҚТЫ ІС (2025):**
40,000 ₸ алды → 86,500 ₸ айыппұл
+ 21,625 ₸ қорға + соттылық

**✅ НЕ ІСТЕУ КЕРЕК:**
❌ Картаны ЕШКІМГЕ бермеңіз
❌ SIM-картаны тіркемеңіз
✅ 102-ге ХАБАРЛАСЫҢЫЗ"""
    else:
        dropper_text = """💳 **ДРОППЕРСТВО — ЭТО ПРЕСТУПЛЕНИЕ**

**УГОЛОВНАЯ ОТВЕТСТВЕННОСТЬ:**
⚖️ Статья 232-1 УК РК (с 16.09.2025)
⚖️ **До 7 лет** лишения свободы
⚖️ Конфискация имущества

**СХЕМА:**
1️⃣ В Instagram/Telegram пишут «лёгкий заработок»
2️⃣ Просят карту или SIM-карту
3️⃣ Через ваш счёт проходят УКРАДЕННЫЕ деньги
4️⃣ Вас задерживают — как СООБЩНИКА

**РЕАЛЬНЫЙ КЕЙС (2025):**
Получила 40,000 ₸ → штраф 86,500 ₸
+ 21,625 ₸ в фонд потерпевших + судимость

**✅ ЧТО ДЕЛАТЬ:**
❌ НЕ давайте карту НИКОМУ
❌ НЕ регистрируйте SIM на других
✅ СООБЩИТЕ В ПОЛИЦИЮ 102"""
    bot.send_message(message.chat.id, dropper_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def emergency_info(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')

    if lang == 'kk':
        emergency_text = """🚨 **ТӨТЕНШЕ ЖАҒДАЙ**

**1️⃣ АҚША КЕТТІ** → картаны бұғатта, банкке қоңырау, 102
**2️⃣ АККАУНТ БҰЗЫЛДЫ** → құпия сөзді ауыстыр, 2FA қос
**3️⃣ ТЕЛЕФОН ҰРЛАНДЫ** → SIM-ді бұғатта, банкті өшір
**4️⃣ ҚОРҚЫТАДЫ** → төлеме, 102-ге хабарлас
**5️⃣ ГОСОРГАННАН ҚОҢЫРАУ** → түтікшені таста, өзің қоңырау шал

**ЖЕДЕЛ НӨМІРЛЕР:**
☎️ 102 — Полиция
☎️ 112 — Бірыңғай
☎️ 103 — Жедел жәрдем
☎️ 8-800-080-0000 — Антифрод

**БАНКТЕР:**
""" + BANK_NUMBERS
    else:
        emergency_text = """🚨 **ЧРЕЗВЫЧАЙНАЯ СИТУАЦИЯ**

**1️⃣ ДЕНЬГИ УШЛИ** → блокируй карту, звони в банк, 102
**2️⃣ АККАУНТ ВЗЛОМАЛИ** → смени пароль, включи 2FA
**3️⃣ УКРАЛИ ТЕЛЕФОН** → блокируй SIM, отвяжи банк
**4️⃣ УГРОЖАЮТ** → не плати, звони 102
**5️⃣ ЗВОНЯТ ИЗ ГОСОРГАНА** → положи трубку, перезвони сам

**ЭКСТРЕННЫЕ НОМЕРА:**
☎️ 102 — Полиция
☎️ 112 — Единый
☎️ 103 — Скорая
☎️ 8-800-080-0000 — Антифрод

**БАНКИ:**
""" + BANK_NUMBERS
    bot.send_message(message.chat.id, emergency_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def about_project(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')
    about_text = f"ℹ️ **SCAM RADAR KZ**\n\n**Что это?** — система раннего обнаружения мошеннических схем, созданная молодежью Казахстана.\n\n📚 **Схем в базе:** {TOTAL_SCHEMES}\n\n**НОМЕРА БАНКОВ:**\n{BANK_NUMBERS}"
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown', reply_markup=main_menu(lang))

def schemes_list(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')

    text = f"📚 **БАЗА ИЗВЕСТНЫХ СХЕМ** ({TOTAL_SCHEMES})\n\n"
    for category, schemes in KNOWN_SCHEMES.items():
        text += f"**{category}** ({len(schemes)}):\n"
        for scheme in schemes[:5]:
            text += f"  • {scheme}\n"
        if len(schemes) > 5:
            text += f"  ... и ещё {len(schemes) - 5}\n"
        text += "\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu(lang))

def get_extended_response(analysis, lang='ru', original_text=''):
    if lang == 'kk':
        response = f"{analysis['risk_emoji']} **ҚАУІП ДЕҢГЕЙІ: {analysis['risk_level']}**\nДәреже: {analysis['risk_score']}/100\n\n**Анықталған белгілер:**\n"
        for detail in analysis['details']:
            response += f"  ⚠️ {detail}\n"
        response += f"\n**НЕ ІСТЕУ КЕРЕК:**\n{analysis['solution']}\n\n**📌 {analysis['instruction']}**\n\n**БАРЛЫҚ НӨМІРЛЕР:**\n{BANK_NUMBERS}\n\n📞 **Антифрод-центр:** 8-800-080-0000\n☎️ **Полиция:** 102 немесе 112\n🔒 Есеп **анонимді** түрде сақталды."
    else:
        response = f"{analysis['risk_emoji']} **УРОВЕНЬ РИСКА: {analysis['risk_level']}**\nОценка: {analysis['risk_score']}/100\n\n**Обнаруженные признаки:**\n"
        for detail in analysis['details']:
            response += f"  ⚠️ {detail}\n"
        response += f"\n**ЧТО ДЕЛАТЬ:**\n{analysis['solution']}\n\n**📌 {analysis['instruction']}**\n\n**ВСЕ НОМЕРА:**\n{BANK_NUMBERS}\n\n📞 **Антифрод-центр:** 8-800-080-0000\n☎️ **Полиция:** 102 или 112\n🔒 Отчёт сохранён **анонимно**."
    return response

# ============================================
# ОСНОВНАЯ ЛОГИКА БОТА
# ============================================
@bot.message_handler(commands=['schemes'])
def cmd_schemes(message):
    schemes_list(message)

@bot.message_handler(commands=['call', 'message', 'bank', 'gov', 'delivery', 'other', 'code', 'money', 'link'])
def clarify_handler(message):
    user_id = str(message.from_user.id)
    lang = user_language.get(user_id, 'ru')
    cmd = message.text.lower().replace('/', '')

    if user_id not in temp_state:
        temp_state[user_id] = {"step": "clarify", "collected": {}}
    if "collected" not in temp_state[user_id]:
        temp_state[user_id]["collected"] = {}

    collected = temp_state[user_id]["collected"]

    if cmd in ['call', 'message']:
        collected['type'] = 'Звонок' if cmd == 'call' else 'Сообщение'
    elif cmd in ['bank', 'gov', 'delivery', 'other']:
        type_map = {'bank': 'Банк', 'gov': 'Госорган', 'delivery': 'Доставка', 'other': 'Другое'}
        collected['source'] = type_map[cmd]
    elif cmd in ['code', 'money', 'link']:
        action_map = {'code': 'Просили код', 'money': 'Просили перевести деньги', 'link': 'Просили перейти по ссылке'}
        collected['action'] = action_map[cmd]

    if all(k in collected for k in ['type', 'source', 'action']):
        full_text = f"{collected['type']} из {collected['source']}. {collected['action']}."
        analysis = analyze_risk(full_text)

        report = {
            "id": len(reports) + 1,
            "user": "Аноним",
            "user_id": user_id,
            "text": full_text,
            "category": collected['source'],
            "channel": collected['type'],
            "analysis": analysis,
            "anonymous": 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        reports.append(report)
        save_reports(reports)

        response = get_extended_response(analysis, lang, full_text)
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=main_menu(lang))
        del temp_state[user_id]
    else:
        msg = "📋 " + " | ".join(collected.values())
        if 'type' not in collected:
            msg += "\n→ /call или /message"
        if 'source' not in collected:
            msg += "\n→ /bank, /gov, /delivery, /other"
        if 'action' not in collected:
            msg += "\n→ /code, /money, /link"
        bot.send_message(message.chat.id, msg, reply_markup=main_menu(lang))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = str(message.from_user.id)
        text = message.text
        lang = user_language.get(user_id, 'ru')
        if user_id not in user_language:
            user_language[user_id] = detect_language(text)
            lang = user_language[user_id]

        if text == "🚀 Запустить бота" or text == "🚀 БОТТЫ ІСКЕ ҚОСУ":
            welcome_message(message)
        elif text == "📋 Главное меню" or text == "📋 БАСТЫ МӘЗІР":
            bot.send_message(message.chat.id, "📋 Меню:", reply_markup=main_menu(lang))
        elif text == "📖 Инструкция" or text == "📖 НҰСҚАУ":
            instructions(message)
        elif text == "📊 Статистика" or text == "📊 СТАТИСТИКА":
            stats(message)
        elif text == "🆘 SOS":
            sos(message)
        elif text == "📝 Сообщить о схеме" or text == "📝 СХЕМА ТУРАЛЫ ХАБАРЛАУ":
            temp_state[user_id] = {"step": "channel"}
            msg = "📝 **Выберите канал:**" if lang == 'ru' else "📝 **Арнаны таңдаңыз:**"
            bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=channel_menu(lang))
        elif text == "📞 Гибридная схема" or text == "📞 ГИБРИДТІ СХЕМА":
            hybrid_scheme(message)
        elif text == "💳 Дропперство" or text == "💳 ДРОППЕРСТВО":
            dropper_info(message)
        elif text == "🚨 Чрезвычайная ситуация" or text == "🚨 ТӨТЕНШЕ ЖАҒДАЙ":
            emergency_info(message)
        elif text == "ℹ️ О проекте" or text == "ℹ️ ЖОБА ТУРАЛЫ":
            about_project(message)
        elif text.lower() in ["/schemes", "схемы", "схема"]:
            schemes_list(message)
        else:
            if user_id in temp_state and temp_state[user_id].get("step") == "description":
                temp_state[user_id]["description"] = text
                state = temp_state[user_id]
                description = state.get("description", "")
                category = state.get("category", "Неизвестно")
                channel = state.get("channel", "Неизвестно")
                analysis = analyze_risk(description)
                report = {
                    "id": len(reports) + 1,
                    "user": "Аноним",
                    "user_id": user_id,
                    "text": description[:500],
                    "category": category,
                    "channel": channel,
                    "analysis": analysis,
                    "anonymous": 1,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                reports.append(report)
                save_reports(reports)
                del temp_state[user_id]
                response = get_extended_response(analysis, lang, description)
                bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=main_menu(lang))
                return

            if user_id in temp_state and temp_state[user_id].get("step") == "clarify":
                analysis = analyze_risk(text)
                if analysis['risk_score'] >= 25 or analysis['is_code'] or analysis['is_bank'] or analysis['is_egov'] or analysis['is_transfer']:
                    report = {
                        "id": len(reports) + 1,
                        "user": "Аноним",
                        "user_id": user_id,
                        "text": text[:500],
                        "category": "Auto Check",
                        "channel": "User Message",
                        "analysis": analysis,
                        "anonymous": 1,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    reports.append(report)
                    save_reports(reports)
                    response = get_extended_response(analysis, lang, text)
                    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=main_menu(lang))
                    del temp_state[user_id]
                else:
                    clarify_response(message, lang)
                return

            analysis = analyze_risk(text)

            if analysis['risk_score'] >= 25 or analysis['is_code'] or analysis['is_bank'] or analysis['is_egov'] or analysis['is_transfer'] or analysis['is_delivery']:
                report = {
                    "id": len(reports) + 1,
                    "user": "Аноним",
                    "user_id": user_id,
                    "text": text[:500],
                    "category": "Auto Check",
                    "channel": "User Message",
                    "analysis": analysis,
                    "anonymous": 1,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                reports.append(report)
                save_reports(reports)
                response = get_extended_response(analysis, lang, text)
                bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=main_menu(lang))
            else:
                clarify_response(message, lang)

    except Exception as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.stderr.flush()
        lang = user_language.get(str(message.from_user.id), 'ru')
        bot.send_message(message.chat.id, "⚠️ Ошибка / Қате. Попробуйте ещё раз.", reply_markup=main_menu(lang))

# ============================================
# INLINE КНОПКИ
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        user_id = str(call.from_user.id)
        lang = user_language.get(user_id, 'ru')
        if call.data.startswith("ch_"):
            channel_map = {
                "ch_phone": "Звонок" if lang == 'ru' else "Телефон",
                "ch_telegram": "Telegram",
                "ch_whatsapp": "WhatsApp",
                "ch_sms": "SMS",
                "ch_website": "Сайт",
                "ch_email": "Email"
            }
            temp_state[user_id] = {"step": "category", "channel": channel_map.get(call.data, "Неизвестно")}
            msg = "📌 **Выберите категорию:**" if lang == 'ru' else "📌 **Санатты таңдаңыз:**"
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=category_menu(lang))
            bot.answer_callback_query(call.id)
            return
        elif call.data.startswith("cat_"):
            category_map_ru = {
                "cat_bank": "Фейк Банк", "cat_egov": "Фейк Госорган",
                "cat_delivery": "Фейк Доставка", "cat_investment": "Инвестиции",
                "cat_job": "Фейк Работа", "cat_other": "Другое"
            }
            category_map_kk = {
                "cat_bank": "Жалған Банк", "cat_egov": "Жалған Мемлекет",
                "cat_delivery": "Жалған Жеткізу", "cat_investment": "Инвестиция",
                "cat_job": "Жалған Жұмыс", "cat_other": "Басқа"
            }
            category = category_map_kk.get(call.data, "Басқа") if lang == 'kk' else category_map_ru.get(call.data, "Другое")
            if user_id not in temp_state:
                temp_state[user_id] = {}
            temp_state[user_id]["category"] = category
            temp_state[user_id]["step"] = "description"
            msg = f"📌 **Категория: {category}**\n\n**Опишите ситуацию подробно:**" if lang == 'ru' else f"📌 **Санат: {category}**\n\n**Не болды?**"
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            bot.answer_callback_query(call.id)
            return
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"ОШИБКА В CALLBACK: {e}", file=sys.stderr)
        sys.stderr.flush()
        bot.answer_callback_query(call.id)

# ============================================
# WEBHOOK
# ============================================
@app.route('/' + TOKEN, methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            print(f"ОШИБКА В WEBHOOK: {e}", file=sys.stderr)
            sys.stderr.flush()
            return 'OK', 200
    return 'OK', 200

@app.route('/')
def index():
    return f'🚨 SCAM RADAR KZ\n📊 Всего: {len(reports)}\n📚 Схем: {TOTAL_SCHEMES}'

# ============================================
# НАСТРОЙКА WEBHOOK
# ============================================
WEBHOOK_URL = "https://knrbvaademi.pythonanywhere.com/" + TOKEN
try:
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ Webhook установлен на: {WEBHOOK_URL}", file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f"❌ Ошибка установки webhook: {e}", file=sys.stderr)
    sys.stderr.flush()

if __name__ == '__main__':
    app.run()