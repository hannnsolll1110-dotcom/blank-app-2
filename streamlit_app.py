import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 헤더 (디자인 수정됨 ✨)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 찾기", 
    page_icon="🔎", 
    layout="wide"
)

st.title("🔎 서울시 착한가격업소 정보 공유소")

# 안내 박스 디자인
with st.container(border=True):
    col_a, col_b = st.columns([0.3, 4])
    
    with col_a:
        st.markdown("<h1 style='text-align: center;'>📢</h1>", unsafe_allow_html=True) 
        
    with col_b:
        st.markdown("### 착한가격업소란?")
        st.markdown("""
        물가 상승 시기에도 **저렴한 가격**과 **청결한 서비스**로 시민들에게 사랑받는 우리 동네 업소(음식점🥘, 미용실💈 등)입니다.  
        하지만 현재 **'자랑거리'나 '찾아오는 길' 정보가 비어있는 곳**이 많습니다. 😢
        
        👉 **여러분의 소중한 기억과 제보로 이 지도를 함께 완성해주세요!**
        """)

# -----------------------------------------------------------------------------
# 2. 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        df = pd.read_csv(file_name, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    # 자치구 컬럼 생성
    if '자치구' not in df.columns:
        df['자치구'] = df['업소 주소'].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else "기타")
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다! 파일을 같은 폴더에 넣어주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 단계별 검색 (지역 -> 업종)
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 검색 옵션")

st.sidebar.markdown("### 1️⃣ 지역 선택 (필수)")
# 자치구 리스트
gu_list = ["전체"] + sorted(df['자치구'].unique().tolist())
# '전체'가 기본값이지만, 사용자가 변경하도록 유도
selected_gu = st.sidebar.selectbox("어느 구를 찾으세요?", gu_list)

st.sidebar.markdown("---") # 구분선

st.sidebar.markdown("### 2️⃣ 업종 선택")
# 업종 리스트
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("어떤 서비스를 원하세요?", cat_list, default=cat_list)

st.sidebar.markdown("---") # 구분선

st.sidebar.markdown("### 3️⃣ 이름 검색")
keyword = st.sidebar.text_input("가게 이름(선택 사항)")

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
# 4. 메인 화면 구성
# -----------------------------------------------------------------------------

# [팁 메시지] 지역을 '전체'로 뒀을 때 사용자에게 팁 주기
if selected_gu == "전체":
    st.info("💡 **팁:** 왼쪽 사이드바에서 **'지역(구)'**를 선택하면 동네별로 모아서 볼 수 있어요!")

# [현황판]
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("검색된 가게", f"{len(filtered_df)} 곳")
with col2:
    missing_count = filtered_df['자랑거리'].isna().sum() + (filtered_df['자랑거리'] == '').sum()
    st.metric("정보가 부족한 가게 😢", f"{missing_count} 곳", delta="제보 필요!", delta_color="inverse")
with col3:
    st.metric("오늘 시민 참여", "15 건") 

st.divider()

# [좌우 레이아웃]
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader(f"📋 {selected_gu if selected_gu != '전체' else '서울시'} 가게 목록")
    
    if filtered_df.empty:
        st.warning("검색 결과가 없습니다.")
    else:
        # 보기 좋게 컬럼 정리
        display_cols = ['업소명', '분류코드명', '자치구', '업소 전화번호']
        st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)
        
        st.caption("👆 위 목록을 보고 오른쪽에서 가게를 선택해주세요.")

with right_col:
    st.subheader("✍️ 상세 정보 & 정보 보완")
    
    # 선택 박스에 데이터가 없으면 오류 나지 않게 처리
    store_list = filtered_df['업소명'].unique()
    
    if len(store_list) > 0:
        target_store = st.selectbox("가게를 선택하세요:", store_list)
        
        # 선택한 가게 데이터 가져오기
        store_data = filtered_df[filtered_df['업소명'] == target_store].iloc[0]
        
        # --- [가게 상세 카드] ---
        with st.container(border=True):
            st.markdown(f"### 🏠 {target_store}")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"**업종:** {store_data['분류코드명']}")
                st.write(f"**지역:** {store_data['자치구']}")
            with col_info2:
                st.write(f"**전화:** {store_data['업소 전화번호']}")
            
            st.write(f"**주소:** {store_data['업소 주소']}")
            
            st.markdown("---")
            
            # 정보(자랑거리) 유무 체크
            pride = store_data['자랑거리']
            
            if pd.isna(pride) or str(pride).strip() == '':
                st.warning("📢 **등록된 자랑거리가 없습니다!**")
                st.info("이 가게의 매력을 가장 먼저 알려주세요.")
            else:
                st.success(f"**✨ 자랑거리:** {pride}")

        # --- [시민 참여 입력폼] ---
        st.markdown("#### 💬 정보 보완하기")
        with st.form("info_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                user_name = st.text_input("닉네임", "시민1")
            with col_b:
                info_type = st.selectbox("어떤 정보인가요?", ["자랑거리 제보", "찾아오는 길 안내", "메뉴 추천"])
            
            content = st.text_area("내용을 입력해주세요", placeholder="예: 여기 김치찌개가 정말 맛있고 양이 많아요! 사장님도 친절하십니다.")
            
            submit_btn = st.form_submit_button("등록하기")
            
            if submit_btn:
                if content.strip() == "":
                    st.error("내용을 입력해주세요!")
                else:
                    st.balloons()
                    st.success(f"감사합니다! '{target_store}'에 대한 소중한 정보가 공유되었습니다.")
    else:
        st.info("조건에 맞는 가게가 없습니다. 검색 조건을 변경해보세요.")
