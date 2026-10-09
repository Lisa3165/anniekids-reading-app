# Anniekids English Reading Lesson Studio

面向中国小学高年级英语阅读教师的 Streamlit 备课应用。

## 安装与运行

需要 Python 3.10+。

```bash
cd /workspace/Anniekids-teaching-lab  # 本地请进入实际项目目录
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

本地浏览器打开 `http://localhost:8501`。云环境使用平台端口转发功能访问 8501（如平台提供）；也可将仓库下载到本地运行。首次启动无需 API Key，即可提取和查看文本。

## AI 配置

启动前设置环境变量（Windows PowerShell 使用 `$env:LESSON_API_KEY="..."`）：

```bash
export LESSON_API_KEY="你的密钥"
export LESSON_MODEL="gpt-4o-mini"  # 可选，默认值如上
# export LESSON_API_BASE_URL="https://你的兼容服务/v1"  # 可选
streamlit run app.py
```

也可使用 `OPENAI_API_KEY`。读取顺序为：环境变量 `LESSON_API_KEY` → 环境变量 `OPENAI_API_KEY` → Streamlit Secrets `LESSON_API_KEY` → Streamlit Secrets `OPENAI_API_KEY`；空白值会跳过。采用 OpenAI Chat Completions JSON 模式；兼容服务和模型须支持 JSON object 输出及相应输出长度。密钥从环境变量或 Streamlit Secrets 读取，不写入代码、不提交 Git。不配置密钥时，界面明确说明无法生成 AI 分析，绝不显示模拟分析。默认外部服务为 OpenAI；需要访问 api.openai.com。自定义服务须允许其实际域名。费用与可用模型由账号决定。

### Streamlit Community Cloud 密钥设置

在应用 **Settings → Secrets** 中填写以下 TOML（示例仅为占位，不是真实密钥）：

```toml
LESSON_API_KEY = "你的密钥"
```

保存后按平台提示重启应用。不要将真实密钥写进仓库文件；本地如使用 `.streamlit/secrets.toml`，该文件已被 `.gitignore` 排除。未配置密钥或不存在 Secrets 文件时，网站仍可启动，允许上传与查看文本，AI 生成按钮禁用并说明原因。页面只显示是否检测到配置，不展示密钥内容。`LESSON_MODEL` 和 `LESSON_API_BASE_URL` 仍从环境变量读取。

公开应用目前没有登录和额度限制；部署为公众可访问服务前，请考虑访问控制及模型费用。此项兼容性修改不等于已完成部署。

## 使用流程

1. 上传 PDF、DOCX 或 TXT，核对标题、全文和英文单词数。
2. 选择 CEFR A2 或 B1。自动识别章节标题；必要时填写原文中唯一出现的完整章节标题，按原文顺序排列。章节前文字保留为单独范围；未识别章节时仅处理全文。
3. 勾选文本发送授权并生成：What–Why–How 分析、每章 Big Question、至少六个问题（每个维度至少两个）、答案及引文、阶段任务和综合写作任务。
4. 核对 AI 草稿后下载 Word。导出包含标题、层级和可编辑问题表格。

教师界面、分析与备课说明为中文；学生问题、参考答案、Big Question 和输出任务为英文。A2 强调具体理解和句型支架，综合写作 60–80 词；B1 加入解释、比较与段落支架，综合写作 100–120 词。

## 证据与第一版限制

- 不提供 OCR：PDF 任意页面无法提取文字时拒绝分析，并提示先 OCR；加密、损坏、空文件给出错误提示。PDF 提取顺序与准确性仍需人工核对。
- TXT 支持 UTF-8 与 GB18030；DOCX 支持正文段落和表格，不提取图片、页眉、页脚。
- 文件限 10 MB；AI 每次限 45,000 字符、12 个章节。长书请拆分上传，不会静默截断。
- 模型以全部选定文本为依据，返回结构化 JSON；系统拒绝缺字段、章节变更、缺维度问题以及不在对应原文中的引文。
- 引文匹配只能证明引用存在，不能证明解释正确。写作目的等推论要求模型标明推测；教师须审核事实、推论、语言等级、英文输出和任务递进。不承诺 AI 永不产生错误。
- 点击生成才发送文本到配置的 AI 服务。不做持久化上传存储；会话中的提取文本及结果会保存在进程内存中。无用户账号和数据库。

## 基本测试

```bash
python -m unittest discover -s tests -v
```

测试不需要 API Key，不访问付费模型，覆盖文件提取、空/损坏输入、PDF 无文字提示、章节识别、引文校验、API 缺失提示和 DOCX 导出。真实模型端到端生成需自行配置有效密钥后验证。
