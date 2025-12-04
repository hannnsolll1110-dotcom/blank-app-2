import streamlit as st
import pandas as pd
import os
from datetime import datetime
import altair as alt 
import plotly.express as px 

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 대시보드", 
    page_icon="🏙️", 
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (함수 부분은 동일)
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
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        df = pd.read_csv(file_name, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    def find_gu(address):
        if not isinstance(address, str): return "기타"
        for gu in SEOUL_GU_LIST:
            if gu in address: return gu
        return "기타"

    df['자치구'] = df['업소 주소'].apply(find_gu)
    df['업소 전화번호'] = df['업소 전화번호'].fillna("-")
    
    df['업소명'] = df['업소명'].astype(str)
    mask_hangul = df['업소명'].str.match(r'^[가-힣]')
    df_hangul = df[mask_hangul].sort_values(by='업소명')
    df_others = df[~mask_hangul].sort_values(by='업소명')
    
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
        new_data.to_csv(review_file, mode='a', header=False, index=False, encoding="utf-8-sig")

try:
    df = load_main_data()
    reviews_df = load_reviews()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 (메뉴 및 필터)
# -----------------------------------------------------------------------------
st.sidebar.title("메뉴 선택")

# [핵심] 여기서 페이지를 선택합니다!
menu = st.sidebar.radio(
    "이동할 페이지를 선택하세요 👇",
    ["🔍 가게 찾기 & 시민 제보", "📊 데이터 분석 시각화"]
)

st.sidebar.markdown("---")
st.sidebar.header("🔍 검색 필터")
st.sidebar.caption("필터를 적용하면 분석 결과도 함께 바뀝니다!")

# 공통 필터 (검색 페이지와 분석 페이지 모두에 적용됨 - 아주 좋은 기능!)
selected_gu = st.sidebar.selectbox("지역 선택", ["전체"] + SEOUL_GU_LIST, index=0)
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("업종 선택", cat_list, default=cat_list)
keyword = st.sidebar.text_input("가게명 검색")

# 필터링 로직
filtered_df = df.copy()
if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]
if selected_cat:
    filtered_df = filtered_df[filtered_df['분류코드명'].isin(selected_cat)]
if keyword:
    filtered_df = filtered_df[filtered_df['업소명'].str.contains(keyword)]

# -----------------------------------------------------------------------------
# 4. 페이지 내용 분기 (If문으로 화면 갈아끼우기)
# -----------------------------------------------------------------------------

# =============================================================================
# [PAGE 1] 가게 찾기 & 시민 제보
# =============================================================================
if menu == "🔍 가게 찾기 & 시민 제보":
    st.title("🔎 서울시 착한가격업소 정보 공유소")
    
    # 안내 박스
    with st.container(border=True):
        col_a, col_b = st.columns([0.3, 4])
        with col_a:
            st.markdown("<h1 style='text-align: center;'>📢</h1>", unsafe_allow_html=True) 
        with col_b:
            st.markdown("### 착한가격업소란?")
            st.markdown("""
            물가 상승 시기에도 **저렴한 가격**과 **청결한 서비스**로 사랑받는 우리 동네 업소입니다.
            **'자랑거리'나 '찾아오는 길' 정보가 비어있는 곳**을 찾아 여러분의 제보로 채워주세요!
            """)

    # 현황판
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("선택된 지역 가게 수", f"{len(filtered_df)} 곳")
    with col2:
        missing_count = filtered_df['자랑거리'].isna().sum() + (filtered_df['자랑거리'] == '').sum()
        st.metric("정보 보완 필요 😢", f"{missing_count} 곳", delta="제보 환영", delta_color="inverse")
    with col3:
        if not reviews_df.empty:
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_count = len(reviews_df[reviews_df['날짜'].str.startswith(today_str)])
        else:
            today_count = 0
        st.metric("오늘의 시민 참여", f"{today_count} 건", delta="실시간 집계 중 🔴") 

    st.divider()

    # 리스트 & 상세화면
    left_col, right_col = st.columns([1, 1])

    with left_col:
        display_title = selected_gu if selected_gu != '전체' else '서울시 전체'
        st.subheader(f"📋 {display_title} 착한업소 목록")
        if filtered_df.empty:
            st.warning("조건에 맞는 가게가 없습니다.")
        else:
            display_cols = ['업소명', '분류코드명', '자치구', '업소 전화번호']
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)

    with right_col:
        st.subheader("✍️ 상세 정보 & 제보하기")
        store_list = filtered_df['업소명'].unique()
        if len(store_list) > 0:
            target_store = st.selectbox("가게를 선택하세요:", store_list)
            store_data = filtered_df[filtered_df['업소명'] == target_store].iloc[0]
            
            with st.container(border=True):
                st.markdown(f"### 🏠 {target_store}")
                st.write(f"**업종:** {store_data['분류코드명']}")
                st.write(f"**위치:** {store_data['자치구']}")
                st.write(f"**주소:** {store_data['업소 주소']}")
                st.write(f"**전화:** {store_data['업소 전화번호']}")
                st.markdown("---")
                pride = store_data['자랑거리']
                if pd.isna(pride) or str(pride).strip() == '':
                    st.warning("📢 **등록된 자랑거리가 없습니다!**")
                    st.info("이 가게의 매력을 가장 먼저 알려주세요.")
                else:
                    st.success(f"**✨ 자랑거리:** {pride}")

            st.markdown(f"#### 💬 시민들의 생생 제보")
            if not reviews_df.empty:
                store_reviews = reviews_df[reviews_df['업소명'] == target_store]
            else:
                store_reviews = pd.DataFrame()

            if not store_reviews.empty:
                for idx, row in store_reviews[::-1].iterrows():
                    st.info(f"**[{row['유형']}] {row['닉네임']}**: {row['내용']} ({row['날짜']})")
            else:
                st.caption("아직 등록된 제보가 없습니다.")

            st.markdown("#### 📝 정보 보완하기")
            with st.form("info_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    nickname = st.text_input("닉네임", "시민1")
                with col_b:
                    review_type = st.selectbox("정보 유형", ["자랑거리", "찾아오는 길", "메뉴 추천", "기타"])
                content = st.text_area("내용 입력", placeholder="예: 돈가스 양이 정말 많아요!")
                if st.form_submit_button("등록하기"):
                    if content.strip():
                        save_review(target_store, nickname, review_type, content)
                        st.balloons()
                        st.success("저장 완료!")
                        st.rerun()
                    else:
                        st.error("내용을 입력해주세요.")
        else:
            st.info("가게 목록이 없습니다.")

# =============================================================================
# [PAGE 2] 데이터 분석 시각화 (여기가 클릭하면 나오는 새 화면!)
# =============================================================================
elif menu == "📊 데이터 분석 시각화":
    st.title("📊 데이터로 보는 서울시 착한업소 트렌드")
    
    # 분석 화면 상단 설명
    st.markdown("""
    > **데이터 인사이트** > 왼쪽 사이드바의 **'검색 필터'**를 변경하면 차트의 데이터도 함께 변경됩니다.  
    > 예를 들어, '강남구'를 선택하면 강남구의 데이터 분석 결과만 볼 수 있습니다.
    """)
    
    st.divider()

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["🏆 자치구별 순위", "🍕 업종별 비율", "🔥 지역x업종 히트맵"])

    with tab1:
        st.markdown(f"#### 🏢 {selected_gu if selected_gu != '전체' else '서울시'} 착한업소 분포")
        if selected_gu != "전체":
            st.info(f"현재 **'{selected_gu}'**가 선택되었습니다. 전체 구와 비교하려면 필터를 '전체'로 변경하세요.")
        
        # 전체 데이터로 비교해야 의미가 있으므로 원본 df 사용 (또는 필터된 것 사용 선택)
        # 여기서는 비교를 위해 원본 df에서 필터링된 내용을 강조하거나, 현재 필터링된 데이터만 보여줌
        # --> 현재 필터링된 데이터 기준 시각화
        
        gu_counts = filtered_df['자치구'].value_counts().reset_index()
        gu_counts.columns = ['자치구', '업소수']
        
        if gu_counts.empty:
            st.warning("데이터가 없습니다.")
        else:
            bar_chart = alt.Chart(gu_counts).mark_bar().encode(
                x=alt.X('업소수:Q', title='업소 수'),
                y=alt.Y('자치구:N', sort='-x', title='자치구'),
                color=alt.Color('업소수:Q', scale=alt.Scale(scheme='blues')),
                tooltip=['자치구', '업소수']
            ).properties(height=500)
            st.altair_chart(bar_chart, use_container_width=True)

    with tab2:
        st.markdown("#### 🍴 업종별 점유율")
        cat_counts = filtered_df['분류코드명'].value_counts().reset_index()
        cat_counts.columns = ['업종', '업소수']
        
        if cat_counts.empty:
            st.warning("데이터가 없습니다.")
        else:
            fig = px.pie(cat_counts, values='업소수', names='업종', hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("#### 🗺️ 업종 밀집도 히트맵")
        # 히트맵은 데이터가 좀 많아야 예쁘므로, 만약 필터링이 너무 많이 됐다면 전체를 보여주는게 나을 수도 있음
        # 여기선 필터링된 기준으로 보여줌
        
        if filtered_df.empty:
             st.warning("데이터가 없습니다.")
        else:
            heatmap_data = filtered_df.groupby(['자치구', '분류코드명']).size().reset_index(name='개수')
            
            heatmap = alt.Chart(heatmap_data).mark_rect().encode(
                x=alt.X('자치구:N'),
                y=alt.Y('분류코드명:N'),
                color=alt.Color('개수:Q', scale=alt.Scale(scheme='orangered')),
                tooltip=['자치구', '분류코드명', '개수']
            ).properties(height=500)
            st.altair_chart(heatmap, use_container_width=True)
