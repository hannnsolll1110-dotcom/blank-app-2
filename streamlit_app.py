import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 찾기", 
    page_icon="🏙️", 
    layout="wide"
)

st.title("🔎 서울시 착한가격업소 정보 공유소")

with st.container(border=True):
    col_a, col_b = st.columns([0.3, 4])
    with col_a:
        st.markdown("<h1 style='text-align: center;'>📢</h1>", unsafe_allow_html=True) 
    with col_b:
        st.markdown("### 착한가격업소란?")
        st.markdown("""
        물가 상승 시기에도 **저렴한 가격**과 **청결한 서비스**로 사랑받는 우리 동네 업소입니다.
        가격, 품질, 위생 등 행정안전부 기준에 의거한 평가를 통해 구청장이 지정한 업소입니다.
        **'자랑거리'나 '찾아오는 길' 등 정보가 비어있는 곳**을 찾아 여러분의 제보로 채워주세요!
        """)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 '25개 구' 강제 필터링
# -----------------------------------------------------------------------------
# 서울시 25개 자치구 리스트 (고정값)
SEOUL_GU_LIST = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", 
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", 
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

@st.cache_data
def load_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        df = pd.read_csv(file_name, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    # [핵심 로직] 주소 문자열 안에 '강남구', '종로구' 등이 포함되어 있는지 확인해서 할당
    def find_gu(address):
        if not isinstance(address, str):
            return "기타"
        
        # 25개 구 리스트를 순회하며 주소에 그 이름이 있는지 확인
        for gu in SEOUL_GU_LIST:
            if gu in address:
                return gu
        return "기타" # 25개 구 이름이 발견되지 않으면 기타 처리

    # '자치구' 컬럼을 새로 만듭니다 (기존 데이터 무시하고 새로 계산)
    df['자치구'] = df['업소 주소'].apply(find_gu)
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 25개 구 전용 선택창
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 지역 및 업종 선택")

st.sidebar.markdown("### 1️⃣ 지역 선택 (필수)")

# [수정됨] 데이터에서 뽑는 게 아니라, 우리가 정한 25개 리스트만 보여줌
selected_gu = st.sidebar.selectbox(
    "어느 구를 볼까요?", 
    ["전체"] + SEOUL_GU_LIST, # 여기에 25개 구 리스트를 바로 넣음
    index=0 
)

st.sidebar.markdown("---") 

st.sidebar.markdown("### 2️⃣ 업종 선택")
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("원하는 업종을 고르세요", cat_list, default=cat_list)

st.sidebar.markdown("---")

st.sidebar.markdown("### 3️⃣ 가게 이름 찾기")
keyword = st.sidebar.text_input("가게명 입력 (선택)")

# --- 필터링 로직 ---
filtered_df = df.copy()

# 1. 지역 필터링
if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]

# 2. 업종 필터링
if selected_cat:
    filtered_df = filtered_df[filtered_df['분류코드명'].isin(selected_cat)]

# 3. 키워드 필터링
if keyword:
    filtered_df = filtered_df[filtered_df['업소명'].str.contains(keyword)]

# -----------------------------------------------------------------------------
# 4. 메인 화면
# -----------------------------------------------------------------------------

if selected_gu == "전체":
    st.info("💡 **Tip:** 왼쪽 사이드바에서 **원하는 '구'**를 선택하면 동네별로 깔끔하게 모아볼 수 있어요!")

# 현황판
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("선택된 지역 가게 수", f"{len(filtered_df)} 곳")
with col2:
    missing_count = filtered_df['자랑거리'].isna().sum() + (filtered_df['자랑거리'] == '').sum()
    st.metric("정보 보완 필요 😢", f"{missing_count} 곳", delta="제보 환영", delta_color="inverse")
with col3:
    st.metric("오늘의 시민 참여", "12 건") 

st.divider()

# 리스트 및 상세화면
left_col, right_col = st.columns([1, 1])

with left_col:
    display_title = selected_gu if selected_gu != '전체' else '서울시 전체'
    st.subheader(f"📋 {display_title} 착한업소 목록")
    
    if filtered_df.empty:
        st.warning("조건에 맞는 가게가 없습니다.")
    else:
        # 보여줄 컬럼 선택
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

# 입력폼
        st.markdown("#### 💬 정보 보완하기")
        with st.form("info_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.text_input("닉네임", "시민1")
            with col_b:
                st.selectbox("정보 유형", ["자랑거리", "찾아오는 길", "메뉴 추천"])
            
            content = st.text_area("내용 입력", placeholder="예: 사장님이 친절해요!")
            
            if st.form_submit_button("등록하기"):
                if content.strip():
                    st.balloons()
                    st.success(f"감사합니다! '{target_store}' 정보가 등록되었습니다.")
                else:
                    st.error("내용을 입력해주세요.")
    else:
        st.info("가게 목록이 없습니다.")
