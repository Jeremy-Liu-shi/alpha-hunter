import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# --- 1. 配置与安全设置 ---
# 部署到公网时，请确保使用 st.secrets["DEEPSEEK_API_KEY"]
# 本地测试时，你可以暂时写成 "你的KEY"
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    DEEPSEEK_API_KEY = "这里填入你的DeepSeek_API_KEY"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


# --- 2. 核心功能：多源头抓取 ---
def fetch_hn_intelligence():
    """抓取 Hacker News Show 频道"""
    url = "https://news.ycombinator.com/show"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.athing')
        results = []
        for item in items[:15]:
            title_tag = item.select_one('.titleline > a')
            score_tag = item.find_next_sibling('tr').select_one('.score')
            if title_tag:
                results.append({
                    "title": title_tag.get_text(),
                    "link": title_tag.get('href'),
                    "score": int(score_tag.get_text().replace(' points', '')) if score_tag else 0,
                    "source": "Hacker News"
                })
        return results
    except:
        return []


# --- 3. 核心功能：DeepSeek 深度拆解 ---
def analyze_with_deepseek(title, is_pro):
    if not is_pro:
        return "🔒 **内容已加密**：AI 深度商业拆解报告仅对【精英猎人】开放。请在左侧侧边栏输入正确暗号。"

    prompt = f"""
    你是一个极其敏锐的商业间谍和套利专家。
    目标项目："{title}"
    请针对该项目进行深度拆解：
    1. 核心逻辑：它在解决什么人的什么问题？
    2. 盈利模式：它是如何实现变现的？
    3. 套利路径：如果在中国市场做，如何利用信息差降维打击？
    要求：用词毒辣，直戳要害，不要废话。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "你只关注赚钱逻辑，不讲废话。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 报告生成失败: {str(e)}"


# --- 4. Streamlit UI 界面设计 ---
st.set_page_config(page_title="Alpha Hunter V1.1", layout="wide")

# 侧边栏：做局的关键——权限控制
with st.sidebar:
    st.title("🛡️ 权限控制中心")
    st.write("---")
    access_code = st.text_input("🔑 输入精英猎人暗号", type="password")

    if access_code == "8888":  # 你可以把 8888 改成任何你喜欢的暗号
        is_pro = True
        st.success("精英权限：已激活")
        st.balloons()
    else:
        is_pro = False
        st.warning("当前状态：访客（仅限浏览标题）")

    st.write("---")
    st.header("雷达偏好")
    threshold = st.slider("情报热度门槛", 10, 200, 30)
    st.info("注：暗号是通往深层商机的唯一凭证。")

# 主界面
st.title("🏹 Alpha Hunter | 全球商业套利雷达")
st.subheader("正在监控：Hacker News / Reddit (Beta)")

if st.button("🛰️ 启动全网情报扫描"):
    with st.spinner("正在穿越防火墙，调取全球实时数据..."):
        intelligence = fetch_hn_intelligence()

        if not intelligence:
            st.error("雷达扫描受阻，请检查网络或稍后再试。")
        else:
            for entry in intelligence:
                if entry['score'] >= threshold:
                    with st.container():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f"### 🔥 {entry['score']} pts")
                            st.write(f"**源头**: {entry['source']}")
                            st.write(f"**项目**: {entry['title']}")
                            st.write(f"[查看原始链接]({entry['link']})")

                        with col2:
                            # 根据权限显示不同内容
                            report = analyze_with_deepseek(entry['title'], is_pro)
                            if is_pro:
                                st.markdown("##### 🕵️ 精英级商业拆解：")
                                st.info(report)
                            else:
                                st.error(report)
                        st.divider()

st.caption("© 2026 Alpha Hunter - 只有看透局的人才能赢")