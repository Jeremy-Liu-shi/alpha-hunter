import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# --- 1. 配置自适应（优先读取云端 Secrets） ---
try:
    # 部署到 Streamlit Cloud 时，从后台 Secrets 读取
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    # 本地运行时，如果你没配 secrets，请手动填入你的 Key 进行测试
    DEEPSEEK_API_KEY = "你的_DEEPSEEK_API_KEY"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


# --- 2. 核心功能：情报抓取 ---
def fetch_hn_intelligence():
    """抓取 Hacker News Show 频道实时动态"""
    url = "https://news.ycombinator.com/show"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.athing')
        results = []
        for item in items[:15]:  # 每次扫描前15个精华
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
    except Exception as e:
        return []


# --- 3. 核心功能：深度商机拆解 (AI 换脑版) ---
def analyze_with_deepseek(title, is_pro):
    if not is_pro:
        return "🔒 **内容已加密**：AI 深度商业拆解报告仅对【精英猎人】开放。请在左侧侧边栏输入正确暗号。"

    # 注入“商业间谍”灵魂的指令
    prompt = f"""
    你是一个冷酷、敏锐的商业套利专家。
    目标项目："{title}"

    请以“情报内参”的口吻，完成以下拆解：
    1. 【核心盘】：用大白话撕掉它的技术外壳，告诉我它本质上是在赚谁的钱？核心痛点是什么？
    2. 【拆局】：它的护城河在哪里？是技术领先、还是由于信息差导致的暂时领先？
    3. 【套利指南】：如果我是国内的创业者，我该如何进行“降维打击”？请给出具体的切入路径（比如：改造成什么中文场景、利用哪个低成本流量渠道）。
    4. 【钱景】：预判这个生意的上限，是只能赚点零花钱，还是有做成垂直领域龙头的潜力？

    要求：禁止使用“可能”、“大概”、“多元化”等废话。要用断言，要用尖锐的视角。字数150字左右。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "你只关注赚钱逻辑，用词毒辣，直戳要害。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 报告生成失败，请检查 API 额度: {str(e)}"


# --- 4. Streamlit UI 界面 ---
st.set_page_config(page_title="Alpha Hunter V1.2", layout="wide")

# 侧边栏：做局的规则设定
with st.sidebar:
    st.title("🛡️ 权限控制中心")
    st.write("---")
    access_code = st.text_input("🔑 输入精英猎人暗号", type="password", help="正确暗号将解锁 AI 深度拆解功能")

    # 局的设计：只有掌握暗号的人才能看到真相
    if access_code == "8888":
        is_pro = True
        st.success("精英权限：已激活")
        st.balloons()
    else:
        is_pro = False
        st.warning("当前状态：访客（权限受限）")

    st.write("---")
    threshold = st.slider("情报价值门槛 (Points)", 10, 200, 30)
    st.info("提示：高分项目代表已被全球极客验证。")

# 主页面展示
st.title("🏹 Alpha Hunter | 全球商业套利雷达")
st.subheader("正在实时监控：Hacker News 全球首发项目")

if st.button("🛰️ 启动全网情报扫描"):
    with st.spinner("正在穿越防火墙，调取硅谷实时数据..."):
        intelligence = fetch_hn_intelligence()

        if not intelligence:
            st.error("雷达扫描受阻，请确保网络环境支持访问 Hacker News。")
        else:
            for entry in intelligence:
                if entry['score'] >= threshold:
                    with st.container():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f"### 🔥 {entry['score']} pts")
                            st.write(f"**项目名称**: {entry['title']}")
                            st.write(f"[🔗 直达原始项目]({entry['link']})")

                        with col2:
                            report = analyze_with_deepseek(entry['title'], is_pro)
                            if is_pro:
                                st.markdown("##### 🕵️ 精英级商业拆解内参：")
                                st.info(report)
                            else:
                                st.error(report)
                        st.divider()

st.caption("© 2026 Alpha Hunter - 只有看透局的人才能赢")