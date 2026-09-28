
import re
import calendar
from datetime import date

import pandas as pd
import requests
import plotly.express as px
import streamlit as st


# =========================
# 기본 설정
# =========================

st.set_page_config(
    page_title="급식 한 달 평균 칼로리",
    page_icon="🍚",
    layout="wide"
)

st.title("🍚 급식의 한 달 평균 칼로리는 얼마나 될까?")
st.write("NEIS 급식 API를 이용해 선택한 달의 학교 급식 칼로리를 분석합니다.")


# =========================
# 학교 정보
# =========================

ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530480"

API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# =========================
# 날짜 선택
# =========================

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
        range(1, 13),
        index=today.month - 1
    )


# =========================
# NEIS API 데이터 가져오기
# =========================

@st.cache_data(ttl=3600)
def get_meal_data(year, month):

    last_day = calendar.monthrange(year, month)[1]

    start_date = f"{year}{month:02d}01"
    end_date = f"{year}{month:02d}{last_day:02d}"

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MLSV_FROM_YMD": start_date,
        "MLSV_TO_YMD": end_date
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:
        st.error(
            f"NEIS API를 불러오는 중 오류가 발생했습니다: {e}"
        )
        return pd.DataFrame()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
    except (KeyError, IndexError):
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    result = []

    for row in rows:

        meal_date = row.get("MLSV_YMD", "")
        menu = row.get("DDISH_NM", "")

        clean_menu = re.sub(
            r"<br\s*/?>",
            "\n",
            menu
        )

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
            "급식 메뉴": clean_menu,
            "칼로리": kcal
        })

    df = pd.DataFrame(result)

    if df.empty:
        return df

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

    df["요일"] = df["날짜"].dt.dayofweek.map(
        weekday_map
    )

    df["칼로리"] = pd.to_numeric(
        df["칼로리"],
        errors="coerce"
    )

    return df.sort_values(
        "날짜"
    ).reset_index(drop=True)


# =========================
# 데이터 불러오기
# =========================

df = get_meal_data(year, month)


# =========================
# 데이터가 없는 경우
# =========================

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
            "해당 월에는 칼로리 정보가 있는 "
            "급식 데이터가 없습니다."
        )

    else:

        # =========================
        # 통계 계산
        # =========================

        avg_kcal = calorie_df["칼로리"].mean()
        max_kcal = calorie_df["칼로리"].max()
        min_kcal = calorie_df["칼로리"].min()

        max_row = calorie_df.loc[
            calorie_df["칼로리"].idxmax()
        ]

        min_row = calorie_df.loc[
            calorie_df["칼로리"].idxmin()
        ]


        # =========================
        # 주요 지표
        # =========================

        st.subheader(
            f"📊 {year}년 {month}월 급식 칼로리"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "월평균 칼로리",
                f"{avg_kcal:,.1f} kcal"
            )

        with c2:
            st.metric(
                "가장 높은 칼로리",
                f"{max_kcal:,.0f} kcal"
            )

        with c3:
            st.metric(
                "가장 낮은 칼로리",
                f"{min_kcal:,.0f} kcal"
            )


        # =========================
        # 한 문장 요약
        # =========================

        st.info(
            f"이 달의 학교 급식은 하루 평균 약 "
            f"{avg_kcal:,.1f}kcal입니다."
        )


        # =========================
        # 그래프 1
        # =========================

        st.subheader("📈 그래프 1. 날짜별 급식 칼로리")

        fig = px.line(
            calorie_df,
            x="날짜",
            y="칼로리",
            markers=True,
            labels={
                "날짜": "날짜",
                "칼로리": "칼로리 (kcal)"
            },
            title=f"{year}년 {month}월 날짜별 급식 칼로리"
        )

        fig.add_hline(
            y=avg_kcal,
            line_dash="dash",
            annotation_text=(
                f"월평균 {avg_kcal:,.1f} kcal"
            ),
            annotation_position="top left"
        )

        fig.update_traces(
            hovertemplate=
            "날짜: %{x|%Y-%m-%d}<br>"
            "칼로리: %{y:,.0f} kcal"
            "<extra></extra>"
        )

        fig.update_layout(
            hovermode="x unified",
            xaxis_title="날짜",
            yaxis_title="칼로리 (kcal)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.markdown(
            "### 💡 이 그래프로 알 수 있는 것"
        )

        st.write(
            f"{year}년 {month}월의 급식 칼로리가 "
            f"날짜별로 어떻게 변하는지 확인할 수 있습니다. "
            f"점선은 한 달 평균인 "
            f"{avg_kcal:,.1f}kcal입니다."
        )


        # =========================
        # 그래프 2
        # =========================

        st.subheader("📊 그래프 2. 요일별 평균 급식 칼로리")

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

        fig2 = px.bar(
            weekday_avg,
            x="요일",
            y="칼로리",
            text="칼로리",
            labels={
                "요일": "요일",
                "칼로리": "평균 칼로리 (kcal)"
            },
            title=(
                f"{year}년 {month}월 "
                "요일별 평균 급식 칼로리"
            )
        )

        fig2.update_traces(
            texttemplate="%{text:,.0f} kcal",
            textposition="outside",
            hovertemplate=
            "요일: %{x}<br>"
            "평균 칼로리: %{y:,.1f} kcal"
            "<extra></extra>"
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


        # =========================
        # 최고 / 최저 칼로리
        # =========================

        st.subheader(
            "🔎 칼로리가 가장 높은 날과 낮은 날"
        )

        high_col, low_col = st.columns(2)

        with high_col:

            st.markdown(
                "#### 🔥 가장 높은 칼로리"
            )

            st.write(
                f"**{max_row['날짜'].strftime('%Y년 %m월 %d일')} "
                f"({max_row['요일']})**"
            )

            st.metric(
                "칼로리",
                f"{max_row['칼로리']:,.0f} kcal"
            )

            with st.expander("급식 메뉴 보기"):
                st.write(
                    max_row["급식 메뉴"]
                )


        with low_col:

            st.markdown(
                "#### 🌱 가장 낮은 칼로리"
            )

            st.write(
                f"**{min_row['날짜'].strftime('%Y년 %m월 %d일')} "
                f"({min_row['요일']})**"
            )

            st.metric(
                "칼로리",
                f"{min_row['칼로리']:,.0f} kcal"
            )

            with st.expander("급식 메뉴 보기"):
                st.write(
                    min_row["급식 메뉴"]
                )


        # =========================
        # 날짜별 표
        # =========================

        st.subheader(
            "🍽️ 날짜별 급식 정보"
        )

        table_df = df.copy()

        table_df["날짜"] = table_df[
            "날짜"
        ].dt.strftime("%Y-%m-%d")

        table_df["칼로리"] = table_df[
            "칼로리"
        ].apply(
            lambda x:
            f"{x:,.0f} kcal"
            if pd.notna(x)
            else "-"
        )

        table_df = table_df[
            [
                "날짜",
                "요일",
                "칼로리",
                "급식 메뉴"
            ]
        ]

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )


        # =========================
        # 데이터 개수
        # =========================

        st.caption(
            f"전체 급식일: {len(df)}일 · "
            f"칼로리 확인 가능: "
            f"{len(calorie_df)}일"
        )


이제 앱에는 **그래프 1(날짜별 변화)**과 **그래프 2(요일별 평균 비교)**가 모두 들어갑니다.
