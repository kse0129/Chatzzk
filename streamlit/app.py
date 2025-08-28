import os
from typing import List

import altair as alt
import pandas as pd
import psycopg2
import streamlit as st
import json
from PIL import Image
from config.settings import *

# ==============================
# 글로벌 설정
# ==============================
PAGE_TITLE = "Chatzzk"
THEME_BG = "#000000"
THEME_FG = "#FFFFFF"
THEME_ACCENT = "#00FF88"
THEME_MUTED = "#115926"
CHART_W = 350
CHART_H = 250

st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")

# CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Altair 테마
def _chzzk_dark():
    return {
        "config": {
            "background": THEME_BG,
            "title": {"color": THEME_FG, "fontSize": 16},
            "axis": {
                "domainColor": "#AAAAAA",
                "gridColor": "#333333",
                "labelColor": THEME_FG,
                "titleColor": THEME_FG,
            },
            "legend": {"labelColor": THEME_FG, "titleColor": THEME_FG},
            "view": {"stroke": "transparent"},
        }
    }

alt.themes.register("chzzk_dark", _chzzk_dark)
alt.themes.enable("chzzk_dark")

with open("config/streamer_list.json", "r", encoding="utf-8") as f:
    streamer_list = json.load(f)

streamer_map = {s["id"]: s["name"] for s in streamer_list}

def map_id2name(table):
    table.index = table.index.map(lambda x: streamer_map.get(x, x))
    return table

# ==============================
# 공통 유틸
# ==============================
@st.cache_data
def load_view(view_name: str) -> pd.DataFrame:
    """Postgres 뷰 전체 로드"""
    with psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    ) as conn:
        return pd.read_sql(f"SELECT * FROM {view_name};", conn)

def chart_line(df: pd.DataFrame, x: str, y: str, title: str = "") -> alt.Chart:
    return (
        alt.Chart(df, title=title)
        .mark_line()
        .encode(
            x=alt.X(x, axis=alt.Axis(title=None)),
            y=alt.Y(y, axis=alt.Axis(title=None)),
        )
        .properties(width=CHART_W, height=CHART_H)
        .configure_mark(color=THEME_ACCENT)
    )

def chart_bar(df: pd.DataFrame, x: str, y: str, title: str = "") -> alt.Chart:
    return (
        alt.Chart(df, title=title)
        .mark_bar()
        .encode(
            x=alt.X(x, axis=alt.Axis(title=None)),
            y=alt.Y(y, axis=alt.Axis(title=None)),
        )
        .properties(width=CHART_W, height=CHART_H)
        .configure_mark(color=THEME_ACCENT)
    )

def chart_area_stacked(df: pd.DataFrame, x: str, y_fields: List[str], title: str = "") -> alt.Chart:
    m = df.melt(id_vars=[x], value_vars=y_fields, var_name="group", value_name="value")
    return (
        alt.Chart(m, title=title)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X(x, axis=alt.Axis(title=None)),
            y=alt.Y("value:Q", stack="zero", axis=alt.Axis(title=None)),
            color=alt.Color("group:N", scale=alt.Scale(range=[THEME_ACCENT, THEME_MUTED])),
            tooltip=["group", "value", x],
        )
        .properties(width=CHART_W, height=CHART_H)
    )

def section(title: str, level: int = 4) -> None:
    st.markdown(f"{'#' * level} {title}")

# ==============================
# 데이터 로딩
# ==============================
chat_counts = load_view("chat_counts_per_streamer")
unique_users = load_view("unique_users_per_streamer")
chat_by_hour = load_view("chat_counts_by_hour")
user_activity = load_view("user_activity_per_streamer")
chat_length = load_view("chat_length_distribution")

# ==============================
# UI
# ==============================
st.title("Chzzk 채팅 데이터 대시보드")

st.sidebar.header("메뉴")
mode = st.sidebar.radio("보기", ["전체 스트리머", "스트리머별"])

# ==============================
# 전체 스트리머
# ==============================
if mode == "전체 스트리머":
    # 상단 요약 (스트리머 수 제외, 스트리머별과 동일 포맷)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 채팅 수", f"{chat_counts['msg_count'].sum():,}")
    col2.metric("총 유저 수", f"{unique_users['unique_users'].sum():,}")
    col3.metric("최대 일별 채팅", f"{chat_counts['msg_count'].max():,}")
    col4.metric("평균 채팅 길이", f"{chat_length['msg_length'].mean():.1f}")

    # 레이아웃: 왼쪽 2, 가운데 1, 오른쪽 2
    left, center, right = st.columns([1, 2, 1])

    with left:
        top_left = st.container()
        bottom_left = st.container()

    with right:
        top_right = st.container()
        bottom_right = st.container()

    # 왼쪽
    with top_left:
        daily_total = chat_counts.groupby("chat_date", as_index=False)["msg_count"].sum()
        st.altair_chart(chart_line(daily_total, "chat_date", "msg_count", "일별 채팅 수"))
    with bottom_left:
        total_users = unique_users.groupby("chat_date", as_index=False)["unique_users"].sum()
        st.altair_chart(chart_bar(total_users, "chat_date", "unique_users", "일별 채팅 유저 수"))

    # 가운데
    with center:
        sim_path = os.path.join("../notebook/similarity_map", "similarity_map.png")
        if os.path.exists(sim_path):
            with Image.open(sim_path) as img:
                st.image(img, caption="스트리머 채팅 유사도", use_container_width=True)
        else:
            st.warning("유사도 맵 없음")

    # 오른쪽
    with top_right:
        hourly_total = chat_by_hour.groupby("chat_hour", as_index=False)["msg_count"].sum()
        st.altair_chart(chart_bar(hourly_total, "chat_hour", "msg_count", "시간대별 전체 채팅 분포"))
    with bottom_right:
        plot_rows = []
        for date, df_day in user_activity.groupby("chat_date"):
            s = df_day.sort_values("user_msg_count", ascending=False)["user_msg_count"]
            top10 = s.head(10).sum()
            others = s.sum() - top10
            plot_rows.append({"chat_date": date, "Top 10": top10, "Others": others})
        df_plot = pd.DataFrame(plot_rows).sort_values("chat_date")
        st.altair_chart(
            chart_area_stacked(df_plot, "chat_date", ["Top 10", "Others"], "참여 집중도 (Top 10 vs Others)"),
            use_container_width=True,
        )

# ==============================
# 스트리머별
# ==============================
else:
    # 선택
    streamers = chat_counts["streamer_id"].unique()
    selected = st.selectbox("스트리머 선택", sorted(streamers.tolist()), format_func=lambda x: streamer_map.get(x, x))

    # 필터
    df_counts = chat_counts[chat_counts["streamer_id"] == selected].copy()
    df_users = unique_users[unique_users["streamer_id"] == selected].copy()
    df_hour = chat_by_hour[chat_by_hour["streamer_id"] == selected].copy()
    df_activity = user_activity[user_activity["streamer_id"] == selected].copy()
    df_length = chat_length[chat_length["streamer_id"] == selected].copy()

    # 상단 요약 (동일 포맷)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 채팅 수", f"{df_counts['msg_count'].sum():,}")
    col2.metric("총 유저 수", f"{df_users['unique_users'].sum():,}")
    col3.metric("최대 일별 채팅", f"{df_counts['msg_count'].max():,}")
    col4.metric("평균 채팅 길이", f"{df_length['msg_length'].mean():.1f}")

    # 레이아웃: 왼쪽 2, 가운데 1, 오른쪽 2
    left, center, right = st.columns([1, 2, 1])

    with left:
        top_left = st.container()
        bottom_left = st.container()

    with right:
        top_right = st.container()
        bottom_right = st.container()

    # 왼쪽
    with top_left:
        daily = df_counts.groupby("chat_date", as_index=False)["msg_count"].sum()
        st.altair_chart(chart_line(daily, "chat_date", "msg_count", "일별 채팅 추세"))
    with bottom_left:
        daily_u = df_users.groupby("chat_date", as_index=False)["unique_users"].sum()
        st.altair_chart(chart_line(daily_u, "chat_date", "unique_users", "일별 고유 사용자"))

    # 가운데
    with center:
        wc_path = os.path.join("../notebook/wordclouds", f"{selected}_wordcloud.png")
        if os.path.exists(wc_path):
            with Image.open(wc_path) as img:
                st.image(img, use_container_width=True)
        else:
            st.warning("워드클라우드 없음")

    # 오른쪽
    with top_right:
        hourly = df_hour.groupby("chat_hour", as_index=False)["msg_count"].sum()
        st.altair_chart(chart_bar(hourly, "chat_hour", "msg_count", "시간대별 채팅"))
    with bottom_right:
        rows = []
        for date, df_day in df_activity.groupby("chat_date"):
            s = df_day.sort_values("user_msg_count", ascending=False)["user_msg_count"]
            top10 = s.head(10).sum()
            others = s.sum() - top10
            rows.append({"chat_date": date, "Top 10": top10, "Others": others})
        df_plot = pd.DataFrame(rows).sort_values("chat_date")
        st.altair_chart(
            chart_area_stacked(df_plot, "chat_date", ["Top 10", "Others"], "참여 집중도 (Top 10 vs Others)"),
            use_container_width=True,
        )

