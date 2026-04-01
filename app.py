import streamlit as st
from supabase import create_client
from datetime import date

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="최강부부 가계부",
    page_icon="💑",
    layout="centered"
)

# ── Supabase 연결 ──────────────────────────────────────
SUPABASE_URL = "https://axzfcsqkfpgraetawgqp.supabase.co"
SUPABASE_KEY = "sb_publishable_msAtmlySUP3-6KtP4Cjflw_21wAm8cd"
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 카테고리 목록 ──────────────────────────────────────
INCOME_CATS = ["희정 급여", "기태 급여", "희정 기타수입", "기태 기타수입"]

EXPENSE_CATS = [
    # 소비
    "식비", "생활비", "교통비", "통신비", "의료비",
    "보험료", "육아용품", "희정용돈", "기태용돈", "기타지출",
    # 저축
    "희정 적금", "희정 주택청약", "희정 IRP",
    "기태 예금", "기태 주택청약", "기태 IRP",
    # 투자
    "희정 주식", "기태 주식",
]

ACCOUNTS = ["토스부부통장", "희정개인계좌", "기태개인계좌"]

# ── UI ─────────────────────────────────────────────────
st.title("💑 최강부부 가계부")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    input_date = st.date_input("📅 날짜", value=date.today())

with col2:
    tx_type = st.selectbox("💳 유형", ["expense", "income"],
                           format_func=lambda x: "지출" if x == "expense" else "수입")

category_list = EXPENSE_CATS if tx_type == "expense" else INCOME_CATS
category = st.selectbox("📂 카테고리", category_list)

amount = st.number_input("💰 금액 (원)", min_value=0, step=1000, format="%d")

col3, col4 = st.columns(2)

with col3:
    created_by = st.selectbox("👤 입력자", ["희정", "기태"])

with col4:
    account = st.selectbox("🏦 계좌", ACCOUNTS)

st.markdown("---")

# ── 저장 버튼 ──────────────────────────────────────────
if st.button("💾 저장하기", use_container_width=True, type="primary"):
    if amount == 0:
        st.warning("금액을 입력해주세요!")
    else:
        try:
            db.table("transactions").insert({
                "date": str(input_date),
                "type": tx_type,
                "category": category,
                "amount": amount,
                "created_by": created_by,
                "account": account,
            }).execute()
            st.success(f"✅ 저장 완료! {category} {amount:,}원")
            st.balloons()
        except Exception as e:
            st.error(f"❌ 저장 실패: {e}")

# ── 최근 내역 보기 ─────────────────────────────────────
st.markdown("---")
if st.button("📋 최근 내역 보기", use_container_width=True):
    try:
        res = db.table("transactions").select("*").order("date", desc=True).limit(10).execute()
        if res.data:
            import pandas as pd
            df = pd.DataFrame(res.data)
            df = df[["date", "type", "category", "amount", "created_by", "account"]]
            df.columns = ["날짜", "유형", "카테고리", "금액", "입력자", "계좌"]
            df["유형"] = df["유형"].map({"expense": "지출", "income": "수입"})
            df["금액"] = df["금액"].apply(lambda x: f"{int(x):,}원")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("아직 입력된 내역이 없어요.")
    except Exception as e:
        st.error(f"❌ 불러오기 실패: {e}")
