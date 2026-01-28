import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
from datetime import datetime
import urllib3

# 禁用 SSL 警告（彻底解决你截图中的连接中断报错）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心配置 ---
try:
    # 优先读取本地 .streamlit/secrets.toml 或云端 Secrets
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    DEEPSEEK_API_KEY = "YOUR_KEY_HERE"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


# --- 2. 核心功能：情报抓取与自动分区 ---
def fetch_and_classify():
    url = "https://news.ycombinator.com/show"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        # 关键修复：verify=False 配合上面的 disable_warnings 解决网络握手失败
        res = requests.get(url, headers=headers, timeout=12, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.athing')

        raw_data = []
        for item in items[:40]:
            title_tag = item.select_one('.titleline > a')
            score_tag = item.find_next_sibling('tr').select_one('.score')

            if title_tag:
                title = title_tag.get_text()
                link = title_tag.get('href')
                score = int(score_tag.get_text().replace(' points', '')) if score_tag else 0

                # 智能分区逻辑
                category = "其他"
                t_low = title.lower()
                if any(k in t_low for k in ['ai', 'gpt', 'llm', 'bot']):
                    category = "🤖 AI & 自动化"
                elif any(k in t_low for k in ['saas', 'app', 'platform']):
                    category = "💻 SaaS & 软件"
                elif any(k in t_low for k in ['dev', 'api', 'code', 'git']):
                    category = "🛠️ 开发工具"
                elif any(k in t_low for k in ['crypto', 'web3', 'pay', 'coin']):
                    category = "💰 金融 & 套利"

                raw_data.append({
                    "title": title, "link": link, "score": score,
                    "category": category, "date": datetime.now().strftime("%Y-%m-%d")
                })
        return pd.DataFrame(raw_data)
    except Exception as e:
        st.error(f"📡 信号抓取失败: {str(e)}")
        return pd.DataFrame()


# --- 3. 核心功能：DeepSeek 商业拆解 ---
def analyze_with_deepseek(title):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "你是一个冷酷敏锐的商业套利专家。请用150字内拆解该项目的赚钱路径和国内落地可行性。"},
                {"role": "user", "content": f"项目名称：{title}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI 暂时无法联网: {str(e)}"


# --- 4. 界面展示 (UI) ---
st.set_page_config(page_title="Alpha Hunter Elite", layout="wide")

with st.sidebar:
    st.title("🛡️ 权限控制中心")
    # 输入 8888 解锁
    access_code = st.text_input("🔑 输入精英暗号", type="password")
    is_pro = (access_code == "8888")
    st.write("---")
    view_mode = st.radio("功能面板", ["实时雷达扫描", "月度商机排行 (Beta)"])

st.title("🏹 Alpha Hunter | 全球商业情报终端")

# 公告栏
st.markdown(f"""
    <div style="padding:15px; background-color:#ff4b4b22; border-left:5px solid #ff4b4b; border-radius:5px;">
        <h4 style="margin-top:0; color:#ff4b4b;">📢 猎人内参公告</h4>
        <p style="margin-bottom:0;">今日精英暗号【8888】限时开放！解锁后可查看 AI 深度套利内参。</p>
    </div>
    """, unsafe_allow_html=True)
st.write("")

if view_mode == "实时雷达扫描":
    if st.button("🛰️ 启动全网情报同步"):
        df = fetch_and_classify()

        if not df.empty:
            # A. 实时排行榜 (Top 3)
            st.subheader("🔥 今日全球商机热度榜 (Top 3)")
            top_cols = st.columns(3)
            leaderboard = df.sort_values(by="score", ascending=False).head(3)
            for i, (idx, row) in enumerate(leaderboard.iterrows()):
                with top_cols[i]:
                    st.metric(label=f"NO.{i + 1} 热度指数", value=f"{row['score']} pts")
                    st.write(f"**{row['title']}**")

            st.divider()

            # B. 行业分区展示
            st.subheader("📂 行业分区内参")
            tab_names = ["全部", "🤖 AI & 自动化", "💻 SaaS & 软件", "🛠️ 开发工具", "💰 金融 & 套利", "其他"]
            tabs = st.tabs(tab_names)

            for i, cat in enumerate(tab_names):
                with tabs[i]:
                    f_df = df if cat == "全部" else df[df['category'] == cat]
                    if f_df.empty:
                        st.info("该领域暂无异动情报。")
                    else:
                        for _, row in f_df.sort_values(by="score", ascending=False).iterrows():
                            with st.expander(f"【{row['score']} pts】{row['title']}"):
                                st.write(f"🔗 [查看原始链接]({row['link']})")
                                if is_pro:
                                    with st.spinner("🕵️ 正在调取精英级商业拆解..."):
                                        # 这里是修复截图问题的关键：真正调用函数并显示内容
                                        report = analyze_with_deepseek(row['title'])
                                        st.markdown("---")
                                        st.success(report)
                                else:
                                    st.error("🔒 商业内参已加密。请输入暗号解锁本条情报。")
        else:
            st.warning("信号灯暂无闪烁，请检查网络后重试。")

elif view_mode == "月度商机排行 (Beta)":
    st.subheader("📅 本月高价值商机汇总")
    st.write("请完成 Google Sheets 授权配置以激活历史数据存储。")

st.caption("© 2026 Alpha Hunter - 让信息差成为你的杠杆")