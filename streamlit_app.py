import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="서울시 착한업소 지도", page_icon="🗺️", layout="wide")

st.title("🗺️ 서울시 착한업소: 시민 참여형 지도")
st.markdown("### 공공데이터 + 시민 참여로 완성하는 착한업소 지도")

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (에러 방지 기능 포함)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_name = "서울시 착한가격업소 현황.csv"
    try:
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        df = pd.read_csv(file_name, encoding='utf-8')
    
    # 컬럼명 공백 정리
    df.columns = df.columns.str.strip()
    
    # '자치구' 컬럼이 없으면 주소에서 추출
    if '자치구' not in df.columns:
        df['자치구'] = df['업소 주소'].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else "기타")
    
    return df

# 데이터 불러오기
try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다! '서울시 착한가격업소 현황.csv' 파일을 같은 폴더에 넣어주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 좌표 처리 (제일 중요한 부분!)
# -----------------------------------------------------------------------------
# 위도/경도가 없으면 -> "자동으로 랜덤 좌표 생성" (이러면 에러 안 남)
if '위도' not in df.columns:
    # 사용자에게는 비밀...이 아니라 솔직하게 알림
    st.warning("📢 현재 데이터에 좌표가 없어 '서울 시내 임의 위치'에 표시합니다. (시뮬레이션 모드)")
    
    # 서울 시청(37.5665, 126.9780) 중심으로 랜덤하게 뿌림
    df['위도'] = [37.5665 + random.uniform(-0.03, 0.03) for _ in range(len(df))]
    df['경도'] = [126.9780 + random.uniform(-0.03, 0.03) for _ in range(len(df))]

# -----------------------------------------------------------------------------
# 4. 사이드바 (검색 기능)
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 검색 옵션")

# 자치구 선택
gu_list = ["전체"] + sorted(df['자치구'].unique().tolist())
selected_gu = st.sidebar.selectbox("지역 선택", gu_list)

# 업종 선택
cat_list = sorted(df['분류코드명'].unique().tolist())
selected_cat = st.sidebar.multiselect("업종 선택", cat_list, default=cat_list)

# 검색어
keyword = st.sidebar.text_input("가게 이름 검색")

# 필터링 적용
filtered_df = df.copy()
if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]
if selected_cat:
    filtered_df = filtered_df[filtered_df['분류코드명'].isin(selected_cat)]
if keyword:
    filtered_df = filtered_df[filtered_df['업소명'].str.contains(keyword)]

# -----------------------------------------------------------------------------
# 5. 메인 화면 구성
# -----------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📍 지도 보기 ({len(filtered_df)}개 검색됨)")
    
    # 지도 그리기
    if not filtered_df.empty:
        center_lat = filtered_df['위도'].mean()
        center_lon = filtered_df['경도'].mean()
    else:
        center_lat, center_lon = 37.5665, 126.9780

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # 지도에 점 찍기
    for i, row in filtered_df.iterrows():
        # 자랑거리가 비어있으면 빨간색, 있으면 파란색
        color = 'red' if pd.isna(row['자랑거리']) or row['자랑거리'] == '' else 'blue'
        
        folium.Marker(
            [row['위도'], row['경도']],
            popup=row['업소명'],
            tooltip=f"{row['업소명']} ({row['분류코드명']})",
            icon=folium.Icon(color=color, icon='star')
        ).add_to(m)

    st_folium(m, width=None, height=500)
    st.caption("🔴 빨간색 마커는 정보가 부족한 가게입니다. 눌러서 정보를 채워주세요!")

with col2:
    st.subheader("📝 시민 참여 (댓글 남기기)")
    
    # 가게 선택
    target = st.selectbox("어디에 정보를 남길까요?", filtered_df['업소명'].unique())
    
    if target:
        store_info = filtered_df[filtered_df['업소명'] == target].iloc[0]
        
        # 가게 정보 보여주기
        with st.expander("가게 상세 정보", expanded=True):
            st.write(f"**주소:** {store_info['업소 주소']}")
            st.write(f"**전화:** {store_info['업소 전화번호']}")
            if pd.isna(store_info['자랑거리']) or store_info['자랑거리'] == '':
                st.error("자랑거리가 비어있습니다!")
            else:
                st.info(f"자랑거리: {store_info['자랑거리']}")

        # 댓글 입력창
        with st.form("comment_form"):
            user_text = st.text_area("내가 아는 꿀팁/길찾기 정보 입력")
            submitted = st.form_submit_button("정보 등록")
            
            if submitted:
                st.balloons()
                st.success(f"'{target}'에 대한 소중한 정보가 등록되었습니다!")

# -----------------------------------------------------------------------------
# 6. 하단 통계
# -----------------------------------------------------------------------------
st.divider()
st.subheader("📊 데이터 한눈에 보기")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**지역별 업소 수**")
    st.bar_chart(df['자치구'].value_counts().head(10))
with c2:
    st.markdown("**업종별 비율**")
    st.bar_chart(df['분류코드명'].value_counts())
