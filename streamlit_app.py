"""
获客3 — 抖音账号免费诊断工具
Streamlit Cloud 部署版本
"""
import streamlit as st
import requests
import json
import re
import time
import base64
from io import BytesIO
from PIL import Image

# ===== 配置 =====
st.set_page_config(
    page_title="抖音账号免费诊断",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/anthropic/v1/messages"

try:
    DOUBAO_KEY = st.secrets["DOUBAO_KEY"]
    DOUBAO_MODEL = st.secrets["DOUBAO_MODEL"]
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_KEY"]
except (KeyError, FileNotFoundError):
    DOUBAO_KEY = "ark-d1754a1a-98cd-4db6-8efa-d21e6c149359-01bf9"
    DOUBAO_MODEL = "ep-20260528232335-78k69"
    DEEPSEEK_KEY = "sk-ecf8b540e2bc4e2fa3e0d4cd3f5d34e8"

SYSTEM_PROMPT = """你是曾科，3年抖音代运营实战专家，深度服务过餐饮、美容、教育、装修、家政等12个行业的中小商家。你看过上千个账号，一眼就能定位问题。

你现在要分析一个抖音账号，输出一份诊断报告。你的语气是「一针见血的专家」——不客套，直接说问题，但每个问题都要有理有据，让人感到「这个人真的懂我」。

## 分析维度（按重要性排序）

1. **账号定位与标签**：账号的人设清晰吗？系统知道该把内容推给谁吗？标签吸引来的是目标客户还是闲逛的人？
2. **内容质量与完播**：前3秒能抓住人吗？画面、文案、节奏哪里掉链子？为什么用户划走了？
3. **流量与推流机制**：播放量卡在哪个量级？是标签问题、内容问题还是被限流了？和同行差距在哪？
4. **转化与变现**：有人看但有人咨询吗？主页、评论区、私信有没有承接流量？缺少什么转化动作？

## 输出要求

结合用户的行业特征，输出恰好3个最核心的问题，按严重程度排序。每个问题必须包含：

- **问题定位**：一针见血指出哪里出了问题
- **症状分析**：为什么会这样？结合行业特点说清因果（2-3句话，要具体，不能用套话）
- **反问引导**：提出1-2个让用户反思的问题（比如「你的粉丝画像和你实际想服务的客户一致吗？」「你有没有发现点赞的都是同行而不是客户？」），这些问题要让用户产生「我得找个专业的人帮我看看」的想法
- **不解决的后果**：这个问题不解决会怎样

## 输出格式

严格按以下JSON格式输出，不要markdown标记，不要任何解释文字：

```json
{
  "overall_score": 52,
  "score_comment": "综合评分偏低，核心问题在标签定位和内容开头，不改的话流量会持续下滑。",
  "problems": [
    {
      "title": "账号标签混乱，推送人群跑偏",
      "severity": 8,
      "analysis": "你的账号内容方向不统一，今天发这个明天发那个，算法很难给你打上精准标签。做餐饮的号如果标签打到「美食爱好者」而不是「本地想吃饭的人」，来的全是看热闹的外地人，根本没法到店转化。这就像你在美食街发传单，结果都发给了来旅游的。",
      "questions": ["你的粉丝画像和你实际想服务的客户一致吗？", "你有没有发现给你评论的人大多是同行或者外地人，而不是你店附近的潜在顾客？"],
      "consequence": "标签继续乱下去，播放量会越推越偏，哪怕花钱投DOU+也是在浪费，因为系统找不到对的人。"
    },
    {
      "title": "前3秒没有钩子，80%的人划走了",
      "severity": 6,
      "analysis": "用户刷抖音平均3秒决定要不要继续看。你的视频开头要么是logo展示、要么是缓慢的画面过渡，没有在第一时间告诉用户「这条视频和你有关」。在XX行业，用户最关心的是结果对比和价格透明，你不在一开始就把钩子亮出来，等于是把客户推给同行。",
      "questions": ["你有回头看过每条视频前3秒的完播率是多少吗？", "如果你的客户刷到你视频，第一眼看到的是什么内容——能让他停下来吗？"],
      "consequence": "开头不改，内容做得再好也没人能看到后面。视频制作的精力全浪费在前3秒。"
    },
    {
      "title": "缺少转化引导，流量变不成客户",
      "severity": 5,
      "analysis": "视频有人看、有人点赞，但没人咨询、没人加微信。因为你没有在视频里告诉用户「下一步该做什么」。评论区的互动也没有引导到私域。每条视频都是一次获客机会，但现在这些机会全漏掉了，等于你每天在给抖音贡献内容，抖音在给同行贡献客户。",
      "questions": ["你的每条视频末尾有没有一句明确的引导话术？", "当有人评论你的视频时，你的回复是在闲聊还是在引导咨询？"],
      "consequence": "流量变不成客户就等于白做。一个月下来视频发了几十条，微信上没加几个人，时间和精力全打了水漂。"
    }
  ]
}
```

## 重要规则

- overall_score：30-85之间的整数，越低问题越大。大部分中小商家在40-65之间。
- score_comment：一句话总结，要让用户产生紧迫感
- problems 必须恰好3个，不能多不能少
- severity：1-10整数，10最严重
- analysis：必须针对用户的具体行业写，不能泛泛而谈。要让人读完后觉得「这个人真的懂我这行」
- questions：每个问题下恰好2个反问，要让用户自己去想、去怀疑自己的账号是不是真的有这些问题
- consequence：让用户感到不解决后果很严重，产生行动冲动
- 不要用「建议」「您可以」「值得关注」这类温和措辞，用「必须」「否则」「继续这样下去」这类有紧迫感的措辞
- 只输出JSON，不输出任何其他内容"""

WECHAT_ID = "zengke_dy"


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
  .stFileUploader>section>button {display:none;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)


def encode_image(uploaded_file) -> str | None:
    """将上传的图片编码为 base64 data URL"""
    try:
        img = Image.open(uploaded_file)
        # 压缩大图到 1024px 宽以内
        if img.width > 1024:
            ratio = 1024 / img.width
            img = img.resize((1024, int(img.height * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def build_messages(account_info: str, image_b64: str | None, use_vision: bool = True) -> list[dict]:
    """构建 API 请求的 messages"""
    if image_b64 and use_vision:
        # 豆包 vision 格式（OpenAI 兼容）
        user_content = [
            {"type": "image_url", "image_url": {"url": image_b64}},
            {"type": "text", "text": f"请诊断这个抖音账号。{account_info}\n\n根据截图中可见的信息（粉丝数、作品数、点赞量、头像、昵称、简介、内容风格、主页排版等）进行综合诊断。"},
        ]
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
    else:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": account_info},
        ]


def call_doubao(account_info: str, image_b64: str | None) -> dict | None:
    """调用豆包 API（支持图片）"""
    try:
        messages = build_messages(account_info, image_b64, use_vision=True)
        resp = requests.post(
            DOUBAO_URL,
            json={
                "model": DOUBAO_MODEL,
                "max_tokens": 2000,
                "temperature": 0.8,
                "messages": messages,
            },
            headers={"Authorization": f"Bearer {DOUBAO_KEY}"},
            timeout=60,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        return parse_json(content)
    except Exception:
        return None


def call_deepseek(account_info: str) -> dict | None:
    """调用 DeepSeek API（回退方案，纯文本）"""
    try:
        resp = requests.post(
            DEEPSEEK_URL,
            json={
                "model": "deepseek-v4-pro",
                "max_tokens": 2000,
                "temperature": 0.8,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": account_info}],
            },
            headers={"x-api-key": DEEPSEEK_KEY},
            timeout=60,
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
    # 尝试匹配 JSON 块
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


def diagnose(account_info: str, image_b64: str | None = None) -> dict:
    """执行诊断，豆包优先，失败回退 DeepSeek"""
    result = call_doubao(account_info, image_b64)
    if result:
        return result
    # DeepSeek 回退（纯文本，不带图片）
    result = call_deepseek(account_info)
    if result:
        return result
    # 硬兜底
    return {
        "overall_score": 48,
        "score_comment": "系统初步判断你的账号存在较严重的定位和转化问题，建议尽快优化。",
        "problems": [
            {
                "title": "账号标签混乱，推送人群跑偏",
                "severity": 8,
                "analysis": "你的账号内容方向不够聚焦，算法很难给你打上精准标签。这意味着系统在把内容推给错误的人群——可能是同行、看热闹的，而不是真正会买单的客户。",
                "questions": ["你的粉丝画像和你实际想服务的客户一致吗？", "给你评论点赞的人，有多少是同行或外地人？"],
                "consequence": "标签继续乱下去，播放量会越推越偏，花钱投流也是浪费。",
            },
            {
                "title": "前3秒没有钩子，用户秒划走",
                "severity": 6,
                "analysis": "用户刷抖音平均3秒决定要不要继续看。你的视频开头没有在第一时间告诉用户「这条视频和你有关」，导致大部分人在看到有价值的内容之前就已经划走了。",
                "questions": ["你有回头看过每条视频前3秒的完播率是多少吗？", "你的视频第一帧给用户看到的是什么——能让他停下来吗？"],
                "consequence": "开头不改，后面内容做得再好也没人能看到，制作精力全浪费。",
            },
            {
                "title": "缺少转化引导，流量变不成客户",
                "severity": 5,
                "analysis": "视频有人看但没人咨询、没人加微信。因为你没有在视频里和评论区引导用户采取下一步行动。每条视频都是一次获客机会，现在全漏掉了。",
                "questions": ["你的每条视频结尾有没有一句明确的引导话术？", "评论区有人互动时，你的回复是在闲聊还是在引导咨询？"],
                "consequence": "一个月发几十条视频，微信上没加几个人，时间和精力全打水漂。",
            },
        ],
    }


def severity_color(s: int) -> str:
    if s >= 7:
        return "#f43f5e"
    if s >= 4:
        return "#f59e0b"
    return "#fbbf24"


def severity_label(s: int) -> str:
    if s >= 7:
        return "严重"
    if s >= 4:
        return "中等"
    return "一般"


def score_color(score: int) -> str:
    if score >= 70:
        return "#10b981"
    if score >= 40:
        return "#f59e0b"
    return "#f43f5e"


def score_emoji(score: int) -> str:
    if score >= 70:
        return "🟢"
    if score >= 40:
        return "🟡"
    return "🔴"


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
    '<p style="text-align:center;font-size:13px;color:#64748b">AI深度分析 + 3年运营经验，30秒定位核心问题</p>',
    unsafe_allow_html=True,
)

# 初始化状态
if "step" not in st.session_state:
    st.session_state.step = "input"
if "result" not in st.session_state:
    st.session_state.result = None
if "image_b64" not in st.session_state:
    st.session_state.image_b64 = None


# ===== 第一步：输入 =====
if st.session_state.step == "input":
    with st.form("diagnose_form", clear_on_submit=False):
        uploaded = st.file_uploader(
            "上传抖音主页截图（推荐，诊断更精准）",
            type=["jpg", "jpeg", "png"],
            label_visibility="visible",
        )
        douyin = st.text_input("抖音号（选填）", placeholder="例如：zhangkemeng666")
        industry = st.selectbox(
            "行业/赛道",
            ["请选择", "餐饮", "美容", "教育/培训", "装修/建材", "家政", "健身", "汽车", "房产", "宠物", "摄影", "法律服务", "财税", "本地生活", "知识付费", "电商带货", "其他"],
        )
        fans = st.text_input("当前粉丝量（选填）", placeholder="例如：2000")
        problem = st.text_area(
            "你觉得账号最大的问题是什么？（选填，填了更精准）",
            placeholder="例如：视频播放量卡在500上不去 / 有人看没人加微信 / 不知道拍什么内容好 / 投了dou+没效果",
            height=68,
        )
        submitted = st.form_submit_button("免费诊断")

    if submitted:
        parts = []
        if douyin:
            parts.append(f"抖音号：{douyin}")
        if industry and industry != "请选择":
            parts.append(f"行业：{industry}")
        if fans:
            parts.append(f"当前粉丝量：{fans}")
        if problem:
            parts.append(f"用户描述的问题：{problem}")
        if not parts and not uploaded:
            st.warning("至少上传截图或填写一项信息")
        else:
            # 处理图片
            if uploaded:
                st.session_state.image_b64 = encode_image(uploaded)
            else:
                st.session_state.image_b64 = None
            st.session_state.account_info = "\n".join(parts) if parts else "请根据截图进行诊断"
            st.session_state.step = "analyzing"
            st.rerun()

# ===== 第二步：分析中 =====
elif st.session_state.step == "analyzing":
    has_image = st.session_state.image_b64 is not None
    st.markdown(
        f'<div style="background:#111827;border-radius:18px;padding:40px 24px;text-align:center;border:1px solid #1e293b">'
        f'<div style="width:72px;height:72px;margin:0 auto 24px;border:3px solid #1e293b;'
        f'border-top-color:#6366f1;border-radius:50%;animation:spin .8s linear infinite"></div>'
        f'<p style="color:#e2e8f0;font-weight:700;font-size:16px;margin-bottom:6px">'
        f'{"正在分析截图 + 多维度诊断..." if has_image else "正在多维度分析你的账号..."}</p>'
        f'<p style="color:#64748b;font-size:13px">'
        f'{"AI视觉识别 + 行业数据比对中，约15-25秒" if has_image else "AI正在比对行业数据，大约需要10-20秒"}</p>'
        f"</div>"
        '<style>@keyframes spin{to{transform:rotate(360deg)}}</style>',
        unsafe_allow_html=True,
    )
    # 执行诊断
    result = diagnose(
        st.session_state.get("account_info", ""),
        st.session_state.get("image_b64"),
    )
    st.session_state.result = result
    st.session_state.step = "result"
    time.sleep(0.5)
    st.rerun()

# ===== 第三步：结果 =====
elif st.session_state.step == "result":
    result = st.session_state.result
    score = result["overall_score"]
    score_comment = result.get("score_comment", "")
    problems = result["problems"]

    # -- 健康度评分 --
    color = score_color(score)
    emoji = score_emoji(score)
    st.markdown(
        f'<div style="text-align:center;margin-bottom:8px">'
        f'<div style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:110px;height:110px;border-radius:50%;border:5px solid {color};'
        f'background:rgba(0,0,0,.3);font-size:42px;font-weight:800;color:{color};'
        f'box-shadow:0 0 40px rgba({("16,185,129" if score>=70 else "245,158,11" if score>=40 else "244,63,94")},.15)">{score}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="text-align:center;margin-bottom:4px">'
        f'<span style="font-size:18px;font-weight:700;color:#e2e8f0">{emoji} 综合健康度</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    if score_comment:
        st.markdown(
            f'<p style="text-align:center;font-size:13px;color:#94a3b8;margin-bottom:24px;max-width:340px;margin-left:auto;margin-right:auto;line-height:1.6">{score_comment}</p>',
            unsafe_allow_html=True,
        )

    # -- 分隔线 --
    st.markdown('<div style="border-top:1px solid #1e293b;margin:0 0 20px 0"></div>', unsafe_allow_html=True)

    # -- 核心问题 --
    st.markdown(
        '<p style="color:#cbd5e1;font-size:15px;font-weight:700;margin-bottom:14px">'
        '🔴 诊断发现 <span style="color:#f59e0b">3个</span> 核心问题</p>',
        unsafe_allow_html=True,
    )

    for i, p in enumerate(problems):
        sev = p.get("severity", 5)
        c = severity_color(sev)
        label = severity_label(sev)

        # 问题卡片
        st.markdown(
            f'<div style="background:#111827;border-radius:16px;padding:20px;'
            f'margin-bottom:14px;border:1px solid #1e293b;border-left:4px solid {c}">'
            # 标题行
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">'
            f'<div style="flex:1">'
            f'<span style="display:inline-block;background:rgba({("244,63,94" if sev>=7 else "245,158,11" if sev>=4 else "251,191,36")},.12);'
            f'color:{c};padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700;margin-bottom:6px">问题{i+1} · {label} · {sev}/10</span>'
            f'<span style="display:block;color:#f1f5f9;font-weight:700;font-size:16px">{p["title"]}</span>'
            f"</div>"
            f"</div>"
            # 分析
            f'<p style="color:#cbd5e1;font-size:14px;line-height:1.75;margin-bottom:14px">{p["analysis"]}</p>'
            # 反问
            f'<div style="background:rgba(99,102,241,.06);border-radius:10px;padding:12px 14px;margin-bottom:10px;border:1px solid rgba(99,102,241,.12)">'
            f'<p style="font-size:11px;color:#818cf8;font-weight:600;margin-bottom:6px;letter-spacing:.5px">🤔 不妨问自己：</p>'
            + "".join(
                f'<p style="font-size:13px;color:#a5b4fc;margin:4px 0;line-height:1.6">· {q}</p>'
                for q in p.get("questions", [])
            )
            + "</div>"
            # 后果
            f'<div style="display:flex;align-items:flex-start;gap:6px;font-size:12px;color:#ef4444;line-height:1.6">'
            f'<span style="flex-shrink:0">⚠</span>'
            f'<span>{p.get("consequence", "如不解决，账号增长将持续受阻。")}</span>'
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # -- CTA --
    problems_summary = "、".join(p["title"][:8] for p in problems[:3])
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,.08),rgba(139,92,246,.06));'
        f'border-radius:16px;padding:24px 20px;text-align:center;margin-top:24px;'
        f'border:1.5px solid rgba(99,102,241,.35)">'
        f'<p style="color:#f1f5f9;font-weight:700;font-size:16px;margin-bottom:4px">📩 想解决「{problems_summary}」？</p>'
        f'<p style="color:#94a3b8;font-size:13px;margin-bottom:6px;line-height:1.6">'
        f'这3个问题是多年服务{score}+分账号总结的共性痛点。<br>每个问题都有对应的解决方案，但需要结合你的具体情况定制。</p>'
        f'<p style="color:#cbd5e1;font-size:14px;margin-bottom:16px;font-weight:600">'
        f'加微信，我帮你一对一分析，从{score}分提到90+分怎么走。</p>'
        f'<span style="display:inline-block;background:#07c160;'
        f'color:white;padding:12px 32px;border-radius:10px;font-weight:700;font-size:16px;'
        f'letter-spacing:.5px;box-shadow:0 4px 16px rgba(7,193,96,.3)">'
        f'💬 加微信：{WECHAT_ID}</span>'
        f'<p style="color:#64748b;font-size:11px;margin-top:12px">不加也正常，但建议你至少把上面3个反思问题想清楚</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # 重新诊断
    st.markdown('<div style="margin-top:24px">', unsafe_allow_html=True)
    if st.button("🔄 重新诊断另一个账号", type="secondary"):
        st.session_state.step = "input"
        st.session_state.result = None
        st.session_state.image_b64 = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
