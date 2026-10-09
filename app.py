import hashlib

import streamlit as st

from studio import StudioError, export_docx, extract_material, generate_lesson, get_api_key, split_chapters

st.set_page_config(page_title='Anniekids 阅读备课工作室', page_icon='📚', layout='wide')
st.title('📚 Anniekids English Reading Lesson Studio')
st.caption('面向中国小学高年级英语阅读教师 · 从原文到问题链与综合写作')
with st.sidebar:
    st.header('备课设置')
    level = st.selectbox('学生英语等级', ['A2', 'B1'])
    st.write('A2：具体理解、句型支架、60–80 词综合写作。' if level == 'A2' else 'B1：解释与比较、段落支架、100–120 词综合写作。')
    configured = bool(get_api_key())
    st.success('已检测到 API Key 配置') if configured else st.info('未配置 API Key：可提取文本，暂不能生成分析。')
    with st.expander('AI 配置说明'):
        st.code('export LESSON_API_KEY="你的密钥"\nexport LESSON_MODEL="gpt-4o-mini"\nstreamlit run app.py', language='bash')
        st.write('Streamlit Community Cloud：在 Settings → Secrets 中设置 LESSON_API_KEY。也支持 OPENAI_API_KEY。优先读取环境变量，其次读取 Streamlit Secrets；请勿提交密钥到 Git。')
        st.write('兼容服务可通过环境变量设置 LESSON_API_BASE_URL（完整 API 基础地址）。')
        st.write('点击生成后，提取文本会发送至所配置的 AI 服务；请仅上传有权使用的材料。')
st.header('1. 上传阅读材料')
upload = st.file_uploader('选择 PDF、DOCX 或 TXT（最多 10 MB）', type=['pdf', 'docx', 'txt'])
if upload is None:
    st.info('上传英文阅读材料即可开始。扫描 PDF 请先完成 OCR，本应用不猜测缺失文字。')
    st.stop()
if upload.size > 10 * 1024 * 1024:
    st.error('文件超过 10 MB，请拆分后上传。')
    st.stop()
data = upload.getvalue()
try:
    material = extract_material(upload.name, data)
except StudioError as exc:
    st.error(str(exc))
    st.stop()
title = st.text_input('书名 / 材料标题（请核对）', material['title'])
material['title'] = title.strip() or material['title']
st.metric('英文单词数', material['words'])
with st.expander('查看提取的全文', expanded=True):
    st.text_area('文本内容（只读）', material['text'], height=280, disabled=True)
chapters = split_chapters(material['text'])
st.header('2. 确认章节范围')
st.caption('自动识别独立行 Chapter 1 / Chapter One / 第一章等标题。识别不准确时，可手工指定每章起始行；未提供标题的文本按全文处理。不会凭空生成章节。')
manual = st.text_area('可选：每行填写一个章节标题，须与原文中的完整独立行完全一致，并按原文顺序填写', height=100)
if manual.strip():
    titles = [line.strip() for line in manual.splitlines() if line.strip()]
    lines = material['text'].splitlines(keepends=True)
    offsets, offset = {}, 0
    for line in lines:
        offsets.setdefault(line.strip(), []).append(offset)
        offset += len(line)
    if len(set(titles)) != len(titles) or any(len(offsets.get(t, [])) != 1 for t in titles):
        st.error('每个章节标题必须在原文中唯一出现，且不能重复。')
        st.stop()
    positions = [offsets[t][0] for t in titles]
    if positions != sorted(positions):
        st.error('章节标题顺序与原文不一致。')
        st.stop()
    chapters = []
    if material['text'][:positions[0]].strip():
        chapters.append({'title': '章节前文字', 'text': material['text'][:positions[0]].strip()})
    for i, name in enumerate(titles):
        end = positions[i+1] if i+1 < len(positions) else len(material['text'])
        chapters.append({'title': name, 'text': material['text'][positions[i]:end].strip()})
for chapter in chapters:
    st.write('• ' + chapter['title'])
identity = hashlib.sha256((data.hex() + material['title'] + level + manual).encode()).hexdigest()
if st.session_state.get('lesson_identity') != identity:
    st.session_state.pop('lesson', None)
    st.session_state['lesson_identity'] = identity
st.header('3. 生成备课草稿')
st.caption('所有问题与任务使用英文，教师分析与说明使用中文。每次生成最多 45,000 字符、12 个章节。')
consent = st.checkbox('我同意将当前文本发送至所配置的 AI 服务进行分析。')
if st.button('生成文本分析、章节问题链与输出任务', type='primary', disabled=not configured or not consent):
    try:
        with st.spinner('正在分析原文并核对引文，请稍候…'):
            lesson = generate_lesson(material, chapters, level)
        st.session_state['lesson'] = lesson
    except StudioError as exc:
        st.error(str(exc))
lesson = st.session_state.get('lesson')
if lesson:
    st.warning('这是 AI 辅助备课草稿。系统核对引文是否存在，但不能保证推论与答案正确；请结合原文审核后使用。')
    tabs = st.tabs(['What–Why–How', '章节问题链与任务', '综合写作与导出'])
    with tabs[0]:
        for dimension in ('What', 'Why', 'How'):
            st.subheader(dimension)
            for point in lesson['analysis'][dimension]:
                st.write(point['point'])
                st.text('原文依据：' + point['evidence'])
    with tabs[1]:
        for chapter in lesson['chapters']:
            with st.expander(chapter['title'], expanded=True):
                st.subheader('Big Question: ' + chapter['big_question'])
                for i, question in enumerate(chapter['questions'], 1):
                    st.write(f"{i}. [{question['dimension']}] {question['question']}")
                    st.write('Reference answer: ' + question['answer'])
                    st.text('Text evidence: ' + question['evidence'])
                st.subheader('Student output task')
                st.write(chapter['task'])
                st.write('教师说明：' + chapter['teacher_notes'])
    with tabs[2]:
        st.subheader('Final writing task')
        st.write(lesson['final_task'])
        st.subheader('教师备课说明')
        st.write(lesson['teacher_notes'])
        st.download_button('下载可编辑 Word 备课文档', export_docx(material, lesson, level), file_name=f'Anniekids_Lesson_{level}.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
