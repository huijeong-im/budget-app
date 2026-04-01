import requests
import os
import json
from datetime import datetime
import pandas as pd
from supabase import create_client

# ── Supabase 연결 ──────────────────────────────────────
SUPABASE_URL = "https://axzfcsqkfpgraetawgqp.supabase.co"
SUPABASE_KEY = "sb_publishable_msAtmlySUP3-6KtP4Cjflw_21wAm8cd"
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 설정 ──────────────────────────────────────────────
BUDGET_STEPS = [1000000, 1500000, 2000000, 2500000, 3000000]
STEP_LABELS  = ["100만원", "150만원", "200만원", "250만원", "300만원"]

SAVING_CATS = ['기태 예금', '기태 주택청약', '기태 IRP', '희정 적금', '희정 주택청약', '희정 IRP']
INVEST_CATS = ['기태 주식', '희정 주식']

# ── 토큰 로드 (로컬은 .env, GitHub Actions는 환경변수) ──
def load_tokens():
    # 환경변수 먼저 확인 (GitHub Actions)
    wife    = os.environ.get("KAKAO_ACCESS_TOKEN")
    husband = os.environ.get("KAKAO_ACCESS_TOKEN_HUSBAND")
    if wife and husband:
        return wife, husband
    # 없으면 .env 파일에서 읽기 (로컬)
    env_path = os.path.expanduser("~/가계부분析/.env")
    tokens = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, val = line.split("=", 1)
                tokens[key] = val
    return tokens["KAKAO_ACCESS_TOKEN"], tokens["KAKAO_ACCESS_TOKEN_HUSBAND"]

TOKEN_WIFE, TOKEN_HUSBAND = load_tokens()

# ── 카카오 메시지 발송 ─────────────────────────────────
def send_kakao(token, message):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message,
            "link": {"web_url": "https://example.com"}
        }, ensure_ascii=False)
    }
    res = requests.post(url, headers={"Authorization": f"Bearer {token}"}, data=data)
    return res.json()

def send_both(message):
    r1 = send_kakao(TOKEN_WIFE, message)
    r2 = send_kakao(TOKEN_HUSBAND, message)
    print(f"  희정: {r1} / 기태: {r2}")

# ── 이번 달 소비 계산 ──────────────────────────────────
today = datetime.today()
this_month = today.strftime("%Y-%m")

response = db.table("transactions").select("*").execute()
df = pd.DataFrame(response.data)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%Y-%m")

expense = df[(df["type"] == "expense") & (df["month"] == this_month)].copy()
expense["분류"] = expense["category"].apply(
    lambda c: "저축" if c in SAVING_CATS else ("투자" if c in INVEST_CATS else "소비")
)
consume_total = int(expense[expense["분류"] == "소비"]["amount"].sum())

print(f"📅 {this_month} 소비 합계: {consume_total:,}원")

# ── 이미 보낸 알림 확인 (Supabase) ────────────────────
sent = db.table("alert_log").select("label").eq("month", this_month).execute()
sent_steps = [row["label"] for row in sent.data]

# ── 초과된 단계 알림 발송 ──────────────────────────────
for step, label in zip(BUDGET_STEPS, STEP_LABELS):
    if consume_total >= step and label not in sent_steps:
        over = consume_total - step
        msg = (
            f"⚠️ 최강부부 가계부 예산 알림\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 {this_month} 소비가 {label}을 넘었어요!\n\n"
            f"💸 현재 소비: {consume_total:,}원\n"
            f"📊 예산 기준: {step:,}원\n"
            f"🔴 초과 금액: {over:,}원\n\n"
            f"저축·투자 제외 순수 소비 기준입니다."
        )
        print(f"🚨 [{label} 초과] 알림 발송!")
        send_both(msg)
        db.table("alert_log").insert({"month": this_month, "label": label}).execute()

# ── 다음 단계 안내 ─────────────────────────────────────
remaining = [(s, l) for s, l in zip(BUDGET_STEPS, STEP_LABELS) if consume_total < s]
if remaining:
    next_step, next_label = remaining[0]
    print(f"✅ 다음 알림 기준 [{next_label}]까지 {next_step - consume_total:,}원 남았어요.")
else:
    print("⚠️ 모든 예산 단계를 초과했어요!")
