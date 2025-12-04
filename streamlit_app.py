import streamlit as st
import pandas as pd
import os
from datetime import datetime
import altair as alt

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 착한업소 찾기",
    page_icon="🏙️",
    layout="wide"
)

st.title("🔎 서울시 착한가격업소 정보 공유소")

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
        가격, 품질, 위생 등 **행정안전부 기준에 의거한 평가**를 통해 구청장이 지정한 업소입니다.
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
except FileNotF
