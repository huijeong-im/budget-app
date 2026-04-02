import streamlit as st
from supabase import create_client
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# ── 카테고리 설정 ──────────────────────────────────────
SAVING_CATS = ['기태 예금', '기태 주택청약', '기태 IRP', '희정 적금', '희정 주택청약', '희정 IRP']
INVEST_CATS = ['기태 주식', '희정 주식']
INCOME_CATS = ["희정 급여", "기태 급여", "희정 기타수입", "기태 기타수입"]
EXPENSE_CATS = [
    "식비", "생활비", "교통비", "통신비", "의료비",
    "보험료", "육아용품", "희정용돈", "기태용돈", "기타지출",
    "희정 적금", "희정 주택청약", "희정 IRP",
    "기태 예금", "기태 주택청약", "기태 IRP",
    "희정 주식", "기태 주식",
]
ACCOUNTS = ["토스부부통장", "희정개인계좌", "기태개인계좌"]
BUDGET_STEPS = [1000000, 1500000, 2000000, 2500000, 3000000]
STEP_LABELS  = ["100만원", "150만원", "200만원", "250만원", "300만원"]

# ── 데이터 로드 ────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    res = db.table("transactions").select("*").execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    df["분류"] = df["category"].apply(
        lambda c: "저축" if c in SAVING_CATS else ("투자" if c in INVEST_CATS else ("수입" if df.loc[df["category"]==c, "type"].iloc[0] == "income" else "소비"))
    )
    return df

# ── 탭 구성 ────────────────────────────────────────────
st.title("💑 최강부부 가계부")
tab1, tab2 = st.tabs(["📝 입력", "📊 대시보드"])

# ════════════════════════════════════════════════════
# 탭 1: 입력
# ════════════════════════════════════════════════════
with tab1:
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
                st.cache_data.clear()
                st.balloons()
            except Exception as e:
                st.error(f"❌ 저장 실패: {e}")

# ════════════════════════════════════════════════════
# 탭 2: 대시보드
# ════════════════════════════════════════════════════
with tab2:
    df = load_data()

    if df.empty:
        st.info("아직 입력된 데이터가 없어요. 먼저 거래를 입력해주세요!")
    else:
        # 월 선택
        months = sorted(df["month"].unique(), reverse=True)
        selected_month = st.selectbox("📅 월 선택", months)

        monthly_df = df[df["month"] == selected_month]
        expense_df = monthly_df[monthly_df["type"] == "expense"].copy()
        expense_df["분류"] = expense_df["category"].apply(
            lambda c: "저축" if c in SAVING_CATS else ("투자" if c in INVEST_CATS else "소비")
        )

        income_total  = int(monthly_df[monthly_df["type"] == "income"]["amount"].sum())
        consume_total = int(expense_df[expense_df["분류"] == "소비"]["amount"].sum())
        saving_total  = int(expense_df[expense_df["분류"] == "저축"]["amount"].sum())
        invest_total  = int(expense_df[expense_df["분류"] == "투자"]["amount"].sum())

        # ── 요약 카드 ──────────────────────────────────
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 수입",  f"{income_total/10000:.0f}만원")
        c2.metric("💸 소비",  f"{consume_total/10000:.0f}만원")
        c3.metric("🏦 저축",  f"{saving_total/10000:.0f}만원")
        c4.metric("📈 투자",  f"{invest_total/10000:.0f}만원")

        # ── 예산 진행바 ────────────────────────────────
        st.markdown("---")
        st.markdown("**💳 이번달 소비 예산 진행**")
        next_steps = [(s, l) for s, l in zip(BUDGET_STEPS, STEP_LABELS) if consume_total < s]
        if next_steps:
            next_step, next_label = next_steps[0]
            progress = min(consume_total / next_step, 1.0)
            st.progress(progress)
            st.caption(f"{consume_total:,}원 / {next_step:,}원 ({next_label}까지 {next_step - consume_total:,}원 남음)")
        else:
            st.progress(1.0)
            st.caption(f"⚠️ 모든 예산 단계 초과! 현재 {consume_total:,}원")

        # ── 월별 수입/지출 차트 ────────────────────────
        st.markdown("---")
        st.markdown("**📊 월별 수입 / 지출**")
        monthly_summary = df.groupby(["month", "type"])["amount"].sum().reset_index()
        monthly_summary["type"] = monthly_summary["type"].map({"income": "수입", "expense": "지출"})
        monthly_summary["amount_만"] = (monthly_summary["amount"] / 10000).round(0)
        fig1 = px.bar(monthly_summary, x="month", y="amount_만", color="type",
                      barmode="group",
                      color_discrete_map={"수입": "#3b82f6", "지출": "#f43f5e"},
                      labels={"month": "", "amount_만": "금액 (만원)", "type": ""},
                      text="amount_만")
        fig1.update_traces(texttemplate="%{text:.0f}만", textposition="outside")
        fig1.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig1, use_container_width=True)

        # ── 카테고리별 소비 파이차트 ───────────────────
        st.markdown("---")
        st.markdown("**🥧 카테고리별 소비**")
        cat_df = expense_df[expense_df["분류"] == "소비"].groupby("category")["amount"].sum().reset_index()
        if not cat_df.empty:
            fig2 = px.pie(cat_df, values="amount", names="category",
                          hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("이번달 소비 데이터가 없어요.")

