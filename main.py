import re
import calendar
from datetime import date

import pandas as pd
import requests
import plotly.express as px
import streamlit as st


# ==================================================
# 기본 설정
# ==================================================
st.set_page_config(
    page_title="급식 한 달 평균 칼로리",
    page_icon="🍚",
    layout="wide"
)

st.title("🍚 급식의 한 달 평균 칼로리는 얼마나 될까?")

st.write(
    "송탄고등학교의 NEIS 급식 데이터를 이용해 "
    "한 달 동안 급식의 평균 칼로리를 알아봅니다."
)


# ==================================================
# 학교 정보
# ==================================================
ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# ==================================================
# 연도 / 월 선택
# ==================================================
today = date.today()

col1, col2 = st.columns(2)

with col1:
    year = st.number_input(
        "연도",
        min_value=2020,
        max_value=today.year,
        value=today.year,
        step=1
    )

with col2:
    month = st.selectbox(
        "월",
        list(range(1, 13)),
        index=today.month - 1
    )


# ==================================================
# NEIS 급식 데이터 가져오기
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
        st.error(
            f"NEIS API에 접속할 수 없습니다.\n\n{e}"
        )
        return pd.DataFrame()

    except ValueError:
        st.error(
            "NEIS API에서 올바른 JSON 데이터를 받지 못했습니다."
        )
        return pd.DataFrame()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    try:
        rows = data["mealServiceDietInfo"][1]["row"]

    except (KeyError, IndexError):
        return pd.DataFrame()

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

        # kcal 숫자 추출
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
        return df

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        format="%Y%m%d",
        errors="coerce"
    )

    # 요일
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

    # 칼로리 숫자 변환
    df["칼로리"] = pd.to_numeric(
        df["칼로리"],
        errors="coerce"
    )

    return df.sort_values("날짜")


# ==================================================
# 데이터 불러오기
# ==================================================
df = get_meal_data(year, month)


# ==================================================
# 데이터가 없는 경우
# ==================================================
if df.empty:

    st.warning(
        "해당 월에는 급식 데이터가 없습니다."
    )

else:

    calorie_df = df.dropna(
        subset=["칼로리"]
    ).copy()

    if calorie_df.empty:

        st.warning(
            "칼로리 정보가 있는 급식 데이터가 없습니다."
        )

    else:

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
        st.subheader("📌 한눈에 보기")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "한 달 평균",
                f"{avg_kcal:,.0f} kcal"
            )

        with col2:
            st.metric(
                "가장 높은 날",
                f"{max_kcal:,.0f} kcal"
            )

        with col3:
            st.metric(
                "가장 낮은 날",
                f"{min_kcal:,.0f} kcal"
            )

        st.info(
            f"{year}년 {month}월 학교 급식의 하루 평균 칼로리는 "
            f"약 {avg_kcal:,.0f} kcal입니다."
        )


        # ==================================================
        # 그래프 1
        # ==================================================
        st.subheader(
            "📈 그래프 1. 날짜별 급식 칼로리"
        )

        fig1 = px.line(
            calorie_df,
            x="날짜",
            y="칼로리",
            markers=True,
            title=f"{year}년 {month}월 날짜별 급식 칼로리",
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
            xaxis_title="날짜",
            yaxis_title="칼로리 (kcal)",
            height=500,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        st.markdown(
            "### 💡 이 그래프로 알 수 있는 것"
        )

        st.write(
            "날짜에 따라 급식 칼로리가 어떻게 변하는지와 "
            "월 평균보다 높은 날과 낮은 날을 확인할 수 있습니다."
        )


        # ==================================================
        # 그래프 2
        # ==================================================
        st.subheader(
            "📊 그래프 2. 요일별 평균 급식 칼로리"
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
                calorie_df["요일"].isin(
                    weekday_order
                )
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

        if weekday_avg.empty:

            st.warning(
                "요일별로 표시할 데이터가 없습니다."
            )

        else:

            fig2 = px.bar(
                weekday_avg,
                x="요일",
                y="칼로리",
                text="칼로리",
                title=f"{year}년 {month}월 요일별 평균 급식 칼로리",
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
                xaxis_title="요일",
                yaxis_title="평균 칼로리 (kcal)",
                height=500
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

            st.markdown(
                "### 💡 이 그래프로 알 수 있는 것"
            )

            highest_weekday = weekday_avg.loc[
                weekday_avg["칼로리"].idxmax()
            ]

            lowest_weekday = weekday_avg.loc[
                weekday_avg["칼로리"].idxmin()
            ]

            st.write(
                f"{highest_weekday['요일']}의 평균 칼로리가 "
                f"{highest_weekday['칼로리']:,.1f}kcal로 가장 높고, "
                f"{lowest_weekday['요일']}이 "
                f"{lowest_weekday['칼로리']:,.1f}kcal로 가장 낮습니다."
            )


        # ==================================================
        # 가장 높은 날 / 가장 낮은 날
        # ==================================================
        st.subheader(
            "🍽️ 가장 높은 날과 가장 낮은 날"
        )

        high_col, low_col = st.columns(2)

        with high_col:

            st.markdown(
                "### 🔥 가장 높은 칼로리"
            )

            st.write(
                f"**{max_row['날짜'].strftime('%Y-%m-%d')}**"
            )

            st.metric(
                "칼로리",
                f"{max_row['칼로리']:,.0f} kcal"
            )

            st.write(
                max_row["급식 메뉴"]
            )

        with low_col:

            st.markdown(
                "### 🌱 가장 낮은 칼로리"
            )

            st.write(
                f"**{min_row['날짜'].strftime('%Y-%m-%d')}**"
            )

            st.metric(
                "칼로리",
                f"{min_row['칼로리']:,.0f} kcal"
            )

            st.write(
                min_row["급식 메뉴"]
            )


        # ==================================================
        # 날짜별 데이터
        # ==================================================
        st.subheader(
            "📋 날짜별 급식 데이터"
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

        st.dataframe(
            display_df[
                [
                    "날짜",
                    "요일",
                    "칼로리",
                    "급식 메뉴"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"총 {len(calorie_df)}일의 칼로리 데이터를 분석했습니다."
        )


# ==================================================
# 참고 자료
# ==================================================
st.divider()

st.subheader("📚 참고 자료")

st.write(
    "학교 급식과 식품·영양에 관한 참고 자료입니다."
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
