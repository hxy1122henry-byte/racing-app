import streamlit as pd
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# =================【固定配置】=================
ADMIN_PASSWORD = "666"                        # 管理员暗号
SCORE_SYSTEM = {1: 25, 2: 18, 3: 15, 4: 12}   # 积分规则
DATA_FILE = "race_results.csv"                # 成绩文件
PLAYERS_FILE = "players_config.json"          # 车手配置文件
CALENDAR_FILE = "calendar_config.csv"         # 赛历配置文件
TEAMS_FILE = "teams_config.json"              # 车队配置文件

# =================【数据初始化加载】=================
# 1. 初始化车手
if os.path.exists(PLAYERS_FILE):
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        PLAYERS = json.load(f)
else:
    PLAYERS = []
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(PLAYERS, f, ensure_ascii=False)

# 2. 初始化车队
if os.path.exists(TEAMS_FILE):
    with open(TEAMS_FILE, "r", encoding="utf-8") as f:
        TEAMS = json.load(f)
else:
    TEAMS = {}
    with open(TEAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(TEAMS, f, ensure_ascii=False)

# 3. 初始化赛历
if os.path.exists(CALENDAR_FILE):
    df_calendar_base = pd.read_csv(CALENDAR_FILE)
    if "日期" in df_calendar_base.columns:
        df_calendar_base = df_calendar_base.drop(columns=["日期"])
    df_calendar_base = df_calendar_base.dropna(how="all").fillna("")
else:
    df_calendar_base = pd.DataFrame(columns=["站次", "赛道", "指定用车"])
    df_calendar_base.to_csv(CALENDAR_FILE, index=False)

# 4. 初始化成绩单
if os.path.exists(DATA_FILE):
    df_results = pd.read_csv(DATA_FILE)
    if "最快单圈" not in df_results.columns:
        df_results["最快单圈"] = "无"
else:
    df_results = pd.DataFrame(columns=["分站名称"] + PLAYERS + ["最快单圈"])

# =================【数据核心计算】=================
# 计算车手个人总积分 及 分站冠军数量
player_scores_dict = {player: 0 for player in PLAYERS}
player_wins_dict = {player: 0 for player in PLAYERS} # 冠军数统计

INV_SCORE_SYSTEM = {v: k for k, v in SCORE_SYSTEM.items()}

if not df_results.empty:
    for player in PLAYERS:
        # 算积分
        if player in df_results.columns:
            base_score = df_results[player].sum()
            
            # 算分站冠军数（名次为1，即得分为25分的次数）
            # 或者是根据原始得分反推名次为1的次数
            player_wins_dict[player] = (df_results[player] == SCORE_SYSTEM[1]).sum()
        else:
            base_score = 0
            
        fastest_lap_count = (df_results["最快单圈"] == player).sum()
        player_scores_dict[player] = int(base_score + fastest_lap_count)

# 生成车手积分榜（严格降序）
total_scores = pd.DataFrame({"车手": list(player_scores_dict.keys()), "总积分": list(player_scores_dict.values())})
if not total_scores.empty:
    total_scores = total_scores.sort_values(by="总积分", ascending=False).reset_index(drop=True)
else:
    total_scores = pd.DataFrame(columns=["车手", "总积分"])

# 生成分站冠军榜（严格降序）
total_wins = pd.DataFrame({"车手": list(player_wins_dict.keys()), "冠军分站数": list(player_wins_dict.values())})
if not total_wins.empty:
    total_wins = total_wins.sort_values(by="冠军分站数", ascending=False).reset_index(drop=True)
else:
    total_wins = pd.DataFrame(columns=["车手", "冠军分站数"])

# 计算车队总积分（严格降序）
team_scores_list = []
for team_name, team_members in TEAMS.items():
    team_total = 0
    for member in team_members:
        if member in player_scores_dict:
            team_total += player_scores_dict[member]
    team_scores_list.append({"车队": team_name, "阵容": "、".join(team_members), "车队总积分": team_total})

if team_scores_list:
    df_team_scores = pd.DataFrame(team_scores_list).sort_values(by="车队总积分", ascending=False).reset_index(drop=True)
else:
    df_team_scores = pd.DataFrame(columns=["车队", "阵容", "车队总积分"])

# 动态计算赛历状态
completed_races_count = len(df_results)
dynamic_calendar = []
for idx, row in df_calendar_base.iterrows():
    race_copy = row.to_dict()
    if idx < completed_races_count:
        race_copy["状态"] = "🏁 已完赛"
    else:
        race_copy["状态"] = "⏳ 未开始"
    dynamic_calendar.append(race_copy)


# =================【前端页面渲染】=================
st.set_page_config(page_title="超级赛车联机大奖赛", layout="wide")
st.title("🏁 赛车联机大奖赛完全体系统")
st.markdown("---")

# 1. 【第一梯队】：官方赛历放最前面
st.markdown("### 🗓️ 赛季官方赛历 (含指定车型)")
if dynamic_calendar:
    df_calendar_show = pd.DataFrame(dynamic_calendar)
    st.dataframe(df_calendar_show, use_container_width=True, hide_index=True)
else:
    st.info("📅 暂无赛历配置，请超级干事在控制台编辑并保存官方赛历！")

st.markdown("---")

# 2. 【第二梯队】：各类荣誉排行榜
tab_show_player, tab_show_team = st.tabs(["🏆 个人车手荣誉榜", "🏎️ 俱乐部车队积分榜"])

with tab_show_player:
    if not total_scores.empty:
        # 分为上下或左右两个子模块，这里用两行分别展示“积分”和“冠军数”更清晰
        sub_tab_score, sub_tab_wins = st.tabs(["💎 车手积分榜", "🥇 分站冠军数榜"])
        
        with sub_tab_score:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("🏆 车手积分排行 (高分在上)")
                display_df = total_scores.copy()
                display_df.index = display_df.index + 1
                st.dataframe(display_df, use_container_width=True)
            with col2:
                st.subheader("📊 车手积分实时图")
                fig = px.bar(total_scores, x="车手", y="总积分", color="车手", text="总积分", template="plotly_dark")
                fig.update_layout(yaxis=dict(range=[0, max(10, total_scores["总积分"].max() * 1.1)]))
                st.plotly_chart(fig, use_container_width=True)
                
        with sub_tab_wins:
            col_w1, col_w2 = st.columns([1, 2])
            with col_w1:
                st.subheader("🥇 胜场多者在上")
                display_wins_df = total_wins.copy()
                display_wins_df.index = display_wins_df.index + 1
                st.dataframe(display_wins_df, use_container_width=True)
            with col_w2:
                st.subheader("📊 车手夺冠次数图")
                fig_wins = px.bar(total_wins, x="车手", y="冠军分站数", color="车手", text="冠军分站数", template="plotly_dark")
                fig_wins.update_layout(yaxis=dict(range=[0, max(5, total_wins["冠军分站数"].max() * 1.2)]))
                st.plotly_chart(fig_wins, use_container_width=True)
    else:
        st.info("💡 暂无自由车手名单，请先在管理员控制台添加参赛车手！")

with tab_show_team:
    if not df_team_scores.empty:
        col_t1, col_t2 = st.columns([4, 5])
        with col_t1:
            st.subheader("👑 车队总积分排行 (高分在上)")
            display_team_df = df_team_scores.copy()
            display_team_df.index = display_team_df.index + 1
            st.dataframe(display_team_df, use_container_width=True)
        with col_t2:
            st.subheader("📊 车队积分对比图")
            fig_team = px.bar(df_team_scores, x="车队", y="车队总积分", color="车队", text="车队总积分", template="plotly_dark")
            fig_team.update_layout(yaxis=dict(range=[0, max(10, df_team_scores["车队总积分"].max() * 1.1)]))
            st.plotly_chart(fig_team, use_container_width=True)
    else:
        st.info("💡 暂无车队数据，请超级干事在控制台创建车队并分配队员！")

st.markdown("---")

# 3. 【第三梯队】：历史分站成绩明细放最后
st.markdown("### 📅 历史分站成绩明细")
if not df_results.empty:
    st.dataframe(df_results, use_container_width=True, hide_index=True)
else:
    st.info("暂无赛场数据，等待干事录入！")


# =================【管理员后台】=================
st.markdown("---")
st.subheader("🔒 赛事超级干事控制台")

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    password_input = st.text_input("请输入管理员暗号以解锁全部配置：", type="password")
    if password_input == ADMIN_PASSWORD:
        st.session_state["admin_logged_in"] = True
        st.rerun()
    elif password_input != "":
        st.error("暗号错误！")

if st.session_state["admin_logged_in"]:
    welcome_col, logout_col = st.columns([3, 1])
    with welcome_col:
        st.success("密码正确！已解锁全动态编辑功能。")
    with logout_col:
        if st.button("🔒 退出管理员模式", type="primary", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.rerun()
            
    tab_score, tab_players, tab_team_admin, tab_calendar = st.tabs([
        "📝 成绩录入与修正", 
        "👥 参赛车手管理", 
        "🏎️ 车队与阵容管理", 
        "📅 赛季赛历编辑"
    ])
    
    # ---- TAB 1：成绩管理 ----
    with tab_score:
        if PLAYERS:
            admin_col1, admin_col2 = st.columns(2)
            with admin_col1:
                st.write("**录入新成绩**")
                with st.form("race_form", clear_on_submit=True):
                    suggested_name = f"第 {len(df_results)+1} 站"
                    if len(df_results) < len(df_calendar_base):
                        r_info = df_calendar_base.iloc[len(df_results)]
                        suggested_name = f"{r_info['站次']} - {r_info['赛道']} ({r_info['指定用车']})"
                        
                    race_name = st.text_input("分站名称", value=suggested_name)
                    input_ranks = {}
                    new_race_data = {"分站名称": race_name}
                    
                    cols = st.columns(len(PLAYERS))
                    for i, player in enumerate(PLAYERS):
                        with cols[i]:
                            rank = st.number_input(f"{player} 名次", min_value=1, max_value=20, value=i+1, step=1, key=f"add_{player}")
                            input_ranks[player] = rank
                            new_race_data[player] = SCORE_SYSTEM.get(rank, 0)
                    
                    fastest_player = st.selectbox("⏱️ 本站最快单圈：", options=["无"] + PLAYERS)
                    new_race_data["最快单圈"] = fastest_player
                    
                    if st.form_submit_button("💾 提交本站成绩"):
                        all_ranks = list(input_ranks.values())
                        if len(set(all_ranks)) != len(all_ranks):
                            st.error("❌ 提交失败：名次不能重复！")
                        else:
                            new_row = pd.DataFrame([new_race_data])
                            df_results = pd.concat([df_results, new_row], ignore_index=True)
                            df_results.to_csv(DATA_FILE, index=False)
                            st.success("🎉 提交成功！")
                            st.rerun()
                            
            with admin_col2:
                st.write("**修正指定分站成绩**")
                if not df_results.empty:
                    race_options = df_results["分站名称"].tolist()
                    selected_race = st.selectbox("请选择要修改的分站：", options=race_options)
                    race_idx = df_results[df_results["分站名称"] == selected_race].index[0]
                    current_row = df_results.loc[race_idx]
                    
                    INV_SCORE_SYSTEM = {v: k for k, v in SCORE_SYSTEM.items()}
                    with st.form("edit_form"):
                        edit_ranks = {}
                        updated_race_data = {"分站名称": selected_race}
                        edit_cols = st.columns(len(PLAYERS))
                        for i, player in enumerate(PLAYERS):
                            with edit_cols[i]:
                                curr_score = current_row[player] if player in current_row else 0
                                curr_rank = INV_SCORE_SYSTEM.get(curr_score, i+1)
                                new_rank = st.number_input(f"{player} 新名次", min_value=1, max_value=20, value=int(curr_rank), step=1, key=f"edit_{player}")
                                edit_ranks[player] = new_rank
                                updated_race_data[player] = SCORE_SYSTEM.get(new_rank, 0)
                        
                        current_fastest = current_row["最快单圈"] if "最快单圈" in current_row else "无"
                        fl_options = ["无"] + PLAYERS
                        default_fl_idx = fl_options.index(current_fastest) if current_fastest in fl_options else 0
                        new_fastest_player = st.selectbox("⏱️ 修改最快单圈：", options=fl_options, index=default_fl_idx)
                        updated_race_data["最快单圈"] = new_fastest_player
                        
                        if st.form_submit_button("🔥 覆盖修改本站成绩"):
                            all_edit_ranks = list(edit_ranks.values())
                            if len(set(all_edit_ranks)) != len(all_edit_ranks):
                                st.error("❌ 修改失败：名次有重复！")
                            else:
                                for player in PLAYERS:
                                    df_results.loc[race_idx, player] = updated_race_data[player]
                                df_results.loc[race_idx, "最快单圈"] = updated_race_data["最快单圈"]
                                df_results.to_csv(DATA_FILE, index=False)
                                st.success("覆盖更新成功！")
                                st.rerun()
                    
                    st.markdown("---")
                    st.write("🚨 **不小心提交错了？单站成绩撤销**")
                    last_race_name = df_results.iloc[-1]["分站名称"]
                    st.warning(f"当前最后一次录入的比赛为：**{last_race_name}**")
                    
                    confirm_delete = st.checkbox(f"我确认要彻底删除【{last_race_name}】的所有成绩数据")
                    if st.button("🔥 立即撤销并删除该站成绩", type="primary"):
                        if confirm_delete:
                            df_results = df_results.drop(df_results.index[-1]).reset_index(drop=True)
                            df_results.to_csv(DATA_FILE, index=False)
                            st.success(f"💥 成功撤销！【{last_race_name}】的成绩已被彻底清除。")
                            st.rerun()
                        else:
                            st.error("请先勾选上方的“我确认要彻底删除...”复选框以解锁删除按钮！")
                else:
                    st.info("暂无历史历史数据，无需撤销。")
        else:
            st.warning("⚠️ 必须先在‘参赛车手管理’标签页中添加至少一名车手，才可进行成绩录入！")

    # ---- TAB 2：动态车手管理 ----
    with tab_players:
        st.write("👥 **实时管理参赛车手名单**")
        if PLAYERS:
            st.info(f"当前参赛车手： {', '.join(PLAYERS)}")
        else:
            st.info("💡 暂无注册车手，请在下方添加第一个参赛车手。")
        
        with st.form("add_player_form", clear_on_submit=True):
            new_player_name = st.text_input("➕ 输入新车手的外号：", placeholder="例如：大壮、车神小李")
            submit_player = st.form_submit_button("确认添加该车手")
            
            if submit_player:
                if new_player_name.strip() and new_player_name.strip() not in PLAYERS:
                    PLAYERS.append(new_player_name.strip())
                    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
                        json.dump(PLAYERS, f, ensure_ascii=False)
                    st.success(f"🎉 成功让 {new_player_name.strip()} 加盟大奖赛！输入框已重置。")
                    st.rerun()
                else:
                    st.error("❌ 添加失败：车手名字不能为空，且不能与现有车手重复！")
                
        st.warning("⚠️ 如果有哥们退赛，你可以在下面把不需要的人删掉，用英文逗号隔开：")
        players_str = st.text_area("重新编辑全体车手名单：", value=",".join(PLAYERS))
        if st.button("💾 保存全新车手阵容"):
            updated_players = [p.strip() for p in players_str.split(",") if p.strip()]
            with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_players, f, ensure_ascii=False)
            st.success("车手名单全新重组成功！")
            st.rerun()

    # ---- TAB 3：🏎️ 车队与阵容管理 ----
    with tab_team_admin:
        st.write("🏎️ **大奖赛俱乐部车队建制管理**")
        
        all_assigned_players = []
        for t_name, t_members in TEAMS.items():
            all_assigned_players.extend(t_members)
            
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.write("**新建/调整车队阵容**")
            with st.form("team_admin_form", clear_on_submit=True):
                new_team_name = st.text_input("📢 输入车队（俱乐部）名称：", placeholder="例如：法拉利、红牛车队")
                available_players = [p for p in PLAYERS if p not in all_assigned_players]
                
                st.write(f"💡 提示：已被其他车队签约的车手将自动隐藏。")
                selected_members = st.multiselect("👥 请选择该车队的正式成员（仅显示未签约自由车手）：", options=available_players)
                
                if st.form_submit_button("💾 确认创建/更新该车队"):
                    if new_team_name.strip():
                        TEAMS[new_team_name.strip()] = selected_members
                        with open(TEAMS_FILE, "w", encoding="utf-8") as f:
                            json.dump(TEAMS, f, ensure_ascii=False)
                        st.success(f"🎉 车队【{new_team_name}】阵容成功注册！")
                        st.rerun()
                    else:
                        st.error("车队名称不能为空！")
                    
        with t_col2:
            st.write("**当前车队花名册及解散**")
            if TEAMS:
                for t_name, t_m in list(TEAMS.items()):
                    m_str = "、".join(t_m) if t_m else "暂无队员"
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.info(f"🏁 **{t_name}** \n队员：{m_str}")
                    with c2:
                        if st.button("❌ 解散", key=f"del_team_{t_name}"):
                            del TEAMS[t_name]
                            with open(TEAMS_FILE, "w", encoding="utf-8") as f:
                                json.dump(TEAMS, f, ensure_ascii=False)
                            st.success(f"车队 {t_name} 已解散！")
                            st.rerun()
            else:
                st.info("目前还没有任何有效车队，快在左侧创建一个吧！")

    # ---- TAB 4：动态赛历编辑 ----
    with tab_calendar:
        st.write("📅 **实时编辑分站赛历与用车配置**")
        st.info("💡 增加新行直接在空白处填字即可。若要删行，请勾选那一行，并点击表格右上角的 🗑️ 图标。")
        
        column_configs = {
            "站次": st.column_config.TextColumn("站次", default=""),
            "赛道": st.column_config.TextColumn("赛道", default=""),
            "指定用车": st.column_config.TextColumn("指定用车", default=""),
        }
        
        display_base = df_calendar_base.copy().fillna("").astype(str)
        for col in display_base.columns:
            display_base[col] = display_base[col].apply(lambda x: "" if x.lower() == "none" else x)
        
        edited_cal_df = st.data_editor(
            display_base, 
            num_rows="dynamic", 
            use_container_width=True, 
            column_config=column_configs,
            key="cal_editor_v8"
        )
        
        if st.button("💾 保存赛历的所有改动"):
            cleaned_df = edited_cal_df.fillna("")
            cleaned_df = cleaned_df[
                (cleaned_df["站次"] != "") & 
                (cleaned_df["站次"].astype(str).str.lower() != "none") &
                (cleaned_df["赛道"] != "") &
                (cleaned_df["赛道"].astype(str).str.lower() != "none")
            ]
            df_calendar_base = cleaned_df.reset_index(drop=True)
            df_calendar_base.to_csv(CALENDAR_FILE, index=False)
            st.success("⚙️ 赛季官方新赛历已成功写入数据库！")
            st.rerun()
