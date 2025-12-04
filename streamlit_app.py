import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 찾기", 
    page_icon="🔎", 
    layout="wide"
)

st.title("🔎 서울시 착한가격업소 정보 공유소")
st.markdown("""
> **"여러분의 제보가 필요합니다!"** > 공공데이터에 비어있는 '자랑거리'와 '찾아오는 길' 정보를 시민 여러분이 직접 채워주세요.
""")

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (오류 없이 읽기)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        # 윈도우 엑셀 저장 포맷
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        # 일반 포맷
        df = pd.read_csv(file_name, encoding='utf-8')
    
    df.columns = df.columns.str.strip()
    
    # 자치구(구 이름) 컬럼 만들기
    if '자치구' not in df.columns:
        df['자치구'] = df['업소 주소'].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else "기타")
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다! 파일을 같은 폴더에 넣어주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 강력한 검색 기능
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 원하는 가게 찾기")

# 1) 지역 선택
gu_list = ["전체"] + sorted(df['자치구'].unique().tolist())
selected_gu = st.sidebar.selectbox("지역(구) 선택", gu_list)

# 2) 업종 선택
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("어떤 서비스를 찾으세요?", cat_list, default=cat_list)

# 3) 검색어
keyword = st.sidebar.text_input("가게 이름 검색")

# --- 필터링 로직 ---
filtered_df = df.copy()

if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]

if selected_cat:
    filtered_df = filtered_df[filtered_df['분류코드명'].isin(selected_cat)]

if keyword:
    filtered_df = filtered_df[filtered_df['업소명'].str.contains(keyword)]

# -----------------------------------------------------------------------------
# 4. 메인 화면 구성
# -----------------------------------------------------------------------------

# [현황판]
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("검색된 가게", f"{len(filtered_df)} 곳")
with col2:
    # 자랑거리가 비어있는 곳 찾기
    missing_count = filtered_df['자랑거리'].isna().sum() + (filtered_df['자랑거리'] == '').sum()
    st.metric("정보가 부족한 가게 😢", f"{missing_count} 곳", delta="도와주세요!", delta_color="inverse")
with col3:
    st.metric("오늘 시민 참여", "15 건") # 예시 데이터

st.divider()

# [좌우 레이아웃] 왼쪽: 검색 결과 리스트 / 오른쪽: 상세 정보 및 댓글
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📋 가게 목록")
    
    if filtered_df.empty:
        st.warning("검색 결과가 없습니다.")
    else:
        # 깔끔하게 표로 보여주기 (원하는 컬럼만)
        display_cols = ['업소명', '분류코드명', '업소 전화번호', '자치구']
        st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)
        
        st.caption("👆 위 목록을 보고 오른쪽에서 가게를 선택해주세요.")

with right_col:
    st.subheader("✍️ 상세 정보 & 정보 보완")
    
    # 검색된 가게들 중에서 선택하게 함
    store_list = filtered_df['업소명'].unique()
    
    if len(store_list) > 0:
        target_store = st.selectbox("가게를 선택하세요:", store_list)
        
        # 선택한 가게의 데이터 한 줄 가져오기
        store_data = filtered_df[filtered_df['업소명'] == target_store].iloc[0]
        
        # --- [가게 상세 카드] ---
        with st.container(border=True):
            st.markdown(f"### 🏠 {target_store}")
            st.write(f"**업종:** {store_data['분류코드명']}")
            st.write(f"**전화:** {store_data['업소 전화번호']}")
            st.write(f"**주소:** {store_data['업소 주소']}")
            
            st.markdown("---")
            
            # 정보(자랑거리) 유무에 따라 다르게 표시
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
                    st.balloons() # 풍선 효과 🎉
                    st.success(f"감사합니다! '{target_store}'에 대한 소중한 정보가 공유되었습니다.")
                    # 여기에 실제 저장 코드(csv_save)를 넣으면 완벽
    else:
        st.info("왼쪽에서 검색 조건을 변경해보세요.")
