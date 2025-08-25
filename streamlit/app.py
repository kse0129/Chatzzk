import streamlit as st
import psycopg2
import pandas as pd
from PIL import Image
from config.settings import *
import gc
import json

with open("config/streamer_list.json", "r", encoding="utf-8") as f:
    streamer_list = json.load(f)

streamer_map = {s["id"]: s["name"] for s in streamer_list}

def map_id2name(table):
    table.index = table.index.map(lambda x: streamer_map.get(x, x))
    return table

@st.cache_data
def load_view(view_name: str):
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )
    query = f"SELECT * FROM {view_name};"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("Chzzk 채팅 데이터 분석 대시보드")

# 사이드바 메뉴
st.sidebar.header("메뉴")
mode = st.sidebar.radio("보기", ["전체 스트리머", "스트리머별"])

# 뷰 테이블 로딩
chat_counts = load_view("chat_counts_per_streamer")
unique_users = load_view("unique_users_per_streamer")
chat_by_hour = load_view("chat_counts_by_hour")
user_activity = load_view("user_activity_per_streamer")
chat_length = load_view("chat_length_distribution")

if mode == "전체 스트리머":
    st.subheader("전체 스트리머")

    # 일별 전체 채팅 수
    st.subheader("일별 전체 채팅 수")
    daily_total = chat_counts.groupby("chat_date")["msg_count"].sum()
    st.line_chart(daily_total)

    # 스트리머별 채팅 수
    st.subheader("스트리머별 채팅 수")
    total_per_streamer = chat_counts.groupby("streamer_id")["msg_count"].sum()
    st.bar_chart(map_id2name(total_per_streamer))

    # 스트리머별 고유 유저 수
    st.subheader("스트리머별 채팅 시청자 수")
    unique_per_streamer = unique_users.groupby("streamer_id")["unique_users"].sum()
    st.bar_chart(map_id2name(unique_per_streamer))

    # 스트리머별 유사도
    st.subheader("스트리머별 유사도")
    wordcloud_dir = "../notebook/similarity_map"
    fname = f"similarity_map.png"
    fpath = os.path.join(wordcloud_dir, fname)
    if os.path.exists(fpath):
        img = Image.open(fpath)
        st.image(img, use_container_width=True)
        img.close()
    else:
        st.warning("Don't have similarity_map png")

    st.session_state.clear()
    gc.collect()

elif mode == "스트리머별":
    st.subheader("스트리머별")
    # 스트리머 선택
    streamers = chat_counts["streamer_id"].unique()
    selected_streamer = st.selectbox("스트리머 선택", streamers, format_func=lambda x: streamer_map.get(x, x))

    # 데이터 필터링
    df_counts = chat_counts[chat_counts["streamer_id"] == selected_streamer]
    df_users = unique_users[unique_users["streamer_id"] == selected_streamer]
    df_hour = chat_by_hour[chat_by_hour["streamer_id"] == selected_streamer]
    df_activity = user_activity[user_activity["streamer_id"] == selected_streamer]
    df_length = chat_length[chat_length["streamer_id"] == selected_streamer]

    # 시각화
    # 일별 채팅 수
    st.subheader("일별 채팅 수")
    st.line_chart(df_counts.set_index("chat_date")["msg_count"])

    # 일별 채팅 시청자 수
    st.subheader("일별 채팅 시청자 수")
    st.bar_chart(df_users.set_index("chat_date")["unique_users"])

    # 워드 클라우드
    st.subheader("채팅 워드클라우드")

    wordcloud_dir = "../notebook/wordclouds"
    fname = f"{selected_streamer}_wordcloud.png"
    fpath = os.path.join(wordcloud_dir, fname)

    if os.path.exists(fpath):
        img = Image.open(fpath)
        st.image(img, use_container_width=True)
        img.close()
    else:
        st.warning("Don't have wordcloud png")

    # 시간대별 채팅 분포
    st.subheader("시간대별 채팅 분포")
    hourly = df_hour.set_index("chat_hour")["msg_count"]
    st.bar_chart(hourly)

    # 채팅 참여 집중도
    st.subheader("참여 집중도 (Top 10 유저 vs 나머지)")
    df_sel = df_activity[df_activity["streamer_id"] == selected_streamer]

    plot_data = []
    for date, df_day in df_sel.groupby("chat_date"):
        df_day_sorted = df_day.sort_values("user_msg_count", ascending=False)
        top10 = df_day_sorted.head(10)["user_msg_count"].sum()
        others = df_day_sorted["user_msg_count"].sum() - top10

        plot_data.append({
            "chat_date": date,
            "top10": top10,
            "others": others
        })

    df_plot = pd.DataFrame(plot_data).sort_values("chat_date")
    st.bar_chart(df_plot.set_index("chat_date")[["top10", "others"]])

    # 채팅 길이 분포
    st.subheader("채팅 길이 분포")
    length_dist = df_length.groupby("msg_length")["msg_count"].sum()
    st.bar_chart(length_dist)

    st.session_state.clear()
    gc.collect()