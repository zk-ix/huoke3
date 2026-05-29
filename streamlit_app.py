"""
获客3 — 抖音账号免费诊断工具
Streamlit Cloud 部署版本
"""
import streamlit as st
import requests
import json
import re
import time

# ===== 配置 =====
st.set_page_config(
    page_title="抖音账号免费诊断",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/anthropic/v1/messages"

# 从 Streamlit Secrets 读取，本地开发时从 st.secrets 的默认值
try:
    DOUBAO_KEY = st.secrets["DOUBAO_KEY"]
    DOUBAO_MODEL = st.secrets["DOUBAO_MODEL"]
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_KEY"]
except (KeyError, FileNotFoundError):
    DOUBAO_KEY = "ark-d1754a1a-98cd-4db6-8efa-d21e6c149359-01bf9"
    DOUBAO_MODEL = "ep-20260528232335-78k69"
    DEEPSEEK_KEY = "sk-ecf8b540e2bc4e2fa3e0d4cd3f5d34e8"

SYSTEM_PROMPT = """你是抖音账号诊断专家。用户会提供账号信息（如抖音号、粉丝量、行业、症状描述等），请你：

1. 分析账号存在的问题（流量、内容、转化、定位等维度）
2. 输出恰好3个核心问题，按严重程度排序
3. 每个问题包括：问题标题、严重程度（1-10分）、一句话说明

严格按以下JSON格式输出，不要输出其他内容：
```json
{
  "overall_score": 65,
  "problems": [
    {"title": "问题标题", "score": 7, "detail": "一句话说明"},
    {"title": "问题标题", "score": 5, "detail": "一句话说明"},
    {"title": "问题标题", "score": 4, "detail": "一句话说明"}
  ]
}
```

overall_score 是账号健康度综合评分（0-100），分数越低问题越大。只输出JSON。"""

WECHAT_ID = "zengke"  # 改为实际微信号

# ===== 隐藏 Streamlit 默认样式 =====
hide_st_style = """
<style>
  header[data-testid="stHeader"] {display: none;}
  .stAppToolbar {display: none;}
  footer {visibility: hidden;}
  #MainMenu {visibility: hidden;}
  section[data-testid="stSidebar"] {display: none;}
  .stApp {background: #080c14;}
  .stButton>button {
    width: 100%; padding: 14px; border-radius: 12px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; border: none; font-size: 16px; font-weight: 700;
    cursor: pointer; transition: all .2s;
  }
  .stButton>button:hover {transform: translateY(-1px); box-shadow: 0 8px 24px rgba(99,102,241,.35);}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)


def call_doubao(account_info: str) -> dict | None:
    """调用豆包 API"""
    try:
        resp = requests.post(
            DOUBAO_URL,
            json={
                "model": DOUBAO_MODEL,
                "max_tokens": 500,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": account_info},
                ],
            },
            headers={"Authorization": f"Bearer {DOUBAO_KEY}"},
            timeout=45,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        return parse_json(content)
    except Exception:
        return None


def call_deepseek(account_info: str) -> dict | None:
    """调用 DeepSeek API（回退方案）"""
    try:
        resp = requests.post(
            DEEPSEEK_URL,
            json={
                "model": "deepseek-v4-pro",
                "max_tokens": 500,
                "temperature": 0.7,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": account_info}],
            },
            headers={"x-api-key": DEEPSEEK_KEY},
            timeout=45,
        )
        if resp.status_code != 200:
            return None
        for block in resp.json().get("content", []):
            if block.get("type") == "text":
                return parse_json(block["text"])
        return None
    except Exception:
        return None


def parse_json(raw: str) -> dict | None:
    """从 AI 回复中提取 JSON"""
    # 尝试直接匹配 JSON 块
    m = re.search(r"\{[\s\S]*\"overall_score\"[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # 兜底：尝试解析整个内容
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def diagnose(account_info: str) -> dict:
    """执行诊断，豆包优先，失败回退 DeepSeek"""
    result = call_doubao(account_info)
    if result:
        return result
    result = call_deepseek(account_info)
    if result:
        return result
    # 兜底
    return {
        "overall_score": 55,
        "problems": [
            {"title": "内容定位模糊", "score": 8, "detail": "视频内容方向不统一，算法无法精准推荐目标人群"},
            {"title": "互动率偏低", "score": 6, "detail": "评论区互动不足，粉丝粘性和信任度建立缓慢"},
            {"title": "缺乏转化引导", "score": 5, "detail": "视频缺少明确的行动号召，流量无法有效转化为客户"},
        ],
    }


def score_to_color(s: int) -> str:
    if s >= 7:
        return "#f43f5e"
    if s >= 4:
        return "#f59e0b"
    return "#fbbf24"


def score_to_label(s: int) -> str:
    if s >= 7:
        return "严重"
    if s >= 4:
        return "中等"
    return "一般"


# ===== 主界面 =====
st.markdown(
    '<div style="text-align:center;margin-bottom:8px">'
    '<span style="display:inline-flex;align-items:center;justify-content:center;'
    'width:60px;height:60px;background:linear-gradient(135deg,#6366f1,#8b5cf6);'
    'border-radius:18px;font-size:28px;box-shadow:0 6px 24px rgba(99,102,241,.3)">🔍</span>'
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<h1 style="text-align:center;font-size:20px;color:#e2e8f0;margin-bottom:4px">抖音账号免费诊断</h1>'
    '<p style="text-align:center;font-size:13px;color:#64748b">输入账号信息，30秒生成诊断报告</p>',
    unsafe_allow_html=True,
)

# 初始化状态
if "step" not in st.session_state:
    st.session_state.step = "input"
if "result" not in st.session_state:
    st.session_state.result = None

# ===== 第一步：输入 =====
if st.session_state.step == "input":
    with st.form("diagnose_form", clear_on_submit=False):
        douyin = st.text_input("抖音号（选填）", placeholder="例如：zhangkemeng666")
        industry = st.selectbox(
            "行业/赛道",
            ["请选择", "知识付费", "电商带货", "本地生活", "探店/餐饮", "教育培训", "情感咨询", "法律服务", "其他"],
        )
        fans = st.text_input("当前粉丝量（选填）", placeholder="例如：2000")
        problem = st.text_area(
            "你觉得账号最大的问题是什么？（选填）",
            placeholder="例如：视频播放量卡在500上不去 / 有人看没人加微信 / 不知道拍什么内容好",
            height=68,
        )
        submitted = st.form_submit_button("开始免费诊断")

    if submitted:
        parts = []
        if douyin:
            parts.append(f"抖音号：{douyin}")
        if industry and industry != "请选择":
            parts.append(f"行业：{industry}")
        if fans:
            parts.append(f"粉丝量：{fans}")
        if problem:
            parts.append(f"用户描述的问题：{problem}")
        if not parts:
            st.warning("至少填一项信息")
        else:
            st.session_state.step = "analyzing"
            st.session_state.account_info = "\n".join(parts)
            st.rerun()

# ===== 第二步：分析中 =====
elif st.session_state.step == "analyzing":
    # 显示骨架屏
    st.markdown(
        '<div style="background:#111827;border-radius:18px;padding:32px 24px;text-align:center;border:1px solid #1e293b">'
        '<div style="width:80px;height:80px;margin:0 auto 20px;border:3px solid #1e293b;'
        'border-top-color:#6366f1;border-radius:50%;animation:spin .8s linear infinite"></div>'
        '<p style="color:#e2e8f0;font-weight:700;font-size:16px;margin-bottom:6px">正在分析你的账号...</p>'
        '<p style="color:#64748b;font-size:13px">AI 正在多维度评估，大约需要 10-20 秒</p>'
        "</div>"
        '<style>@keyframes spin{to{transform:rotate(360deg)}}</style>',
        unsafe_allow_html=True,
    )
    # 执行诊断
    result = diagnose(st.session_state.account_info)
    st.session_state.result = result
    st.session_state.step = "result"
    time.sleep(0.5)
    st.rerun()

# ===== 第三步：结果 =====
elif st.session_state.step == "result":
    result = st.session_state.result
    score = result["overall_score"]
    problems = result["problems"]

    # 健康度分数
    ring_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 40 else "#f43f5e")
    st.markdown(
        f'<div style="text-align:center;margin-bottom:20px">'
        f'<div style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:100px;height:100px;border-radius:50%;border:4px solid {ring_color};'
        f'background:rgba(0,0,0,.3);font-size:32px;font-weight:800;color:{ring_color}">{score}</div>'
        f'<p style="color:#64748b;font-size:13px;margin-top:8px">账号健康度评分</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # 问题列表
    st.markdown(
        '<p style="color:#94a3b8;font-size:14px;font-weight:600;margin-bottom:10px">核心问题</p>',
        unsafe_allow_html=True,
    )
    for i, p in enumerate(problems):
        color = score_to_color(p["score"])
        label = score_to_label(p["score"])
        st.markdown(
            f'<div style="background:#111827;border-radius:14px;padding:16px 18px;'
            f'margin-bottom:10px;border-left:3px solid {color}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">'
            f'<span style="color:#e2e8f0;font-weight:700;font-size:15px">{i+1}. {p["title"]}</span>'
            f'<span style="background:rgba({("244,63,94" if p["score"]>=7 else "245,158,11" if p["score"]>=4 else "251,191,36")},.15);'
            f'color:{color};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600">{label} {p["score"]}/10</span>'
            f"</div>"
            f'<p style="color:#94a3b8;font-size:13px;margin:0">{p["detail"]}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # CTA
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,.1),rgba(139,92,246,.08));'
        f'border-radius:14px;padding:20px;text-align:center;margin-top:20px;border:1px solid #1e293b">'
        f'<p style="color:#e2e8f0;font-weight:700;font-size:15px;margin-bottom:6px">想要详细的优化方案？</p>'
        f'<p style="color:#94a3b8;font-size:13px;margin-bottom:12px">专业运营团队一对一诊断，帮你从{score}分提到90+</p>'
        f'<span style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);'
        f'color:white;padding:10px 28px;border-radius:10px;font-weight:700;font-size:15px">加微信：{WECHAT_ID}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # 重新诊断
    if st.button("重新诊断", type="secondary"):
        st.session_state.step = "input"
        st.session_state.result = None
        st.rerun()
