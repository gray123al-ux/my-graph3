
import streamlit as st
import pandas as pd
import requests
import re
import plotly.express as px

st.set_page_config(
    page_title="2020 송탄고등학교 급식 열량",
    layout="wide"
)

st.title("2020년 송탄고등학교 급식 열량")
st.write("NEIS API에서 2020년 중식 데이터를 가져와 날짜별 열량을 그래프로 보여줍니다.")

# =========================
# 기본 설정
# =========================

API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

# 송탄고등학교
ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

# Streamlit Secrets에서 API 키 가져오기
# .streamlit/secrets.toml
# NEIS_KEY = "발급받은_인증키"
NEIS_KEY = st.secrets.get("NEIS_KEY", "")

if not NEIS_KEY:
    st.error("NEIS_KEY가 설정되지 않았습니다.")
    st.info("""
    Streamlit Cloud의 Settings → Secrets에 다음과 같이 입력하세요.

    NEIS_KEY = "발급받은_인증키"
    """)
    st.stop()


# =========================
# NEIS API 호출
# =========================

@st.cache_data
def load_meal_data():

    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,

        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,

        # 중식
        "MMEAL_SC_CODE": 2,

        # 2020년 전체
        "MLSV_FROM_YMD": "20200101",
        "MLSV_TO_YMD": "20201231"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    # 데이터가 없는 경우
    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    meal_info = data["mealServiceDietInfo"]

    if len(meal_info) < 2:
        return pd.DataFrame()

    rows = meal_info[1].get("row", [])

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df


# =========================
# 데이터 가져오기
# =========================

with st.spinner("2020년 급식 데이터를 불러오는 중입니다..."):
    df = load_meal_data()


if df.empty:
    st.warning("2020년 급식 데이터를 찾을 수 없습니다.")
    st.stop()


# =========================
# 날짜와 열량 정리
# =========================

df["날짜"] = pd.to_datetime(
    df["MLSV_YMD"],
    format="%Y%m%d",
    errors="coerce"
)


# CAL_INFO 예:
# "748.1 Kcal"
# "1055.0 Kcal"

df["열량"] = (
    df["CAL_INFO"]
    .astype(str)
    .str.extract(r"([\d.]+)", expand=False)
)

df["열량"] = pd.to_numeric(
    df["열량"],
    errors="coerce"
)


# 날짜순 정렬
df = df.sort_values("날짜")

# 열량이 없는 데이터 제거
graph_df = df.dropna(subset=["날짜", "열량"]).copy()


# =========================
# 요약 통계
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "급식 데이터 수",
    f"{len(graph_df):,}일"
)

col2.metric(
    "평균 열량",
    f"{graph_df['열량'].mean():,.1f} kcal"
)

col3.metric(
    "최고 열량",
    f"{graph_df['열량'].max():,.1f} kcal"
)

col4.metric(
    "최저 열량",
    f"{graph_df['열량'].min():,.1f} kcal"
)


# =========================
# 그래프
# =========================

st.subheader("날짜별 급식 열량")

fig = px.line(
    graph_df,
    x="날짜",
    y="열량",
    markers=True,
    labels={
        "날짜": "날짜",
        "열량": "열량 (kcal)"
    },
    hover_data={
        "날짜": "|%Y-%m-%d",
        "열량": ":.1f"
    }
)

fig.update_layout(
    xaxis_title="날짜",
    yaxis_title="열량 (kcal)",
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================
# 평균선
# =========================

average_calories = graph_df["열량"].mean()

st.info(
    f"2020년 중식의 평균 열량은 "
    f"**{average_calories:,.1f} kcal**입니다."
)


# =========================
# 원본 데이터
# =========================

with st.expander("급식 데이터 보기"):

    display_df = graph_df[
        [
            "날짜",
            "SCHUL_NM",
            "MMEAL_SC_NM",
            "DDISH_NM",
            "열량",
            "ORPLC_INFO"
        ]
    ].copy()

    display_df.columns = [
        "날짜",
        "학교",
        "식사",
        "메뉴",
        "열량 (kcal)",
        "원산지"
    ]

    # <br/>을 줄바꿈으로 변경
    display_df["메뉴"] = (
        display_df["메뉴"]
        .astype(str)
        .str.replace("<br/>", "\n", regex=False)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
