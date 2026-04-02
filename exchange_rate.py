import requests
import statistics
from datetime import datetime, timedelta

BOT_TOKEN = "8533743870:AAGvNrJ2uEXg-dcr9Yzdmu82lndimMJtsCA"
CHAT_IDS = ["8783395762", "7169251813"]

CURRENCIES = {
    "USD": "🇺🇸",
    "JPY": "🇯🇵",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
}

def get_rates(start, end):
    """frankfurter.app에서 EUR 기준 환율 가져오기"""
    url = f"https://api.frankfurter.app/{start}..{end}?from=EUR&to=USD,JPY,GBP,KRW"
    res = requests.get(url)
    return res.json()

def to_krw(rates_by_date, currency):
    """EUR 기준 데이터를 KRW 기준으로 변환"""
    result = {}
    for date, rates in rates_by_date.items():
        if currency == "EUR":
            result[date] = rates["KRW"]
        else:
            result[date] = rates["KRW"] / rates[currency]
    return result

def send_telegram(message):
    for chat_id in CHAT_IDS:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )

# ── 날짜 설정 ───────────────────────────────────────
today = datetime.today()
past_30 = (today - timedelta(days=30)).strftime("%Y-%m-%d")
today_str = today.strftime("%Y-%m-%d")
today_label = today.strftime("%Y년 %-m월 %-d일")

# ── 데이터 가져오기 ─────────────────────────────────
data = get_rates(past_30, today_str)
dates = sorted(data["rates"].keys())

# ── 분석 ───────────────────────────────────────────
lines = [f"📊 오늘의 환율 ({today_label})", "━━━━━━━━━━━━━━━━━━"]

trend_summary = []

for currency, flag in CURRENCIES.items():
    krw_by_date = to_krw(data["rates"], currency)
    sorted_dates = sorted(krw_by_date.keys())

    today_rate = krw_by_date[sorted_dates[-1]]
    yesterday_rate = krw_by_date[sorted_dates[-2]]
    week_ago_rate = krw_by_date[sorted_dates[max(0, len(sorted_dates)-8)]]

    diff_day = today_rate - yesterday_rate
    diff_week_pct = (today_rate - week_ago_rate) / week_ago_rate * 100

    # 어제 대비
    if diff_day > 0:
        day_str = f"▲{diff_day:+.1f}원"
    elif diff_day < 0:
        day_str = f"▼{diff_day:.1f}원"
    else:
        day_str = "변동없음"

    # JPY는 100엔 기준
    if currency == "JPY":
        lines.append(f"{flag} JPY 100엔: {today_rate*100:,.0f}원 (어제보다 {day_str})")
    else:
        lines.append(f"{flag} {currency}: {today_rate:,.0f}원 (어제보다 {day_str})")

    # 트렌드 분석
    all_rates = [krw_by_date[d] for d in sorted_dates]
    week_rates = all_rates[-7:]
    month_rates = all_rates

    volatility = statistics.stdev(week_rates) / statistics.mean(week_rates) * 100

    if diff_week_pct > 1:
        trend = "📈 상승세"
    elif diff_week_pct < -1:
        trend = "📉 하락세"
    else:
        trend = "➡️ 횡보"

    if volatility < 0.5:
        vol_str = "안정적"
    elif volatility < 1.5:
        vol_str = "보통"
    else:
        vol_str = "변동 큼"

    trend_summary.append(
        f"{flag} {currency}: {trend} ({diff_week_pct:+.1f}%, 변동성 {vol_str})"
    )

lines.append("")
lines.append("📈 7일 트렌드 & 변동성")
lines.append("━━━━━━━━━━━━━━━━━━")
lines.extend(trend_summary)

msg = "\n".join(lines)
print(msg)
print("\n발송 중...")
send_telegram(msg)
print("✅ 완료!")
