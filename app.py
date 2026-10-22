import hashlib

import streamlit as st
from template_flow import analyze_book, make_framework, make_lessons, export_pack, document_bytes

from studio import StudioError, export_docx, extract_material, generate_lesson, get_api_key, split_chapters

st.set_page_config(page_title='Anniekids 阅读备课工作室', page_icon='📚', layout='wide')
st.title('📚 Anniekids English Reading Lesson Studio')
st.caption('面向中国小学高年级英语阅读教师 · 从原文到问题链与综合写作')
with st.sidebar:
    st.header('备课设置')
    level = st.selectbox('学生英语等级', ['A2', 'B1'])
    grade = st.text_input('年级', '六年级')
    lesson_count = st.number_input('课次数', 1, 30, 3)
    minutes = st.number_input('每次课分钟数', 20, 240, 80)
    words = st.text_input('最终写作词数范围', '120–150')
    st.caption('内置 Life Online 教学结构；主题、章节和活动根据新材料生成。')
    configured = bool(get_api_key())
    if configured:
        st.success('已检测到 API Key 配置')
    else:
        st.info('未配置 API Key：可提取文本，暂不能生成分析。')
    with st.expander('AI 配置说明'):
        st.code('export LESSON_API_KEY="你的密钥"\nexport LESSON_MODEL="gpt-4o-mini"\nstreamlit run app.py', language='bash')
        st.write('Streamlit Community Cloud：在 Settings → Secrets 中设置 LESSON_API_KEY。也支持 OPENAI_API_KEY。优先读取环境变量，其次读取 Streamlit Secrets；请勿提交密钥到 Git。')
        st.write('兼容服务可通过环境变量设置 LESSON_API_BASE_URL（完整 API 基础地址）。')
        st.write('点击生成后，提取文本会发送至所配置的 AI 服务；请仅上传有权使用的材料。')
st.header('1. 上传阅读材料')
upload = st.file_uploader('选择 PDF、DOCX 或 TXT（本地上传上限 2 GB）', type=['pdf', 'docx', 'txt'])
if upload is None:
    st.info('上传英文阅读材料即可开始。扫描 PDF 请先完成 OCR，本应用不猜测缺失文字。')
    st.stop()
data = upload.getvalue()
try:
    @st.cache_data(show_spinner=False, max_entries=2)
    def parse_file(name, content):
        return extract_material(name, content)
    with st.spinner('正在提取文档文字…'):
        material = parse_file(upload.name, data)
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
settings = {'grade':grade, 'level':level, 'lessons':int(lesson_count), 'minutes':int(minutes), 'words':words}
identity = hashlib.sha256(data).hexdigest() + str((material['title'], settings, manual))
if st.session_state.get('lesson_identity') != identity:
    for name in ('framework', 'pack', 'notes', 'framework_editor', 'pack_framework', 'analysis_checkpoint'):
        st.session_state.pop(name, None)
    st.session_state['lesson_identity'] = identity
st.header('3. 生成并确认教学框架')
st.caption('长文本按段分析后整合；文档越长，耗时和 AI 调用费用越高。分段不会被当成新增章节。')
consent = st.checkbox('我同意将当前文本发送至所配置的 AI 服务进行分析。')
if st.button('分析原文并生成教学框架', type='primary', disabled=not configured or not consent):
    bar = st.progress(0.0)
    try:
        notes = analyze_book(material, chapters, level, lambda value, label: bar.progress(value, text=label), st.session_state.setdefault('analysis_checkpoint', {}))
        bar.progress(0.95, text='整合全书教学框架…')
        framework = make_framework(material, notes, settings)
        st.session_state['notes'] = notes
        st.session_state['framework'] = framework
        st.session_state.pop('framework_editor', None)
        st.session_state.pop('pack', None)
        bar.progress(1.0, text='教学框架已生成，请核对后继续')
    except StudioError as exc:
        st.error(str(exc))
if st.session_state.get('framework'):
    framework = st.text_area('可编辑教学框架（核对章节安排、全书核心问题和最终任务）', value=st.session_state['framework'], height=450, key='framework_editor')
    st.download_button('下载教学框架 Word', document_bytes(material['title'], framework), file_name='教学框架.docx')
    with st.expander('查看逐段分析与已核对的原文依据'):
        st.json(st.session_state.get('notes', []))
    st.header('4. 生成教师教案、学生作业纸和参考答案')
    if st.button('按当前框架生成配套材料', disabled=not consent or not configured or not framework.strip()):
        st.session_state.pop('pack', None)
        bar = st.progress(0.0)
        try:
            st.session_state['pack'] = make_lessons(framework, settings, lambda v, t: bar.progress(v, text=t))
            st.session_state['pack_framework'] = framework
        except StudioError as exc:
            st.error(str(exc))
    pack = st.session_state.get('pack')
    if pack and st.session_state.get('pack_framework') != framework:
        st.info('教学框架已修改，请重新生成配套材料。')
        pack = None
    if pack:
        st.warning('请审核后使用：原文分析中的引文已核对；整合后的教案、作业纸和答案仍需人工核查。Word 为可编辑文字版，表格样式可能需要调整。')
        for item in pack:
            with st.expander(item['title'], expanded=True):
                tabs = st.tabs(['教师教案', '学生作业纸', '教师参考答案'])
                with tabs[0]:
                    for activity in item['activities']:
                        st.write(f"{activity['minutes']} 分钟：{activity['activity']}")
                    st.markdown(item['teacher'])
                with tabs[1]: st.markdown(item['worksheet'])
                with tabs[2]: st.markdown(item['answers'])
        st.download_button('下载全套 Word（ZIP）', export_pack(framework, pack), file_name='Anniekids教案与作业纸.zip', mime='application/zip')
