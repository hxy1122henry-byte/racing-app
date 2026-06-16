import streamlit as st
import pandas as pd
from datetime import datetime

# 设置网页标题和图标
st.set_page_config(page_title="超级赛车联机大奖赛", page_icon="🏎️", layout="wide")

st.title("🏎️ 超级赛车联机圈速榜")
st.write("数据实时同步至云端，兄弟们冲起来！")

# 尝试从 Streamlit Secrets 读取谷歌表格链接
try:
    sheet_url = st.secrets["generic_config"]["spreadsheet_url"]
except Exception:
    sheet_url = None

if not sheet_url:
    st.warning("⚠️ 提示：尚未在 Streamlit 后台配置谷歌表格链接（Secrets），当前数据仅在本地展示。")

# --- 模拟数据交互（如果配置了表格会从网络读取，这里做核心逻辑展示） ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["选手", "赛道", "赛车", "圈速(秒)", "提交时间"])

# 输入区域
with st.form("lap_time_form", clear_on_submit=True):
    st.subheader("🏁 提交你的新圈速")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        player = st.text_input("选手花名", placeholder="例如：宁博车神")
    with col2:
        track = st.selectbox("选择赛道", ["斯帕", "蒙扎", "银石", "铃鹿", "红牛环"])
    with col3:
        car = st.text_input("驾驶赛车", placeholder="例如：RB20")
    with col4:
        lap_time = st.number_input("圈速（秒）", min_value=0.0, max_value=600.0, value=90.0, step=0.1)
    
    submit_btn = st.form_submit_with_button("💥 轰油门！提交成绩")

if submit_btn and player:
    new_data = {
        "选手": player,
        "赛道": track,
        "赛车": car,
        "圈速(秒)": lap_time,
        "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_data])], ignore_index=True)
    st.success(f"🎉 恭喜 {player} 成功提交成绩！")

# 展示榜单
st.subheader("🏆 全服实时圈速排行（按圈速由快到慢）")
if not st.session_state.data.empty:
    sorted_df = st.session_state.data.sort_values(by="圈速(秒)", ascending=True)
    st.dataframe(sorted_df, use_container_width=True)
else:
    st.info("目前还没有圈速记录，快来拿下全服一哥！")
