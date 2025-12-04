import streamlit as st
import pandas as pd
import os
from datetime import datetime
import altair as alt

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한가격업소 정보 및 시민참여형 대시보드",
    page_icon="🏙️",
    layout="wide"
)

st.title("서울시 착한가격업소 정보 및 시민참여형 대시보드")

# [안내 박스]
with st.container(border=True):
    col_a, col_b = st.columns([0.3, 4])
    with col_a:
        st.markdown("<h1 style='text-align: center;'>📢</h1>", unsafe_allow_html=True)
    with col_b:
        st.markdown("### 착한가격업소란?")
        st.markdown("""
        물가 상승 시기에도 **저렴한 가격**과 **청결한 서비스**로 사랑받는 우리 동네 업소입니다.
        """)
        st.markdown("""
        가격, 품질, 위생 등 **행정안전부 기준에 의거한 평가를 통해 구청장이 지정한 업소이니 안심하세요:)**
        """)
        st.markdown("""
        👉 **'자랑거리'나 '찾아오는 길' 정보가 비어있는 곳**을 찾아 여러분의 제보로 채워주세요!
        """)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
SEOUL_GU_LIST = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

@st.cache_data
def load_main_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        df = pd.read_csv(file_name, encoding="cp949")
    except:
        df = pd.read_csv(file_name, encoding="utf-8")

    df.columns = df.columns.str.strip()

    # 자치구 추출
    def find_gu(address):
        if not isinstance(address, str):
            return "기타"
        for gu in SEOUL_GU_LIST:
            if gu in address:
                return gu
        return "기타"

    df["자치구"] = df["업소 주소"].apply(find_gu)

    # 전화번호 결측치 처리
    df["업소 전화번호"] = df["업소 전화번호"].fillna("-")

    # 한글 이름 우선 정렬
    df["업소명"] = df["업소명"].astype(str)
    mask_hangul = df["업소명"].str.match(r"^[가-힣]")
    df_hangul = df[mask_hangul].sort_values(by="업소명")
    df_others = df[~mask_hangul].sort_values(by="업소명")

    return pd.concat([df_hangul, df_others])

def load_reviews():
    review_file = "user_reviews.csv"
    if os.path.exists(review_file):
        return pd.read_csv(review_file)
    else:
        return pd.DataFrame(columns=["업소명", "닉네임", "유형", "내용", "날짜"])

def save_review(store_name, nickname, review_type, content):
    review_file = "user_reviews.csv"
    new_data = pd.DataFrame([{
        "업소명": store_name,
        "닉네임": nickname,
        "유형": review_type,
        "내용": content,
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M")
    }])

    if not os.path.exists(review_file):
        new_data.to_csv(review_file, index=False, encoding="utf-8-sig")
    else:
        new_data.to_csv(review_file, mode="a", header=False, index=False, encoding="utf-8-sig")

# 데이터 로드
try:
    df = load_main_data()
    reviews_df = load_reviews()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다. '서울시 착한가격업소 현황.csv' 파일을 현재 디렉토리에 두세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 상단 탭 (가로 메뉴)
# -----------------------------------------------------------------------------
tab_search, tab_analytics = st.tabs([
    "🔍 가게 찾기 & 시민 제보",
    "📊 자치구 분석"
])

# -----------------------------------------------------------------------------
# 4-A. 🔍 가게 찾기 & 시민 제보 탭
# -----------------------------------------------------------------------------
with tab_search:
    st.sidebar.header("🔍 지역 및 업종 선택")

    st.sidebar.markdown("### 1️⃣ 지역 선택 (필수)")
    selected_gu = st.sidebar.selectbox("어느 구를 볼까요?", ["전체"] + SEOUL_GU_LIST, index=0)

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 2️⃣ 업종 선택")
    cat_list = sorted(df["분류코드명"].unique().tolist())
    selected_cat = st.sidebar.multiselect("원하는 업종을 고르세요", cat_list, default=cat_list)

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 3️⃣ 가게 이름 찾기")
    keyword = st.sidebar.text_input("가게명 입력 (선택)")

    # 필터링 적용
    filtered_df = df.copy()

    if selected_gu != "전체":
        filtered_df = filtered_df[filtered_df["자치구"] == selected_gu]

    if selected_cat:
        filtered_df = filtered_df[filtered_df["분류코드명"].isin(selected_cat)]

    if keyword:
        filtered_df = filtered_df[filtered_df["업소명"].str.contains(keyword)]

    # 현황판
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("선택된 지역 가게 수", f"{len(filtered_df)} 곳")

    with col2:
        missing_count = filtered_df["자랑거리"].isna().sum() + (filtered_df["자랑거리"] == "").sum()
        st.metric("정보 보완 필요 😢", f"{missing_count} 곳", delta="제보 환영", delta_color="inverse")

    with col3:
        if not reviews_df.empty:
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_count = len(reviews_df[reviews_df["날짜"].str.startswith(today_str)])
        else:
            today_count = 0
        st.metric("오늘의 시민 참여", f"{today_count} 건", delta="실시간 집계 중 🔴")

    st.divider()

    # 좌우 레이아웃
    left_col, right_col = st.columns([1, 1])

    # 왼쪽: 리스트
    with left_col:
        display_title = selected_gu if selected_gu != "전체" else "서울시 전체"
        st.subheader(f"📋 {display_title} 착한업소 목록")

        if filtered_df.empty:
            st.warning("조건에 맞는 가게가 없습니다.")
        else:
            display_cols = ["업소명", "분류코드명", "자치구", "업소 전화번호"]
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)

    # 오른쪽: 상세 + 제보
    with right_col:
        st.subheader("✍️ 상세 정보 & 제보하기")

        store_list = filtered_df["업소명"].unique()

        if len(store_list) > 0:
            target_store = st.selectbox("가게를 선택하세요:", store_list)
            store_data = filtered_df[filtered_df["업소명"] == target_store].iloc[0]

            # 1. 가게 정보 카드
            with st.container(border=True):
                st.markdown(f"### 🏠 {target_store}")
                st.write(f"**업종:** {store_data['분류코드명']}")
                st.write(f"**위치:** {store_data['자치구']}")
                st.write(f"**주소:** {store_data['업소 주소']}")
                st.write(f"**전화:** {store_data['업소 전화번호']}")

                st.markdown("---")

                pride = store_data["자랑거리"]
                if pd.isna(pride) or str(pride).strip() == "":
                    st.warning("📢 **등록된 자랑거리가 없습니다!**")
                    st.info("이 가게의 매력을 가장 먼저 알려주세요.")
                else:
                    st.success(f"**✨ 자랑거리:** {pride}")

            # 2. 시민 제보 현황
            st.markdown("#### 💬 시민들의 생생 제보")

            if not reviews_df.empty:
                store_reviews = reviews_df[reviews_df["업소명"] == target_store]
            else:
                store_reviews = pd.DataFrame()

            if not store_reviews.empty:
                for idx, row in store_reviews[::-1].iterrows():
                    st.info(f"**[{row['유형']}] {row['닉네임']}**: {row['내용']} ({row['날짜']})")
            else:
                st.caption("아직 등록된 제보가 없습니다. 첫 번째 제보자가 되어주세요! 👇")

            # 3. 제보 입력 폼
            st.divider()
            st.markdown("#### 📝 정보 보완하기")

            with st.form("info_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    nickname = st.text_input("닉네임", "시민1")
                with col_b:
                    review_type = st.selectbox("정보 유형", ["자랑거리", "찾아오는 길", "메뉴 추천", "기타"])

                content = st.text_area("내용 입력", placeholder="예: 돈가스 양이 정말 많아요! 주차장은 뒤편에 있습니다.")

                submit_btn = st.form_submit_button("등록하기")

                if submit_btn:
                    if content.strip():
                        save_review(target_store, nickname, review_type, content)
                        st.balloons()
                        st.success(f"저장 완료! '{target_store}'에 정보가 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("내용을 입력해주세요.")
        else:
            st.info("가게 목록이 없습니다.")

# -----------------------------------------------------------------------------
# 4-B. 📊 자치구 분석 탭
# -----------------------------------------------------------------------------
with tab_analytics:
    st.subheader("📊 자치구 분석")

    # -------------------------------------------------------------------------
    # 1️⃣ 자치구별 착한가격업소 수 (Top 13)
    # -------------------------------------------------------------------------
    st.markdown("#### 1️⃣ 자치구별 착한가격업소 수 (Top 13)")

    gu_counts = df.copy()
    gu_counts = gu_counts[gu_counts["자치구"] != "기타"]
    gu_counts = (
        gu_counts.groupby("자치구")
        .size()
        .reset_index(name="업소 수")
        .sort_values("업소 수", ascending=False)
    )

    top13 = gu_counts.head(13)

    st.markdown(
        "※ 서울시 25개 자치구 중, **착한가격업소 수 기준 상위 13개 자치구**만 시각화했습니다."
    )

    if not top13.empty:
        top_gu = top13.iloc[0]
        st.metric(
            "착한가격업소가 가장 많은 자치구",
            f"{top_gu['자치구']}",
            f"{int(top_gu['업소 수'])} 곳"
        )

    base_chart = alt.Chart(top13).encode(
        y=alt.Y("자치구:N", sort="-x", title="자치구"),
        x=alt.X("업소 수:Q", title="착한가격업소 수"),
        tooltip=["자치구", "업소 수"]
    )

    bars = base_chart.mark_bar(cornerRadius=4).encode(
        color=alt.Color(
            "업소 수:Q",
            scale=alt.Scale(scheme="reds"),
            legend=None
        )
    )

    labels = base_chart.mark_text(
        align="left",
        baseline="middle",
        dx=5,
        fontSize=12
    ).encode(
        text="업소 수:Q"
    )

    chart = (bars + labels).properties(
        height=450,
        width="container",
        title="자치구별 착한가격업소 수 (Top 13)"
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=13
    ).configure_title(
        fontSize=16,
        fontWeight="bold",
        anchor="start"
    )

    st.altair_chart(chart, use_container_width=True)

    with st.expander("🔍 자치구별 업소 수 (Top 13) 표로 보기"):
        st.dataframe(top13, hide_index=True, use_container_width=True)

    st.divider()

       # -------------------------------------------------------------------------
    # 2️⃣ 업종별 착한가격업소 비중 분석 (파이차트)
    # -------------------------------------------------------------------------
    st.markdown("#### 2️⃣ 업종별 착한가격업소 비중 분석 (파이차트)")

    # 업종별 집계
    cat_counts = (
        df.groupby("분류코드명")
        .size()
        .reset_index(name="업소 수")
        .sort_values("업소 수", ascending=False)
    )

    # ▶ 업종이 너무 많으면 상위 5개 + '기타'로 묶기
    max_cats = 6  # 상위 5개 + 기타
    if len(cat_counts) > max_cats:
        top = cat_counts.head(max_cats - 1).copy()
        others = cat_counts.iloc[max_cats - 1:]["업소 수"].sum()
        other_row = pd.DataFrame([{"분류코드명": "기타", "업소 수": others}])
        cat_plot = pd.concat([top, other_row], ignore_index=True)
    else:
        cat_plot = cat_counts.copy()

    # 비중 계산
    cat_plot["비중(%)"] = (cat_plot["업소 수"] / cat_plot["업소 수"].sum() * 100).round(1)

    # ▶ 범례에 바로 보이게: "업종명 (XX.X%)"
    cat_plot["범례라벨"] = cat_plot["분류코드명"] + " (" + cat_plot["비중(%)"].astype(str) + "%)"

    st.markdown(
        "※ 각 색은 **업종(분류코드명)**을 의미하며, 괄호 안 숫자는 전체에서 차지하는 비중입니다. "
        "업종 종류가 많아 상위 5개 업종과 **'기타'**로 묶어서 보여줍니다."
    )

    pie_chart = alt.Chart(cat_plot)

    # 파이 본체 (텍스트 라벨은 빼고, 범례 + 툴팁으로만 표시)
    pie = pie_chart.mark_arc(outerRadius=150, innerRadius=40).encode(
        theta=alt.Theta("업소 수:Q", stack=True),
        color=alt.Color(
            "범례라벨:N",
            legend=alt.Legend(title="업종 (비중 기준)")
        ),
        tooltip=["분류코드명", "업소 수", "비중(%)"]
    )

    pie_figure = pie.properties(
        width="container",
        height=400,
        title="업종별 착한가격업소 비중 (상위 5개 + 기타)"
    ).configure_title(
        fontSize=16,
        fontWeight="bold",
        anchor="start"
    )

    st.altair_chart(pie_figure, use_container_width=True)

    with st.expander("📋 업종별 비중 데이터 보기 (상위 5개 + 기타)"):
        st.dataframe(cat_plot, hide_index=True, use_container_width=True)

    # -------------------------------------------------------------------------
    # 3️⃣ 자치구 × 업종 히트맵 (상위 5개 자치구)
    # -------------------------------------------------------------------------
    st.markdown("#### 3️⃣ 자치구 × 업종 히트맵 (Top 5 자치구)")

    # 상위 5개 자치구 선정
    top5 = gu_counts.head(5)
    top5_list = top5["자치구"].tolist()

    st.markdown(
        "※ 서울시 25개 자치구 중, **착한가격업소 수 기준 상위 5개 자치구**만 히트맵으로 보여줍니다."
    )

    heatmap_data = (
        df.groupby(["자치구", "분류코드명"])
        .size()
        .reset_index(name="업소 수")
    )
    heatmap_top5 = heatmap_data[heatmap_data["자치구"].isin(top5_list)]

    heatmap_chart = (
        alt.Chart(heatmap_top5)
        .mark_rect()
        .encode(
            x=alt.X(
                "분류코드명:N",
                title="업종",
                sort=cat_counts["분류코드명"].tolist(),
                axis=alt.Axis(labelAngle=0)  # 글씨 똑바로
            ),
            y=alt.Y(
                "자치구:N",
                title="자치구",
                sort=top5_list
            ),
            color=alt.Color(
                "업소 수:Q",
                scale=alt.Scale(scheme="reds"),
                title="업소 수"
            ),
            tooltip=["자치구", "분류코드명", "업소 수"]
        )
        .properties(
            width="container",
            height=400,
            title="자치구 × 업종별 착한가격업소 분포 (Top 5 자치구)"
        )
        .configure_axis(
            labelFontSize=11,
            titleFontSize=12
        )
        .configure_title(
            fontSize=16,
            fontWeight="bold",
            anchor="start"
        )
    )

    st.altair_chart(heatmap_chart, use_container_width=True)

    with st.expander("📋 히트맵 데이터 (Top 5 자치구) 보기"):
        st.dataframe(heatmap_top5, hide_index=True, use_container_width=True)
