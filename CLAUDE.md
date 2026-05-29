# 获客3 — 诊断工具前置漏斗

> 在获客1（采集）和销售（转化）之间插入免费诊断工具，从「兜售模式」切换为「帮助模式」。

## 核心逻辑

```
获客1搜到客户 → 私信「免费帮你测账号健康度 → [链接]」
    → 客户点进去 → 输入抖音号 → 30秒出一份诊断报告
    → 报告指出3个问题（只给痛，不给药）
    → 「想拿详细方案？加微信」
    → 客户主动加微信 → 销售跟进
```

## 文件

| 文件 | 用途 |
|------|------|
| `diagnostic.html` | 诊断网页（输入→加载→报告，三屏单页） |
| `CLAUDE.md` | 本文档 |

## 技术栈

- 纯前端 HTML/CSS/JS，无需后端
- AI 诊断：DeepSeek API → 后续切豆包（火山引擎）
- 静态托管：Vercel / GitHub Pages / 随便放

## 部署

1. 把 `diagnostic.html` 上传到任意静态托管
2. 修改里面的 `WECHAT_ID` 为实际微信号
3. 拿到链接后，获客1私信发这个链接

## API 切换

已完成！当前默认豆包，自动回退 DeepSeek。

## 当前状态 (2026-05-28)

| 组件 | 状态 |
|------|------|
| diagnostic.html | ✅ 前端页面完成（深色UI/SVG评分/动画） |
| server.py | ✅ 后端服务，豆包+DeepSeek双通道 |
| streamlit_app.py | ✅ Streamlit版本，待部署 |
| requirements.txt | ✅ 已创建 |
| 豆包 API | ✅ ep-20260528232335-78k69 已测通 |
| DeepSeek API | ✅ 一直可用 |

## 部署进度

**下一步：部署到 Streamlit Cloud 给销售团队用**

需要做的事（按顺序）：
1. 在 GitHub 创建一个新仓库（叫 huoke3 或类似）
2. 把 streamlit_app.py + requirements.txt 推上去
3. 打开 https://streamlit.io/cloud 用 GitHub 登录
4. New app → 选仓库 → 填主文件路径 `获客3/streamlit_app.py`
5. 在 Advanced settings → Secrets 里填：
   ```
   DOUBAO_KEY = "ark-d1754a1a-98cd-4db6-8efa-d21e6c149359-01bf9"
   DOUBAO_MODEL = "ep-20260528232335-78k69"
   DEEPSEEK_KEY = "sk-ecf8b540e2bc4e2fa3e0d4cd3f5d34e8"
   ```
6. Deploy → 拿到公网 URL → 发给销售团队

最后把 `WECHAT_ID` 改成你的真实微信号（streamlit_app.py 第 61 行左右）。

## API 配置

| 配置 | 值 |
|------|-----|
| 豆包 URL | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` |
| 豆包 Key | `ark-d1754a1a-98cd-4db6-8efa-d21e6c149359-01bf9` |
| 豆包 Model | `ep-20260528232335-78k69` |
| DeepSeek URL | `https://api.deepseek.com/anthropic/v1/messages` |
| DeepSeek Key | `sk-ecf8b540e2bc4e2fa3e0d4cd3f5d34e8` |
