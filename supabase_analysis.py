import pandas as pd
from supabase import create_client

# ── Supabase 연결 ──────────────────────────────────────
SUPABASE_URL = "https://axzfcsqkfpgraetawgqp.supabase.co"
SUPABASE_KEY = "sb_publishable_msAtmlySUP3-6KtP4Cjflw_21wAm8cd"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 데이터 불러오기 ────────────────────────────────────
print("📡 Supabase에서 데이터 불러오는 중...")
response = db.table("transactions").select("*").order("date").execute()
data = response.data

if not data:
    print("❌ 데이터가 없어요. 가계부 앱에서 먼저 거래를 입력해주세요!")
else:
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")

    print(f"✅ 총 {len(df)}건 로드 완료!")
    print(f"   기간: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    print()

    # 월별 요약
    monthly = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0)
    print("📊 월별 수입/지출 요약")
    print(monthly.to_string())
    print()

    # 카테고리별 지출 TOP 5
    top5 = (df[df["type"] == "expense"]
            .groupby("category")["amount"].sum()
            .sort_values(ascending=False)
            .head(5))
    print("💸 지출 TOP 5 카테고리")
    for cat, amt in top5.items():
        print(f"  {cat:<12} {int(amt):>9,}원")
