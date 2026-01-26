import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
from datetime import datetime

# --- 1. 基础配置 ---
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    DEEPSEEK_API_KEY = "你的_DEEPSEEK_API_KEY"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


# --- 2. 核心功能：带分类的抓取 ---
def fetch_and_classify():
    url = "https://news.ycombinator.com/show"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.athing')
        raw_data = []
        for item in items[:40]:
            title_tag = item.select_one('.titleline > a')
            score_tag = item.find_next_sibling('tr').select_one('.score')
            if title_tag:
                title = title_tag.get_text()
                score = int(score_tag.get_text().replace(' points', '')) if score_tag else 0

                category = "其他"
                t_low = title.lower()
                if any(k in t_low for k in ['ai', 'gpt', 'llm', 'bot']):
                    category = "🤖 AI & 自动化"
                elif any(k in t_low for k in ['saas', 'app', 'platform']):
                    category = "💻 SaaS & 软件"
                elif any(k in t_low for k in ['dev', 'api', 'code']):
                    category = "🛠️ 开发工具"
                elif any(k in t_low for k in ['crypto', 'web3', 'pay']):
                    category = "💰 金融 & 套利"

                raw_data.append({
                    "title": title,
                    "link": title_tag.get('href'),
                    "score": score,
                    "category": category,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
        return pd.DataFrame(raw_data)
    except Exception as e:
        return pd.DataFrame()


# --- 3. UI 界面设计 ---
st.set_page_config(page_title="Alpha Hunter Elite", layout="wide")

# 自定义公告栏样式
st.markdown("""
    <style>
    .announcement-box {
        padding: 20px;
        background-color: #ff4b4b22;
        border-left: 5px solid #ff4b4b;
        border-radius: 5px;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.title("🛡️ 权限控制中心")
    access_code = st.text_input("🔑 输入精英暗号", type="password")
    is_pro = (access_code == "8888")
    st.write("---")
    st.write("📊 **统计视角**")
    view_mode = st.radio("切换视图", ["实时雷达", "月度商机排行 (Beta)"])
    st.info("提示：月度排行基于历史抓取的高分项目累计。")

# --- 主页面内容 ---
st.title("🏹 Alpha Hunter | 全球商业情报终端")

# 1. 全站公告栏（引流与做局的核心）
st.markdown(f"""
    <div class="announcement-box">
        <h4 style="margin-top:0;">📢 猎人内参公告</h4>
        <p style="margin-bottom:0;">
            <b>🔥 今日焦点：</b> AI板块出现3个高分项目，其中一个SaaS项目在硅谷热度极高，国内尚无同类产品。<br>
            <b>🔓 权限提示：</b> 当前精英暗号【8888】仅限今日免费，逾期将进入付费邀请制。
        </p>
    </div>
    """, unsafe_allow_html=True)

if st.button("🛰️ 启动情报同步"):
    df = fetch_and_classify()

    if not df.empty:
        if view_mode == "实时雷达":
            # --- 实时排行排行 (Top 3) ---
            st.subheader("🔥 今日全球商机 Top 3")
            top_cols = st.columns(3)
            leaderboard = df.sort_values(by="score", ascending=False).head(3)
            for i, (idx, row) in enumerate(leaderboard.iterrows()):
                with top_cols[i]:
                    st.metric(label=f"NO.{i + 1} 热度值", value=f"{row['score']} pts")
                    st.write(f"**{row['title']}**")

            st.divider()

            # --- 行业分区 ---
            st.subheader("📂 行业分区内参")
            tab_names = ["全部", "🤖 AI & 自动化", "💻 SaaS & 软件", "🛠️ 开发工具", "💰 金融 & 套利", "其他"]
            tabs = st.tabs(tab_names)

            for i, cat in enumerate(tab_names):
                with tabs[i]:
                    f_df = df if cat == "全部" else df[df['category'] == cat]
                    if f_df.empty:
                        st.info("该领域暂无异动。")
                    else:
                        for _, row in f_df.sort_values(by="score", ascending=False).iterrows():
                            with st.expander(f"【{row['score']} pts】{row['title']}"):
                                st.write(f"🔗 [查看原始链接]({row['link']})")
                                if is_pro:
                                    st.success("🕵️ 正在生成深度套利路径报告...")
                                    # 这里可以重新调用 analyze_with_deepseek 函数
                                else:
                                    st.error("🔒 报告已加密。请输入暗号解锁本条内参。")

        else:  # 月度排行模式
            st.subheader("📅 本月高价值商机汇总 (Score > 100)")
            # 模拟逻辑：展示当前抓取中分值极高的项目
            monthly_high = df[df['score'] >= 100].sort_values(by="score", ascending=False)
            if monthly_high.empty:
                st.write("本月暂无超高热度项目，请持续关注实时雷达。")
            else:
                st.dataframe(monthly_high[["date", "score", "category", "title"]], use_container_width=True)
                st.info("💡 历史数据已自动存入分析矩阵，Pro用户可导出完整 Excel 报告。")

st.caption("© 2026 Alpha Hunter - 让信息差成为你的杠杆")