import requests
import json
from datetime import datetime
import pandas as pd
from supabase import create_client
from kakao_token import load_tokens

# ── Supabase 연결 ──────────────────────────────────────
SUPABASE_URL = "https://axzfcsqkfpgraetawgqp.supabase.co"
SUPABASE_KEY = "sb_publishable_msAtmlySUP3-6KtP4Cjflw_21wAm8cd"
db = create_client(SUPABASE_URL, SUPABASE_KEY)

SAVING_CATS = ['기태 예금', '기태 주택청약', '기태 IRP', '희정 적금', '희정 주택청약', '희정 IRP']
INVEST_CATS = ['기태 주식', '희정 주식']

TOKEN_WIFE, TOKEN_HUSBAND = load_tokens()

# ── 카카오 메시지 발송 ─────────────────────────────────
def send_kakao(token, message):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message,
            "link": {"web_url": "https://choigang-budget.streamlit.app"}
        }, ensure_ascii=False)
    }
    res = requests.post(url, headers={"Authorization": f"Bearer {token}"}, data=data)
    return res.json()

def send_both(message):
    r1 = send_kakao(TOKEN_WIFE, message)
    r2 = send_kakao(TOKEN_HUSBAND, message)
    print(f"  희정: {r1} / 기태: {r2}")

# ── 데이터 로드 ────────────────────────────────────────
today = datetime.today()
this_month = today.strftime("%Y-%m")
this_year  = today.strftime("%Y")

response = db.table("transactions").select("*").execute()
df = pd.DataFrame(response.data)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%Y-%m")
df["year"]  = df["date"].dt.strftime("%Y")

def classify(c):
    if c in SAVING_CATS:
        return "저축"
    if c in INVEST_CATS:
        return "투자"
    return "소비"

# ── 이번 달 집계 ───────────────────────────────────────
monthly = df[df["month"] == this_month].copy()
expense = monthly[monthly["type"] == "expense"].copy()
expense["분류"] = expense["category"].apply(classify)

income_total  = int(monthly[monthly["type"] == "income"]["amount"].sum())
consume_total = int(expense[expense["분류"] == "소비"]["amount"].sum())
saving_total  = int(expense[expense["분류"] == "저축"]["amount"].sum())
invest_total  = int(expense[expense["분류"] == "투자"]["amount"].sum())

saving_rate = (saving_total / income_total * 100) if income_total > 0 else 0

top3 = expense[expense["분류"] == "소비"].groupby("category")["amount"].sum().sort_values(ascending=False).head(3)
top3_str = ""
for i, (cat, amt) in enumerate(top3.items(), 1):
    top3_str += f"{i}. {cat}: {amt/10000:.0f}만원\n"

# ── 올해 누적 집계 ─────────────────────────────────────
yearly_exp = df[(df["year"] == this_year) & (df["type"] == "expense")].copy()
yearly_exp["분류"] = yearly_exp["category"].apply(classify)

yearly_consume = int(yearly_exp[yearly_exp["분류"] == "소비"]["amount"].sum())
yearly_saving  = int(yearly_exp[yearly_exp["분류"] == "저축"]["amount"].sum())
yearly_invest  = int(yearly_exp[yearly_exp["분류"] == "투자"]["amount"].sum())

# ── 메시지 작성 ────────────────────────────────────────
month_label = today.strftime("%Y년 %-m월")

msg = (
    f"📅 {month_label} 월간 리포트\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"💰 수입: {income_total/10000:.0f}만원\n"
    f"💸 소비: {consume_total/10000:.0f}만원\n"
    f"🏦 저축: {saving_total/10000:.0f}만원\n"
    f"📈 투자: {invest_total/10000:.0f}만원\n\n"
    f"🥧 이번 달 TOP 3 지출\n"
    f"{top3_str}\n"
    f"💾 이번 달 저축률: {saving_rate:.1f}%\n\n"
    f"📊 {this_year}년 누적\n"
    f"💸 소비: {yearly_consume/10000:.0f}만원\n"
    f"🏦 저축: {yearly_saving/10000:.0f}만원\n"
    f"📈 투자: {yearly_invest/10000:.0f}만원"
)

print(msg)
print("\n발송 중...")
send_both(msg)
print("✅ 완료!")
