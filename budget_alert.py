import requests
import os
import json
from datetime import datetime
import pandas as pd
import sys
sys.path.append(os.path.expanduser("~/가계부분석"))
from sample_data import df as raw_df

# ── 설정 ──────────────────────────────────────────────
BUDGET_STEPS = [1000000, 1500000, 2000000, 2500000, 3000000]  # 100만~300만
STEP_LABELS  = ["100만원", "150만원", "200만원", "250만원", "300만원"]
ALERT_LOG    = os.path.expanduser("~/가계부분析/alert_log.json")

SAVING_CATS = ['기태 예금', '기태 주택청약', '기태 IRP', '희정 적금', '희정 주택청약', '희정 IRP']
INVEST_CATS = ['기태 주식', '희정 주식']

# ── 토큰 로드 ──────────────────────────────────────────
tokens = {}
with open(os.path.expanduser("~/가계부분析/.env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            tokens[key] = val

TOKEN_WIFE    = tokens.get("KAKAO_ACCESS_TOKEN")
TOKEN_HUSBAND = tokens.get("KAKAO_ACCESS_TOKEN_HUSBAND")

# ── 카카오 메시지 발송 함수 ────────────────────────────
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

df = raw_df.copy()
expense = df[(df["type"] == "expense") & (df["month"] == this_month)].copy()
expense["분류"] = expense["category"].apply(
    lambda c: "저축" if c in SAVING_CATS else ("투자" if c in INVEST_CATS else "소비")
)

consume_total = int(expense[expense["분류"] == "소비"]["amount"].sum())

print(f"📅 {this_month} 소비 합계: {consume_total:,}원")
print()

# ── 알림 로그 불러오기 (이미 보낸 단계 확인) ────────────
if os.path.exists(ALERT_LOG):
    with open(ALERT_LOG) as f:
        log = json.load(f)
else:
    log = {}

sent_steps = log.get(this_month, [])

# ── 초과된 단계 알림 발송 ──────────────────────────────
new_alerts = []
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
        new_alerts.append(label)

# ── 아직 안 넘은 다음 단계 안내 ────────────────────────
remaining_steps = [
    (step, label) for step, label in zip(BUDGET_STEPS, STEP_LABELS)
    if consume_total < step
]
if remaining_steps:
    next_step, next_label = remaining_steps[0]
    left = next_step - consume_total
    print(f"✅ 다음 알림 기준 [{next_label}]까지 {left:,}원 남았어요.")
else:
    print("⚠️ 모든 예산 단계를 초과했어요!")

# ── 로그 저장 ──────────────────────────────────────────
if new_alerts:
    log[this_month] = sent_steps + new_alerts
    with open(ALERT_LOG, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\n📝 알림 로그 저장: {new_alerts}")
else:
    if not sent_steps:
        print("\n✅ 아직 초과된 예산 단계가 없어요.")
    else:
        print(f"\n✅ 이미 발송된 알림: {sent_steps} (중복 발송 없음)")
