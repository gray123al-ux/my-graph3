import re
import calendar
from datetime import date

import pandas as pd
import requests
import plotly.express as px
import streamlit as st


# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="급식의 한 달 평균 칼로리는 얼마나 될까?",
    page_icon="🍚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# 디자인
# ==================================================
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #FFF9F0;
    }

    /* 메인 영역 */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* 제목 */
    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        color: #4A3525;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.05rem;
        color: #806F60;
        margin-bottom: 2rem;
    }

    /* 섹션 제목 */
    .section-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #4A3525;
        margin-top: 2rem;
        margin-bottom: 0.8rem;
    }

    /* 설명 박스 */
    .info-box {
        background-color: #FFF3D8;
        border-left: 5px solid #F2B84B;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        color: #5B4636;
        margin: 1rem 0 1.5rem 0;
    }

    /* 카드 */
    .stat-card {
        background-color: white;
        border-radius: 18px;
        padding: 1.3rem;
        box-shadow: 0 4px 14px rgba(90, 65, 40, 0.08);
        border: 1px solid #F1E5D6;
        min-height: 145px;
    }

    .stat-label {
        font-size: 0.95rem;
        color: #88796D;
        margin-bottom: 0.4rem;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: #4A3525;
    }

    .stat-description {
        font-size: 0.85rem;
        color: #9A8B7D;
        margin-top: 0.4rem;
    }

    /* 그래프 카드 */
    .chart-card {
        background-color: white;
        border-radius: 18px;
        padding: 0.8rem 1rem 0.3rem 1rem;
        box-shadow: 0 4px 14px rgba(90, 65, 40, 0.06);
        border: 1px solid #F1E5D6;
        margin-bottom: 1rem;
    }

    /* 알 수 있는 것 */
    .what-box {
        background-color: #F8F3EC;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.8rem 0 2rem 0;
        color: #5E5146;
    }

    .what-title {
        font-weight: 750;
        color: #6A4E35;
        margin-bottom: 0.3rem;
    }

    /* 높은 날 / 낮은 날 */
    .meal-card {
        background-color: white;
        border-radius: 18px;
        padding: 1.3rem;
        border: 1px solid #F1E5D6;
        box-shadow: 0 4px 14px rgba(90, 65, 40, 0.06);
        min-height: 260px;
    }

    .meal-card-title {
        font-size: 1.2rem;
        font-weight: 750;
        color: #4A3525;
    }

    .meal-date {
        font-size: 1rem;
        color: #88796D;
        margin-top: 0.5rem;
    }

    .meal-kcal {
        font-size: 1.8rem;
        font-weight: 800;
        color: #C47D26;
        margin: 0.5rem 0;
    }

    .menu-text {
        color: #65584E;
        line-height: 1.7;
        white-space: pre-line;
    }

    /* 참고자료 */
    .reference-box {
        background-color: white;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #F1E5D6;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #FFF3DD;
    }

    .sidebar-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #4A3525;
    }

    .sidebar-school {
        background-color: white;
        padding: 1rem;
        border-radius: 14px;
        margin: 1rem 0;
        border: 1px solid #F1E5D6;
    }

    /* Streamlit metric 숨김 스타일 대신 직접 카드 사용 */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 16px;
        padding: 1rem;
    }

    /* 링크 */
    a {
        color: #B36B20 !important;
        font-weight: 600;
    }

    /* 모바일 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }

        .stat-value {
            font-size: 1.6rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 학교 / API 정보
# ==================================================
ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# ==================================================
# NEIS 데이터 가져오기
# ==================================================
@st.cache_data(ttl=3600)
def get_meal_data(year, month):

    last_day = calendar.monthrange(year, month)[1]

    from_ymd = f"{year}{month:02d}01"
    to_ymd = f"{year}{month:02d}{last_day:02d}"

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": from_ymd,
        "MLSV_TO_YMD": to_ymd,
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except requests.exceptions.RequestException as e:
        return pd.DataFrame(), f"API 연결 오류: {e}"

    except ValueError:
        return pd.DataFrame(), "API에서 올바른 JSON 데이터를 받지 못했습니다."

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame(), None

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
    except (KeyError, IndexError):
        return pd.DataFrame(), None

    result = []

    for row in rows:

        meal_date = row.get("MLSV_YMD", "")
        menu = row.get("DDISH_NM", "")

        # <br/> → 줄바꿈
        menu = re.sub(
            r"<br\s*/?>",
            "\n",
            menu
        )

        # kcal 추출
        kcal_match = re.search(
            r"(\d+(?:\.\d+)?)\s*[Kk][Cc][Aa][Ll]",
            menu
        )

        if kcal_match:
            kcal = float(kcal_match.group(1))
        else:
            kcal = None

        result.append({
            "날짜": meal_date,
            "급식 메뉴": menu,
            "칼로리": kcal
        })

    df = pd.DataFrame(result)

    if df.empty:
        return df, None

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        format="%Y%m%d",
        errors="coerce"
    )

    weekday_map = {
        0: "월요일",
        1: "화요일",
        2: "수요일",
        3: "목요일",
        4: "금요일",
        5: "토요일",
        6: "일요일"
    }

    df["요일"] = df["날짜"].dt.weekday.map(
        weekday_map
    )

    df["칼로리"] = pd.to_numeric(
        df["칼로리"],
        errors="coerce"
    )

    return df.sort_values("날짜"), None


# ==================================================
# 사이드바
# ==================================================
with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">🍚 급식 분석</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "NEIS 학교 급식 데이터를 이용한 칼로리 분석"
    )

    st.markdown(
        """
        <div class="sidebar-school">
            <b>🏫 송탄고등학교</b><br>
            <span style="color:#88796D;">
            경기도교육청 · 중식
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📅 분석 기간")

    today = date.today()

    year = st.number_input(
        "연도",
        min_value=2020,
        max_value=today.year,
        value=today.year,
        step=1
    )

    month = st.selectbox(
        "월",
        list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda x: f"{x}월"
    )

    st.divider()

    st.markdown("### ℹ️ 데이터 정보")

    st.write("**교육청:** 경기")
    st.write("**학교:** 송탄고등학교")
    st.write("**식사:** 중식")
    st.write("**출처:** NEIS 교육정보 개방 포털")

    st.divider()

    st.caption(
        "데이터는 NEIS API에서 가져옵니다."
    )


# ==================================================
# 메인 제목
# ==================================================
st.markdown(
    '<div class="main-title">🍚 급식의 한 달 평균 칼로리는 얼마나 될까?</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitle">'
    f'송탄고등학교의 {year}년 {month}월 중식 데이터를 분석해 '
    f'하루 평균 칼로리와 급식 패턴을 살펴봅니다.'
    f'</div>',
    unsafe_allow_html=True
)


# ==================================================
# 데이터 불러오기
# ==================================================
df, error_message = get_meal_data(year, month)

if error_message:
    st.error(error_message)
    st.stop()

if df.empty:
    st.warning(
        "해당 월에는 급식 데이터가 없습니다."
    )
    st.stop()

calorie_df = df.dropna(
    subset=["칼로리"]
).copy()

if calorie_df.empty:
    st.warning(
        "칼로리 정보가 있는 급식 데이터가 없습니다."
    )
    st.stop()


# ==================================================
# 기본 통계
# ==================================================
avg_kcal = calorie_df["칼로리"].mean()
max_kcal = calorie_df["칼로리"].max()
min_kcal = calorie_df["칼로리"].min()

max_row = calorie_df.loc[
    calorie_df["칼로리"].idxmax()
]

min_row = calorie_df.loc[
    calorie_df["칼로리"].idxmin()
]


# ==================================================
# 데이터 요약
# ==================================================
st.markdown(
    '<div class="section-title">📌 한눈에 보기</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="info-box">
        <b>{year}년 {month}월</b>에는 총
        <b>{len(calorie_df)}일</b>의 칼로리 데이터가 있습니다.
        하루 평균 급식 칼로리는
        <b>{avg_kcal:,.0f} kcal</b>입니다.
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 통계 카드
# ==================================================
card1, card2, card3 = st.columns(3)

with card1:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">🍚 한 달 평균</div>
            <div class="stat-value">{avg_kcal:,.0f} kcal</div>
            <div class="stat-description">
                하루 평균 급식 에너지
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with card2:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">🔥 가장 높은 날</div>
            <div class="stat-value">{max_kcal:,.0f} kcal</div>
            <div class="stat-description">
                {max_row["날짜"].strftime("%Y-%m-%d")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with card3:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">🌱 가장 낮은 날</div>
            <div class="stat-value">{min_kcal:,.0f} kcal</div>
            <div class="stat-description">
                {min_row["날짜"].strftime("%Y-%m-%d")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# 그래프 1
# ==================================================
st.markdown(
    '<div class="section-title">📈 그래프 1. 날짜별 급식 칼로리</div>',
    unsafe_allow_html=True
)

fig1 = px.line(
    calorie_df,
    x="날짜",
    y="칼로리",
    markers=True,
    labels={
        "날짜": "날짜",
        "칼로리": "칼로리 (kcal)"
    }
)

fig1.add_hline(
    y=avg_kcal,
    line_dash="dash",
    annotation_text=f"월 평균 {avg_kcal:,.0f} kcal",
    annotation_position="top left"
)

fig1.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>칼로리: %{y:,.0f} kcal"
        "<extra></extra>"
    )
)

fig1.update_layout(
    height=500,
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    margin=dict(l=30, r=30, t=30, b=30)
)

st.markdown(
    '<div class="chart-card">',
    unsafe_allow_html=True
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="what-box">
        <div class="what-title">💡 이 그래프로 알 수 있는 것</div>
        날짜에 따라 급식 칼로리가 어떻게 변하는지와
        월 평균보다 높은 날과 낮은 날을 확인할 수 있습니다.
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 그래프 2
# ==================================================
st.markdown(
    '<div class="section-title">📊 그래프 2. 요일별 평균 급식 칼로리</div>',
    unsafe_allow_html=True
)

weekday_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일"
]

weekday_avg = (
    calorie_df[
        calorie_df["요일"].isin(weekday_order)
    ]
    .groupby(
        "요일",
        as_index=False
    )["칼로리"]
    .mean()
)

weekday_avg["요일"] = pd.Categorical(
    weekday_avg["요일"],
    categories=weekday_order,
    ordered=True
)

weekday_avg = weekday_avg.sort_values(
    "요일"
)

if not weekday_avg.empty:

    fig2 = px.bar(
        weekday_avg,
        x="요일",
        y="칼로리",
        text="칼로리",
        labels={
            "요일": "요일",
            "칼로리": "평균 칼로리 (kcal)"
        }
    )

    fig2.update_traces(
        texttemplate="%{text:,.0f} kcal",
        textposition="outside",
        hovertemplate=(
            "요일: %{x}"
            "<br>평균 칼로리: %{y:,.1f} kcal"
            "<extra></extra>"
        )
    )

    fig2.update_layout(
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=30, r=30, t=30, b=30)
    )

    st.markdown(
        '<div class="chart-card">',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    highest_weekday = weekday_avg.loc[
        weekday_avg["칼로리"].idxmax()
    ]

    lowest_weekday = weekday_avg.loc[
        weekday_avg["칼로리"].idxmin()
    ]

    st.markdown(
        f"""
        <div class="what-box">
            <div class="what-title">💡 이 그래프로 알 수 있는 것</div>
            {highest_weekday["요일"]}의 평균 칼로리가
            {highest_weekday["칼로리"]:,.1f} kcal로 가장 높고,
            {lowest_weekday["요일"]}이
            {lowest_weekday["칼로리"]:,.1f} kcal로 가장 낮습니다.
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# 가장 높은 날 / 가장 낮은 날
# ==================================================
st.markdown(
    '<div class="section-title">🍽️ 가장 높은 날과 가장 낮은 날</div>',
    unsafe_allow_html=True
)

high_col, low_col = st.columns(2)

with high_col:

    high_menu = max_row["급식 메뉴"].replace(
        "\n",
        "<br>"
    )

    st.markdown(
        f"""
        <div class="meal-card">
            <div class="meal-card-title">
                🔥 가장 높은 칼로리
            </div>

            <div class="meal-date">
                {max_row["날짜"].strftime("%Y년 %m월 %d일")}
            </div>

            <div class="meal-kcal">
                {max_row["칼로리"]:,.0f} kcal
            </div>

            <div class="menu-text">
                {high_menu}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with low_col:

    low_menu = min_row["급식 메뉴"].replace(
        "\n",
        "<br>"
    )

    st.markdown(
        f"""
        <div class="meal-card">
            <div class="meal-card-title">
                🌱 가장 낮은 칼로리
            </div>

            <div class="meal-date">
                {min_row["날짜"].strftime("%Y년 %m월 %d일")}
            </div>

            <div class="meal-kcal">
                {min_row["칼로리"]:,.0f} kcal
            </div>

            <div class="menu-text">
                {low_menu}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# 날짜별 데이터
# ==================================================
st.markdown(
    '<div class="section-title">📋 날짜별 급식 데이터</div>',
    unsafe_allow_html=True
)

display_df = calorie_df.copy()

display_df["날짜"] = (
    display_df["날짜"]
    .dt.strftime("%Y-%m-%d")
)

display_df["칼로리"] = (
    display_df["칼로리"]
    .round(1)
)

display_df = display_df[
    [
        "날짜",
        "요일",
        "칼로리",
        "급식 메뉴"
    ]
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "날짜": st.column_config.TextColumn(
            "날짜"
        ),
        "요일": st.column_config.TextColumn(
            "요일"
        ),
        "칼로리": st.column_config.NumberColumn(
            "칼로리",
            format="%.1f kcal"
        ),
        "급식 메뉴": st.column_config.TextColumn(
            "급식 메뉴",
            width="large"
        )
    }
)

st.caption(
    f"총 {len(calorie_df)}일의 칼로리 데이터를 분석했습니다."
)


# ==================================================
# 참고 자료
# ==================================================
st.divider()

st.markdown(
    '<div class="section-title">📚 참고 자료</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="reference-box">
        학교 급식과 식품·영양에 관한 참고 자료입니다.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "🔗 [CSPI — Calories in School Lunches]"
    "(https://www.cspi.org/resource/calories-school-lunches)"
)

st.markdown(
    "🌽 [Our World in Data — Global Food Data Explorer "
    "(Maize/Corn Production)]"
    "(https://ourworldindata.org/explorers/global-food?Food=Maize+%28corn%29&Metric=Production&Per+capita=false&country=OWID_WRL~USA~CHN~IND~BRA~GBR)"
)


# ==================================================
# 푸터
# ==================================================
st.divider()

st.caption(
    "🍚 NEIS 학교 급식 데이터 기반 · 송탄고등학교 중식 분석"
)
