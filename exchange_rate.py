import requests
import statistics
import anthropic
import os
from datetime import datetime, timedelta

# ── 텔레그램 설정 ───────────────────────────────────
FX_BOT_TOKEN = "8714388886:AAGOSqNwJd0OyvNNIyuFaAOBbPWNcmpnuxc"
FX_CHAT_ID   = "8783395762"  # 희정만

CURRENCIES = {
    "USD": "🇺🇸",
    "JPY": "🇯🇵",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
}

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{FX_BOT_TOKEN}/sendMessage",
        data={"chat_id": FX_CHAT_ID, "text": message}
    )

def get_rates(start, end):
    url = f"https://api.frankfurter.app/{start}..{end}?from=EUR&to=USD,JPY,GBP,KRW"
    return requests.get(url).json()

def to_krw(rates_by_date, currency):
    result = {}
    for date, rates in rates_by_date.items():
        if currency == "EUR":
            result[date] = rates["KRW"]
        else:
            result[date] = rates["KRW"] / rates[currency]
    return result

# ── 날짜 설정 ───────────────────────────────────────
today = datetime.today()
past_30 = (today - timedelta(days=30)).strftime("%Y-%m-%d")
today_str = today.strftime("%Y-%m-%d")
today_label = today.strftime("%Y년 %-m월 %-d일")

# ── 데이터 수집 ─────────────────────────────────────
data = get_rates(past_30, today_str)
sorted_dates = sorted(data["rates"].keys())

# ── 분석 ───────────────────────────────────────────
rate_lines = [f"📊 오늘의 환율 ({today_label})", "━━━━━━━━━━━━━━━━━━"]
trend_lines = []
timing_lines = []
ai_data = {}

for currency, flag in CURRENCIES.items():
    krw = to_krw(data["rates"], currency)
    dates = sorted(krw.keys())

    today_rate    = krw[dates[-1]]
    yesterday_rate = krw[dates[-2]]
    week_ago_rate = krw[dates[max(0, len(dates)-8)]]
    all_rates     = [krw[d] for d in dates]
    week_rates    = all_rates[-7:]

    diff_day      = today_rate - yesterday_rate
    diff_week_pct = (today_rate - week_ago_rate) / week_ago_rate * 100
    avg_30        = statistics.mean(all_rates)
    max_30        = max(all_rates)
    min_30        = min(all_rates)
    volatility    = statistics.stdev(week_rates) / statistics.mean(week_rates) * 100

    # 환율 라인
    arrow = f"▲{diff_day:+.1f}원" if diff_day > 0 else f"▼{diff_day:.1f}원"
    if currency == "JPY":
        rate_lines.append(f"{flag} JPY 100엔: {today_rate*100:,.0f}원 (어제보다 {arrow})")
    else:
        rate_lines.append(f"{flag} {currency}: {today_rate:,.0f}원 (어제보다 {arrow})")

    # 트렌드
    trend = "📈 상승세" if diff_week_pct > 1 else ("📉 하락세" if diff_week_pct < -1 else "➡️ 횡보")
    vol_str = "안정적" if volatility < 0.5 else ("보통" if volatility < 1.5 else "변동 큼")
    trend_lines.append(f"{flag} {currency}: {trend} ({diff_week_pct:+.1f}%, 변동성 {vol_str})")

    # 송금 타이밍 신호
    pct_from_min = (today_rate - min_30) / (max_30 - min_30) * 100 if max_30 != min_30 else 50
    if pct_from_min <= 20:
        signal = "🟢 매수 유리 (30일 최저 근접)"
    elif pct_from_min >= 80:
        signal = "🔴 매수 불리 (30일 최고 근접)"
    else:
        signal = "🟡 중립"
    timing_lines.append(f"{flag} {currency}: {signal}")

    # AI용 데이터
    ai_data[currency] = {
        "today": round(today_rate, 2),
        "avg_30": round(avg_30, 2),
        "diff_week_pct": round(diff_week_pct, 2),
        "volatility": round(volatility, 2),
        "pct_from_min": round(pct_from_min, 1),
    }

# ── Claude AI 인사이트 ──────────────────────────────
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        import tomllib
        with open(os.path.expanduser("~/가계부분析/.streamlit/secrets.toml"), "rb") as f:
            secrets = tomllib.load(f)
        api_key = secrets["ANTHROPIC_API_KEY"]

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""
다음은 오늘({today_label}) 환율 데이터야:
{ai_data}

나는 해외송금회사의 수익전략개발자야.
이 데이터를 보고 해외송금 비즈니스 관점에서 핵심 인사이트 2~3줄로 짧게 알려줘.
예) 원가 상승/하락 영향, 주목할 통화, 오늘의 전략 포인트 등.
이모지 사용해서 읽기 쉽게 써줘.
"""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    ai_insight = response.content[0].text
except Exception as e:
    ai_insight = f"(AI 분석 오류: {e})"

# ── 메시지 조합 ─────────────────────────────────────
msg = "\n".join(rate_lines)
msg += "\n\n📈 7일 트렌드 & 변동성\n━━━━━━━━━━━━━━━━━━\n"
msg += "\n".join(trend_lines)
msg += "\n\n🎯 송금 타이밍 신호\n━━━━━━━━━━━━━━━━━━\n"
msg += "\n".join(timing_lines)
msg += "\n\n💬 AI 인사이트\n━━━━━━━━━━━━━━━━━━\n"
msg += ai_insight

print(msg)
print("\n발송 중...")
send_telegram(msg)
print("✅ 완료!")
