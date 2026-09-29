import re

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
# 다크 테마 디자인
# ==================================================
st.markdown("""
<style>
    /* 전체 앱 */
    .stApp {
        background-color: #0E1117;
        color: #E8E8E8;
    }

    /* 메인 컨테이너 */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* 기본 텍스트 */
    p, span, label {
        color: #D8D8D8;
    }

    /* 메인 제목 */
    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.05rem;
        color: #A9A9B2;
        margin-bottom: 2rem;
    }

    /* 섹션 제목 */
    .section-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #FFFFFF;
        margin-top: 2rem;
        margin-bottom: 0.8rem;
    }

    /* 안내 박스 */
    .info-box {
        background-color: #1B1F27;
        border-left: 5px solid #FFB84D;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        color: #DCDCDC;
        margin: 1rem 0 1.5rem 0;
    }

    .info-box b {
        color: #FFD27A;
    }

    /* 통계 카드 */
    .stat-card {
        background: linear-gradient(
            145deg,
            #191D25,
            #14171D
        );
        border-radius: 18px;
        padding: 1.3rem;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.35);
        border: 1px solid #292E38;
        min-height: 145px;
    }

    .stat-label {
        font-size: 0.95rem;
        color: #9EA4AF;
        margin-bottom: 0.4rem;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
    }

    .stat-description {
        font-size: 0.85rem;
        color: #858B96;
        margin-top: 0.4rem;
    }

    /* 그래프 카드 */
    .chart-card {
        background-color: #15181F;
        border-radius: 18px;
        padding: 0.8rem 1rem 0.3rem 1rem;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.25);
        border: 1px solid #292E38;
        margin-bottom: 1rem;
    }

    /* 그래프 설명 */
    .what-box {
        background-color: #181C23;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.8rem 0 2rem 0;
        color: #C9CDD4;
        border: 1px solid #292E38;
    }

    .what-title {
        font-weight: 750;
        color: #FFCA70;
        margin-bottom: 0.3rem;
    }

    /* 급식 카드 */
    .meal-card {
        background: linear-gradient(
            145deg,
            #191D25,
            #14171D
        );
        border-radius: 18px;
        padding: 1.3rem;
        border: 1px solid #292E38;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.25);
        min-height: 260px;
    }

    .meal-card-title {
        font-size: 1.2rem;
        font-weight: 750;
        color: #FFFFFF;
    }

    .meal-date {
        font-size: 1rem;
        color: #9EA4AF;
        margin-top: 0.5rem;
    }

    .meal-kcal {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFB84D;
        margin: 0.5rem 0;
    }

    .menu-text {
        color: #C7CBD2;
        line-height: 1.7;
        white-space: pre-line;
    }

    /* 참고 자료 */
    .reference-box {
        background-color: #15181F;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #292E38;
        color: #BFC4CC;
        margin-bottom: 1rem;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #11141A;
        border-right: 1px solid #292E38;
    }

    .sidebar-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #FFFFFF;
    }

    .sidebar-school {
        background-color: #191D25;
        padding: 1rem;
        border-radius: 14px;
        margin: 1rem 0;
        border: 1px solid #292E38;
    }

    .sidebar-school b {
        color: #FFFFFF;
    }

    .sidebar-school span {
        color: #949AA5 !important;
    }

    /* 입력 위젯 */
    div[data-baseweb="select"] > div {
        background-color: #191D25;
        border-color: #343A46;
        color: #FFFFFF;
    }

    div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }

    input {
        background-color: #191D25 !important;
        color: #FFFFFF !important;
    }

    /* 데이터프레임 */
    div[data-testid="stDataFrame"] {
        border: 1px solid #292E38;
        border-radius: 12px;
        overflow: hidden;
    }

    /* 링크 */
    a {
        color: #FFBF5F !important;
        font-weight: 600;
    }

    a:hover {
        color: #FFD88A !important;
    }

    /* 경고 */
    div[data-testid="stAlert"] {
        background-color: #1B1F27;
    }

    /* 버튼 */
    button {
        border-radius: 10px !important;
    }

    /* 구분선 */
    hr {
        border-color: #292E38 !important;
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
def get_all_meal_data():
    """NEIS API에서 2025-09-01 ~ 2026-09-30 중식 데이터를 한 번에 가져옵니다."""
    try:
        api_key = st.secrets["KEY"]
    except Exception:
        return pd.DataFrame(), (
            'Streamlit Secrets에 KEY가 없습니다. '
            '.streamlit/secrets.toml에 KEY = "발급받은_인증키"를 넣어 주세요.'
        )

    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": "20250901",
        "MLSV_TO_YMD": "20260930",
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return pd.DataFrame(), f"API 연결 오류: {e}"
    except ValueError:
        return pd.DataFrame(), "API에서 올바른 JSON 데이터를 받지 못했습니다."

    if "mealServiceDietInfo" not in data:
        result = data.get("RESULT", {})
        message = result.get(
            "MESSAGE",
            "NEIS API에서 급식 데이터를 찾지 못했습니다."
        )
        return pd.DataFrame(), message

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
    except (KeyError, IndexError, TypeError):
        return pd.DataFrame(), "NEIS API 응답에서 급식 데이터를 찾지 못했습니다."

    result = []

    for row in rows:
        meal_date = row.get("MLSV_YMD", "")
        menu = row.get("DDISH_NM", "")

        # <br/> → 줄바꿈
        menu = re.sub(r"<br\s*/?>", "\n", menu)

        # kcal 숫자 추출
        kcal_match = re.search(
            r"(\d+(?:\.\d+)?)\s*[Kk][Cc][Aa][Ll]",
            menu
        )

        kcal = float(kcal_match.group(1)) if kcal_match else None

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

    df["요일"] = df["날짜"].dt.weekday.map(weekday_map)

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
            <span>경기도교육청 · 중식</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📅 분석 기간")

    year = st.selectbox(
        "연도",
        [2025, 2026],
        index=1
    )

    available_months = list(range(1, 13))
    if year == 2025:
        available_months = list(range(9, 13))
    elif year == 2026:
        available_months = list(range(1, 10))

    month = st.selectbox(
        "월",
        available_months,
        index=len(available_months) - 1,
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
    '<div class="main-title">'
    '🍚 급식의 한 달 평균 칼로리는 얼마나 될까?'
    '</div>',
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
all_df, error_message = get_all_meal_data()

if error_message:
    st.error(error_message)
    st.stop()

if all_df.empty:
    st.warning("급식 데이터가 없습니다.")
    st.stop()

df = all_df[
    (all_df["날짜"].dt.year == year) &
    (all_df["날짜"].dt.month == month)
].copy()

if df.empty:
    st.warning("해당 월에는 급식 데이터가 없습니다.")
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
# 한눈에 보기
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
            <div class="stat-value">
                {avg_kcal:,.0f} kcal
            </div>
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
            <div class="stat-value">
                {max_kcal:,.0f} kcal
            </div>
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
            <div class="stat-value">
                {min_kcal:,.0f} kcal
            </div>
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
    '<div class="section-title">'
    '📈 그래프 1. 날짜별 급식 칼로리'
    '</div>',
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
    plot_bgcolor="#15181F",
    paper_bgcolor="#15181F",
    font=dict(
        color="#D8D8D8"
    ),
    xaxis=dict(
        title="날짜",
        gridcolor="#292E38",
        zerolinecolor="#292E38"
    ),
    yaxis=dict(
        title="칼로리 (kcal)",
        gridcolor="#292E38",
        zerolinecolor="#292E38"
    ),
    hovermode="x unified",
    margin=dict(
        l=30,
        r=30,
        t=30,
        b=30
    )
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
        <div class="what-title">
            💡 이 그래프로 알 수 있는 것
        </div>
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
    '<div class="section-title">'
    '📊 그래프 2. 요일별 평균 급식 칼로리'
    '</div>',
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
        plot_bgcolor="#15181F",
        paper_bgcolor="#15181F",
        font=dict(
            color="#D8D8D8"
        ),
        xaxis=dict(
            title="요일",
            gridcolor="#292E38",
            zerolinecolor="#292E38"
        ),
        yaxis=dict(
            title="평균 칼로리 (kcal)",
            gridcolor="#292E38",
            zerolinecolor="#292E38"
        ),
        margin=dict(
            l=30,
            r=30,
            t=30,
            b=30
        )
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
            <div class="what-title">
                💡 이 그래프로 알 수 있는 것
            </div>
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
    '<div class="section-title">'
    '🍽️ 가장 높은 날과 가장 낮은 날'
    '</div>',
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
    '<div class="section-title">'
    '📋 날짜별 급식 데이터'
    '</div>',
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
