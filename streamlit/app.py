import streamlit as st
import psycopg2
import pandas as pd
import settings

@st.cache_data
def load_view(view_name: str):
    conn = psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        dbname=settings.PG_DB,
        user=settings.PG_USER,
        password=settings.PG_PASS,
    )
    query = f"SELECT * FROM {view_name};"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("Chzzk 채팅 데이터 분석 대시보드")

# 뷰 테이블 로딩
chat_counts = load_view("chat_counts_per_streamer")
unique_users = load_view("unique_users_per_streamer")

# 스트리머 선택
streamers = chat_counts["streamer_id"].unique()
selected_streamer = st.selectbox("스트리머 선택", streamers)

# 데이터 필터링
df_counts = chat_counts[chat_counts["streamer_id"] == selected_streamer]
df_users = unique_users[unique_users["streamer_id"] == selected_streamer]

# 시각화
st.subheader("일별 채팅 수")
st.line_chart(df_counts.set_index("chat_date")["msg_count"])

st.subheader("일별 고유 사용자 수")
st.line_chart(df_users.set_index("chat_date")["unique_users"])