import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import zipfile

st.set_page_config(page_title="나만의 PDF 도구 프로", layout="wide")
st.title("📄 PDF 변환 / 병합 / 분할 도구 (v3.0)")

# 세션 상태 초기화
if 'pdf_list' not in st.session_state:
    st.session_state.pdf_list = []

tab1, tab2, tab3 = st.tabs(["🖼️ 이미지 -> PDF 변환", "🔗 PDF 파일 병합", "✂️ PDF 파일 분할"])

# --- (1) 이미지 -> PDF 변환 ---
with tab1:
    st.header("이미지를 PDF로 변환")
    uploaded_images = st.file_uploader("이미지 파일 선택", type=["jpg", "jpeg", "png", "bmp", "gif", "webp"], accept_multiple_files=True, key="img_up")
    if uploaded_images:
        if st.button("PDF 생성 및 다운로드", key="img_gen_btn"):
            pdf_bytes = io.BytesIO()
            images = [Image.open(img).convert("RGB") for img in uploaded_images]
            images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])
            st.download_button("📥 다운로드", data=pdf_bytes.getvalue(), file_name="images_converted.pdf")

# --- (2) PDF 파일 병합 ---
with tab2:
    st.header("여러 PDF 파일 병합")
    uploaded_pdfs = st.file_uploader("PDF 파일을 추가하거나 삭제하세요", type="pdf", accept_multiple_files=True, key="pdf_merge_up")

    if uploaded_pdfs:
        current_ids = set((f.name, f.size) for f in uploaded_pdfs)
        st.session_state.pdf_list = [f for f in st.session_state.pdf_list if (f.name, f.size) in current_ids]
        for pf in uploaded_pdfs:
            if not any(f.name == pf.name and f.size == pf.size for f in st.session_state.pdf_list):
                if len(st.session_state.pdf_list) < 10:
                    st.session_state.pdf_list.append(pf)
    else:
        st.session_state.pdf_list = []

    if st.session_state.pdf_list:
        st.subheader("🔄 병합 순서 조정")
        to_move_up, to_move_down = None, None
        for i, pdf_file in enumerate(st.session_state.pdf_list):
            col1, col2, col3 = st.columns([0.7, 0.1, 0.1])
            col1.write(f"**{i+1}. {pdf_file.name}**")
            if col2.button("↑", key=f"up_{i}"): to_move_up = i
            if col3.button("↓", key=f"down_{i}"): to_move_down = i

        if to_move_up is not None and to_move_up > 0:
            st.session_state.pdf_list[to_move_up], st.session_state.pdf_list[to_move_up-1] = st.session_state.pdf_list[to_move_up-1], st.session_state.pdf_list[to_move_up]
            st.rerun()
        if to_move_down is not None and to_move_down < len(st.session_state.pdf_list)-1:
            st.session_state.pdf_list[to_move_down], st.session_state.pdf_list[to_move_down+1] = st.session_state.pdf_list[to_move_down+1], st.session_state.pdf_list[to_move_down]
            st.rerun()

        st.divider()
        pdf_configs = []
        cols = st.columns(2)
        for i, pdf_file in enumerate(st.session_state.pdf_list):
            with cols[i % 2]:
                with st.expander(f"⚙️ {pdf_file.name} 설정", expanded=False):
                    reader = PdfReader(pdf_file)
                    mode = st.radio(f"범위", ["전체", "일부"], key=f"m_{i}", horizontal=True)
                    page_selection = st.text_input("페이지 (예: 1, 3-5)", key=f"p_{i}") if mode == "일부" else ""
                    pdf_configs.append({"reader": reader, "mode": mode, "selection": page_selection})

        if st.button("🔥 PDF 병합 실행", use_container_width=True, type="primary"):
            writer = PdfWriter()
            try:
                for config in pdf_configs:
                    reader = config["reader"]
                    if config["mode"] == "전체":
                        for page in reader.pages: writer.add_page(page)
                    else:
                        for part in config["selection"].replace(" ", "").split(","):
                            if "-" in part:
                                start, end = map(int, part.split("-"))
                                for p in range(start-1, end): writer.add_page(reader.pages[p])
                            else: writer.add_page(reader.pages[int(part)-1])
                output = io.BytesIO()
                writer.write(output)
                st.success("✅ 병합 완료!")
                st.download_button("📥 병합된 PDF 다운로드", data=output.getvalue(), file_name="merged.pdf")
            except Exception as e:
                st.error(f"오류: {e}")

# --- (3) PDF 파일 분할 (신규 기능) ---
with tab3:
    st.header("PDF 파일 분할")
    split_file = st.file_uploader("분할할 PDF 파일을 선택하세요", type="pdf", key="pdf_split_up")
    
    if split_file:
        reader = PdfReader(split_file)
        total_pages = len(reader.pages)
        st.info(f"선택된 파일: {split_file.name} (총 {total_pages} 페이지)")
        
        split_mode = st.radio(
            "분할 방식 선택", 
            ["모두 한 장씩 분할", "사용자 지정 범위로 분할"], 
            help="한 장씩 분할: 모든 페이지를 각각의 파일로 만듭니다.\n범위 분할: 1, 2-3 같이 입력하여 묶음으로 분할합니다."
        )
        
        custom_range = ""
        if split_mode == "사용자 지정 범위로 분할":
            custom_range = st.text_input(
                "분할할 범위를 입력하세요 (콤마로 구분)", 
                placeholder="예: 1, 2-3, 4-8, 9, 10",
                help="예를 들어 '1, 2-3'을 입력하면 1페이지 파일 하나, 2~3페이지 파일 하나가 만들어집니다."
            )
        
        if st.button("✂️ PDF 분할 시작", type="primary"):
            try:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    
                    # 방식 1: 모두 한 장씩
                    if split_mode == "모두 한 장씩 분할":
                        for i in range(total_pages):
                            writer = PdfWriter()
                            writer.add_page(reader.pages[i])
                            pdf_out = io.BytesIO()
                            writer.write(pdf_out)
                            zf.writestr(f"page_{i+1}.pdf", pdf_out.getvalue())
                    
                    # 방식 2: 사용자 지정 범위
                    else:
                        if not custom_range:
                            st.warning("분할 범위를 입력해주세요.")
                            st.stop()
                            
                        ranges = custom_range.replace(" ", "").split(",")
                        for idx, r in enumerate(ranges):
                            writer = PdfWriter()
                            file_label = r # 파일 이름용 라벨
                            if "-" in r:
                                start, end = map(int, r.split("-"))
                                for p in range(start-1, end):
                                    writer.add_page(reader.pages[p])
                            else:
                                writer.add_page(reader.pages[int(r)-1])
                            
                            pdf_out = io.BytesIO()
                            writer.write(pdf_out)
                            zf.writestr(f"split_{idx+1}_(pages_{file_label}).pdf", pdf_out.getvalue())
                
                st.success(f"✅ 성공적으로 {len(ranges) if split_mode != '모두 한 장씩 분할' else total_pages}개의 파일로 분할되었습니다!")
                st.download_button(
                    "📥 분할된 파일들(ZIP) 다운로드", 
                    data=zip_buffer.getvalue(), 
                    file_name=f"split_{split_file.name.replace('.pdf', '')}.zip",
                    mime="application/zip"
                )
            except Exception as e:
                st.error(f"분할 중 오류가 발생했습니다: {e}. 페이지 번호를 다시 확인해주세요.")