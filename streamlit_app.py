iimport streamlit as st
import pandas as pd
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 찾기", 
    page_icon="🏙️", 
    layout="wide"
)

st.title("🔎 서울시 착한가격업소 정보 공유소")

# [안내 박스] 요청하신 문구 적용됨
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
        가격, 품질, 위생 등 **행정안전부 기준에 의거한 평가**를 통해 구청장이 지정한 업소입니다.
        """)
        st.markdown("""
        👉 **'자랑거리'나 '찾아오는 길' 정보가 비어있는 곳**을 찾아 여러분의 제보로 채워주세요!
        """)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
# 서울시 25개 자치구 리스트 (고정값)
SEOUL_GU_LIST = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", 
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", 
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

# [1] 메인 데이터(착한업소 현황) 로드
@st.cache_data
def load_main_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        df = pd.read_csv(file_name, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    # 자치구 찾기 (주소 내 텍스트 매칭)
    def find_gu(address):
        if not isinstance(address, str): return "기타"
        for gu in SEOUL_GU_LIST:
            if gu in address: return gu
        return "기타"

    df['자치구'] = df['업소 주소'].apply(find_gu)
    
    # 전화번호 결측치 처리 ('-'로 표시)
    df['업소 전화번호'] = df['업소 전화번호'].fillna("-")
    
    # [정렬 로직] 한글 이름 우선 정렬
    df['업소명'] = df['업소명'].astype(str)
    mask_hangul = df['업소명'].str.match(r'^[가-힣]') # 한글로 시작하는지 확인
    df_hangul = df[mask_hangul].sort_values(by='업소명')
    df_others = df[~mask_hangul].sort_values(by='업소명')
    
    # 한글 목록 뒤에 숫자/영어 목록 붙이기
    return pd.concat([df_hangul, df_others])

# [2] 리뷰(시민 참여) 데이터 로드 - 실시간 반영을 위해 캐싱(@st.cache_data) 사용 안 함
def load_reviews():
    review_file = "user_reviews.csv"
    if os.path.exists(review_file):
        # 파일이 있으면 불러오기
        return pd.read_csv(review_file)
    else:
        # 파일이 없으면 빈 데이터프레임 생성 (컬럼 틀만 만듦)
        return pd.DataFrame(columns=["업소명", "닉네임", "유형", "내용", "날짜"])

# [3] 리뷰 저장 함수
def save_review(store_name, nickname, review_type, content):
    review_file = "user_reviews.csv"
    # 저장할 데이터 한 줄 만들기
    new_data = pd.DataFrame([{
        "업소명": store_name,
        "닉네임": nickname,
        "유형": review_type,
        "내용": content,
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M") # 현재 시간
    }])
    
    # 파일에 이어쓰기 (mode='a')
    if not os.path.exists(review_file):
        new_data.to_csv(review_file, index=False, encoding="utf-8-sig")
    else:
        new_data.to_csv(review_file, mode='a', header=False, index=False, encoding="utf-8-sig")

# 프로그램 시작 시 데이터 불러오기
try:
    df = load_main_data()
    reviews_df = load_reviews()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 (필터링)
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 지역 및 업종 선택")

st.sidebar.markdown("### 1️⃣ 지역 선택 (필수)")
# 25개 구 리스트만 보여줌
selected_gu = st.sidebar.selectbox("어느 구를 볼까요?", ["전체"] + SEOUL_GU_LIST, index=0)

st.sidebar.markdown("---") 

st.sidebar.markdown("### 2️⃣ 업종 선택")
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("원하는 업종을 고르세요", cat_list, default=cat_list)

st.sidebar.markdown("---")

st.sidebar.markdown("### 3️⃣ 가게 이름 찾기")
keyword = st.sidebar.text_input("가게명 입력 (선택)")

# --- 필터링 적용 ---
filtered_df = df.copy()

if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]

if selected_cat:
    filtered_df = filtered_df[filtered_df['분류코드명'].isin(selected_cat)]

if keyword:
    filtered_df = filtered_df[filtered_df['업소명'].str.contains(keyword)]

# -----------------------------------------------------------------------------
# 4. 메인 화면
# -----------------------------------------------------------------------------

# (Tip 문구는 삭제했습니다)

# [현황판] 실시간 데이터 반영
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("선택된 지역 가게 수", f"{len(filtered_df)} 곳")

with col2:
    missing_count = filtered_df['자랑거리'].isna().sum() + (filtered_df['자랑거리'] == '').sum()
    st.metric("정보 보완 필요 😢", f"{missing_count} 곳", delta="제보 환영", delta_color="inverse")

with col3:
    # [오늘의 시민 참여] 진짜 카운트 계산
    if not reviews_df.empty:
        today_str = datetime.now().strftime("%Y-%m-%d") # 오늘 날짜 (예: 2023-10-25)
        # 날짜 컬럼이 오늘 날짜로 시작하는 데이터만 필터링
        today_count = len(reviews_df[reviews_df['날짜'].str.startswith(today_str)])
    else:
        today_count = 0
        
    st.metric("오늘의 시민 참여", f"{today_count} 건", delta="실시간 집계 중 🔴") 

st.divider()

# [좌우 레이아웃]
left_col, right_col = st.columns([1, 1])

# [왼쪽] 리스트 뷰
with left_col:
    display_title = selected_gu if selected_gu != '전체' else '서울시 전체'
    st.subheader(f"📋 {display_title} 착한업소 목록")
    
    if filtered_df.empty:
        st.warning("조건에 맞는 가게가 없습니다.")
    else:
        # 화면에 보여줄 컬럼만 선택
        display_cols = ['업소명', '분류코드명', '자치구', '업소 전화번호']
        st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)

# [오른쪽] 상세 정보 및 제보
with right_col:
    st.subheader("✍️ 상세 정보 & 제보하기")
    
    # 필터링된 목록에 있는 가게만 선택 가능
    store_list = filtered_df['업소명'].unique()
    
    if len(store_list) > 0:
        target_store = st.selectbox("가게를 선택하세요:", store_list)
        store_data = filtered_df[filtered_df['업소명'] == target_store].iloc[0]
        
        # 1. 가게 정보 카드
        with st.container(border=True):
            st.markdown(f"### 🏠 {target_store}")
            st.write(f"**업종:** {store_data['분류코드명']}")
            st.write(f"**위치:** {store_data['자치구']}")
            st.write(f"**주소:** {store_data['업소 주소']}")
            st.write(f"**전화:** {store_data['업소 전화번호']}")
            
            st.markdown("---")
            
            pride = store_data['자랑거리']
            # 자랑거리가 비어있거나 공백이면 경고, 아니면 출력
            if pd.isna(pride) or str(pride).strip() == '':
                st.warning("📢 **등록된 자랑거리가 없습니다!**")
                st.info("이 가게의 매력을 가장 먼저 알려주세요.")
            else:
                st.success(f"**✨ 자랑거리:** {pride}")

        # 2. 시민 제보 현황 (리뷰 보여주기)
        st.markdown(f"#### 💬 시민들의 생생 제보")
        
        # 현재 선택된 가게의 리뷰만 필터링
        if not reviews_df.empty:
            store_reviews = reviews_df[reviews_df['업소명'] == target_store]
        else:
            store_reviews = pd.DataFrame()

        if not store_reviews.empty:
            # 최신순으로 보여주기 위해 역순 정렬
            for idx, row in store_reviews[::-1].iterrows():
                st.info(f"**[{row['유형']}] {row['닉네임']}**: {row['내용']} ({row['날짜']})")
        else:
            st.caption("아직 등록된 제보가 없습니다. 첫 번째 제보자가 되어주세요! 👇")

        # 3. 제보 입력 폼 (데이터 저장)
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
                    # CSV 파일에 저장
                    save_review(target_store, nickname, review_type, content)
                    
                    # 성공 메시지 및 화면 새로고침
                    st.balloons()
                    st.success(f"저장 완료! '{target_store}'에 정보가 등록되었습니다.")
                    st.rerun() # 즉시 새로고침해서 내가 쓴 글이 보이게 함
                else:
                    st.error("내용을 입력해주세요.")

    else:
        st.info("가게 목록이 없습니다.")
