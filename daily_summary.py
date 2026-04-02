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
BUDGET_STEPS = [1000000, 1500000, 2000000, 2500000, 3000000]
STEP_LABELS  = ["100만원", "150만원", "200만원", "250만원", "300만원"]

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

# ── 이번 달 데이터 계산 ────────────────────────────────
today = datetime.today()
this_month = today.strftime("%Y-%m")

response = db.table("transactions").select("*").execute()
df = pd.DataFrame(response.data)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%Y-%m")

monthly = df[df["month"] == this_month].copy()
expense = monthly[monthly["type"] == "expense"].copy()
expense["분류"] = expense["category"].apply(
    lambda c: "저축" if c in SAVING_CATS else ("투자" if c in INVEST_CATS else "소비")
)

consume_total = int(expense[expense["분류"] == "소비"]["amount"].sum())
saving_total  = int(expense[expense["분류"] == "저축"]["amount"].sum())
invest_total  = int(expense[expense["분류"] == "투자"]["amount"].sum())

# 다음 예산 단계까지 남은 금액
remaining = [(s, l) for s, l in zip(BUDGET_STEPS, STEP_LABELS) if consume_total < s]
if remaining:
    next_step, next_label = remaining[0]
    next_msg = f"⏳ {next_label}까지 {next_step - consume_total:,}원 남음"
else:
    next_msg = "⚠️ 모든 예산 단계 초과!"

# ── 메시지 작성 ────────────────────────────────────────
msg = (
    f"📊 기태희정의 가계부 일일 리포트\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"📅 {this_month} 누계 ({today.day}일 기준)\n\n"
    f"💸 소비: {consume_total:,}원\n"
    f"🏦 저축: {saving_total:,}원\n"
    f"📈 투자: {invest_total:,}원\n\n"
    f"{next_msg}"
)

print(msg)
print("\n발송 중...")
send_both(msg)
print("✅ 완료!")
