import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# =================【固定配置】=================
ADMIN_PASSWORD = "666"                        
SCORE_SYSTEM = {1: 25, 2: 18, 3: 15, 4: 12}   
DATA_FILE = "race_results.csv"                
PLAYERS_FILE = "players_config.json"          
CALENDAR_FILE = "calendar_config.csv"         
TEAMS_FILE = "teams_config.json"              

# =================【数据初始化加载】=================
if os.path.exists(PLAYERS_FILE):
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        PLAYERS = json.load(f)
else:
    PLAYERS = []
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(PLAYERS, f, ensure_ascii=False)

if os.path.exists(TEAMS_FILE):
    with open(TEAMS_FILE, "r", encoding="utf-8") as f:
        TEAMS = json.load(f)
else:
    TEAMS = {}
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(TEAMS, f, ensure_ascii=False)

if os.path.exists(CALENDAR_FILE):
    df_calendar_base = pd.read_csv(CALENDAR_FILE).dropna(how="all").fillna("")
else:
    df_calendar_base = pd.DataFrame(columns=["站次", "赛道", "指定用车"])
    df_calendar_base.to_csv(CALENDAR_FILE, index=False)

if os.path.exists(DATA_FILE):
    df_results = pd.read_csv(DATA_FILE)
    # 强制补全列，防止因添加车手导致报错
    for player in PLAYERS:
        if player not in df_results.columns:
            df_results[player] = 0
else:
    df_results = pd.DataFrame(columns=["分站名称"] + PLAYERS + ["最快单圈"])

# =================【数据核心计算】=================
player_scores_dict = {player: 0 for player in PLAYERS}
player_wins_dict = {player: 0 for player in PLAYERS}

if not df_results.empty:
    for player in PLAYERS:
        if player in df_results.columns:
            base_score = pd.to_numeric(df_results[player], errors='coerce').fillna(0).sum()
            player_wins_dict[player] = (df_results[player] == SCORE_SYSTEM.get(1, 0)).sum()
        else:
            base_score = 0
        fastest_lap_count = (df_results["最快单圈"] == player).sum()
        player_scores_dict[player] = int(base_score + fastest_lap_count)

total_scores = pd.DataFrame({"车手": list(player_scores_dict.keys()), "总积分": list(player_scores_dict.values())}).sort_values(by="总积分", ascending=False).reset_index(drop=True)
total_wins = pd.DataFrame({"车手": list(player_wins_dict.keys()), "冠军分站数": list(player_wins_dict.values())}).sort_values(by="冠军分站数", ascending=False).reset_index(drop=True)

# =================【前端页面渲染】=================
st.set_page_config(page_title="超级赛车联机大奖赛", layout="wide")
st.title("🏁 赛车联机大奖赛完全体系统")

tab_show_player, tab_show_team = st.tabs(["🏆 个人车手荣誉榜", "🏎️ 俱乐部车队积分榜"])
with tab_show_player:
    if not total_scores.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(total_scores, use_container_width=True)
        with col2:
            fig = px.bar(total_scores, x="车手", y="总积分", color="车手", text="总积分", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("🔒 赛事超级干事控制台")

if "admin_logged_in" not in st.session_state: st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    if st.text_input("请输入管理员暗号：", type="password") == ADMIN_PASSWORD:
        st.session_state["admin_logged_in"] = True
        st.rerun()
else:
    if st.button("🔒 退出管理员模式"):
        st.session_state["admin_logged_in"] = False
        st.rerun()
    st.success("管理员已登录，请在下方进行操作。")
