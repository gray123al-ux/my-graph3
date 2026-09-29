import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 기온 예측기")
st.write("서울의 연평균기온 데이터를 이용해 장기적인 기온 추세를 살펴봅니다.")


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"])

    return df


try:
    df = load_data()
except Exception as e:
    st.error("기온 데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# 연도별 평균기온
# --------------------------------------------------
df["연도"] = df["날짜"].dt.year

# 2025년 이후 제외
df = df[df["연도"] <= 2025].copy()

yearly = (
    df.groupby("연도")
    .agg(
        평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    )
    .reset_index()
)

# 관측일 300일 미만인 해 제외
yearly = yearly[yearly["관측일수"] >= 300].copy()

yearly = yearly.sort_values("연도").reset_index(drop=True)


if len(yearly) < 2:
    st.error("회귀 분석을 수행하기에 충분한 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 전체 기간 회귀
# --------------------------------------------------
yearly["지난연수"] = yearly["연도"] - 1908

x = yearly["지난연수"].to_numpy(dtype=float)
y = yearly["평균기온"].to_numpy(dtype=float)

slope, intercept = np.polyfit(x, y, 1)

correlation = np.corrcoef(x, y)[0, 1]

# 100년에 몇 도 변화하는가
slope_100 = slope * 100


# --------------------------------------------------
# 최근 20년 회귀
# --------------------------------------------------
latest_year = yearly["연도"].max()
recent_start_year = latest_year - 19

recent20 = yearly[
    yearly["연도"] >= recent_start_year
].copy()

if len(recent20) >= 2:
    recent_x = (recent20["연도"] - 1908).to_numpy(dtype=float)
    recent_y = recent20["평균기온"].to_numpy(dtype=float)

    recent_slope, recent_intercept = np.polyfit(
        recent_x,
        recent_y,
        1
    )

    recent_slope_100 = recent_slope * 100

    recent_correlation = np.corrcoef(
        recent_x,
        recent_y
    )[0, 1]
else:
    recent_slope = None
    recent_intercept = None
    recent_slope_100 = None
    recent_correlation = None


# --------------------------------------------------
# 회귀 정보
# --------------------------------------------------
st.subheader("🌡️ 100년에 몇 도 오르는가?")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "전체 기간의 기온 변화",
        f"{slope_100:+.2f} °C / 100년"
    )

with col2:
    if recent_slope_100 is not None:
        st.metric(
            f"최근 20년의 기온 변화 ({recent_start_year}~{latest_year})",
            f"{recent_slope_100:+.2f} °C / 100년"
        )
    else:
        st.metric(
            "최근 20년의 기온 변화",
            "계산 불가"
        )


# --------------------------------------------------
# 전체 기간 vs 최근 20년 비교
# --------------------------------------------------
st.subheader("📊 전체 기간과 최근 20년 비교")

compare_col1, compare_col2 = st.columns(2)

with compare_col1:
    st.markdown("### 전체 기간")
    st.metric(
        "100년당 변화량",
        f"{slope_100:+.2f} °C"
    )
    st.write(
        f"사용 기간: {yearly['연도'].min()}~{yearly['연도'].max()}년"
    )
    st.write(f"사용한 해: {len(yearly)}개")
    st.write(f"상관계수: {correlation:.3f}")

with compare_col2:
    st.markdown("### 최근 20년")
    if recent_slope_100 is not None:
        st.metric(
            "100년당 변화량",
            f"{recent_slope_100:+.2f} °C"
        )
        st.write(
            f"사용 기간: {recent_start_year}~{latest_year}년"
        )
        st.write(f"사용한 해: {len(recent20)}개")
        st.write(f"상관계수: {recent_correlation:.3f}")
    else:
        st.write("최근 20년 데이터가 부족합니다.")


# --------------------------------------------------
# 연도 선택
# --------------------------------------------------
st.subheader("🔮 연도별 예상 기온")

selected_year = st.slider(
    "예상 기온을 보고 싶은 연도를 선택하세요.",
    min_value=1900,
    max_value=2100,
    value=2025,
    step=1
)

selected_x = selected_year - 1908
predicted_temp = intercept + slope * selected_x

st.metric(
    f"{selected_year}년 예상 연평균기온",
    f"{predicted_temp:.2f} °C"
)


# --------------------------------------------------
# 산점도 + 전체 회귀선 + 최근 20년 회귀선
# --------------------------------------------------
st.subheader("📈 연도별 평균기온과 회귀선")

fig = go.Figure()

# 실제 연평균기온
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["평균기온"],
        mode="markers",
        name="실제 연평균기온",
        marker=dict(size=7),
        customdata=yearly[["관측일수"]].to_numpy(),
        hovertemplate=(
            "연도: %{x}년<br>"
            "평균기온: %{y:.2f} °C<br>"
            "관측일수: %{customdata[0]}일"
            "<extra></extra>"
        )
    )
)


# --------------------------------------------------
# 전체 기간 회귀선
# --------------------------------------------------
line_years = np.linspace(
    yearly["연도"].min(),
    yearly["연도"].max(),
    300
)

line_x = line_years - 1908
line_y = intercept + slope * line_x

fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_y,
        mode="lines",
        name="전체 기간 회귀선",
        line=dict(width=3),
        hovertemplate=(
            "연도: %{x:.0f}년<br>"
            "예측: %{y:.2f} °C"
            "<extra></extra>"
        )
    )
)


# --------------------------------------------------
# 최근 20년 회귀선
# --------------------------------------------------
if recent_slope_100 is not None:

    recent_line_years = np.linspace(
        recent_start_year,
        latest_year,
        100
    )

    recent_line_x = recent_line_years - 1908
    recent_line_y = (
        recent_intercept
        + recent_slope * recent_line_x
    )

    fig.add_trace(
        go.Scatter(
            x=recent_line_years,
            y=recent_line_y,
            mode="lines",
            name="최근 20년 회귀선",
            line=dict(
                width=3,
                dash="dash"
            ),
            hovertemplate=(
                "연도: %{x:.0f}년<br>"
                "최근 20년 회귀 예측: %{y:.2f} °C"
                "<extra></extra>"
            )
        )
    )


# --------------------------------------------------
# 선택한 연도의 예측값
# --------------------------------------------------
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name=f"{selected_year}년 예측",
        marker=dict(
            size=14,
            symbol="diamond"
        ),
        hovertemplate=(
            f"{selected_year}년<br>"
            f"예상 기온: {predicted_temp:.2f} °C"
            "<extra></extra>"
        )
    )
)


fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    hovermode="closest",
    height=600,
    legend_title="구분"
)

fig.update_xaxes(
    tickmode="linear",
    dtick=10
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# 회귀식
# --------------------------------------------------
st.subheader("📐 회귀식")

st.write(
    f"**전체 기간:** "
    f"예상 연평균기온 = {intercept:.4f} "
    f"+ ({slope:.4f} × 지난 연수)"
)

if recent_slope_100 is not None:
    st.write(
        f"**최근 20년:** "
        f"예상 연평균기온 = {recent_intercept:.4f} "
        f"+ ({recent_slope:.4f} × 지난 연수)"
    )

st.caption("지난 연수 = 연도 − 1908")


# --------------------------------------------------
# 추세 설명
# --------------------------------------------------
if slope > 0:
    st.info(
        f"전체 기간의 회귀선은 100년에 약 "
        f"{slope_100:.2f} °C 상승하는 추세입니다."
    )
elif slope < 0:
    st.info(
        f"전체 기간의 회귀선은 100년에 약 "
        f"{abs(slope_100):.2f} °C 하락하는 추세입니다."
    )


# --------------------------------------------------
# 데이터 조건
# --------------------------------------------------
with st.expander("사용한 데이터 조건 보기"):
    st.write("• 서울 기온 원본 데이터 사용")
    st.write("• 2025년 이후 데이터 제외")
    st.write("• 연간 관측일 수가 300일 미만인 해 제외")
    st.write("• 각 연도의 평균기온으로 회귀 분석")
    st.write("• 독립변수: 연도 − 1908")
    st.write(
        f"• 전체 회귀 기간: "
        f"{yearly['연도'].min()}~{yearly['연도'].max()}년"
    )
    st.write(f"• 전체 사용 연도: {len(yearly)}개")
    st.write(
        f"• 최근 20년 회귀 기간: "
        f"{recent_start_year}~{latest_year}년"
    )
    st.write(f"• 최근 20년 사용 연도: {len(recent20)}개")
