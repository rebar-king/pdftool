import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import zipfile
import fitz  # PyMuPDF

# 넓은 화면(layout="wide")을 제거하여 중앙에 깔끔하게 모이도록 수정했습니다.
st.set_page_config(page_title="나만의 PDF 종합 도구 프로")
st.title("📄 PDF 종합 도구 (v4.1)")

# 세션 상태 초기화
if 'pdf_list' not in st.session_state:
    st.session_state.pdf_list = []

# 요청하신 대로 탭 순서를 변경했습니다!
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🖼️ 이미지 ➔ PDF", 
    "🖼️ PDF ➔ 이미지", # 위치 변경됨
    "🔗 PDF 병합", 
    "✂️ PDF 분할", 
    "🔄 PDF 회전/삭제"
])

# --- (1) 이미지 -> PDF 변환 ---
with tab1:
    st.header("이미지를 PDF로 변환")
    col1, col2 = st.columns(2) # 2분할 적용
    
    with col1:
        uploaded_images = st.file_uploader("이미지 파일 선택 (여러 개 가능)", type=["jpg", "jpeg", "png", "bmp", "gif", "webp"], accept_multiple_files=True, key="img_up")
        
    with col2:
        if uploaded_images:
            st.info(f"총 {len(uploaded_images)}개의 이미지가 선택되었습니다.")
            if st.button("🔥 PDF 생성 및 다운로드", key="img_gen_btn", use_container_width=True, type="primary"):
                pdf_bytes = io.BytesIO()
                images = [Image.open(img).convert("RGB") for img in uploaded_images]
                images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])
                st.success("✅ 변환 완료!")
                st.download_button("📥 다운로드", data=pdf_bytes.getvalue(), file_name="images_converted.pdf", use_container_width=True)

# --- (2) PDF ➔ 이미지 변환 (순서 변경됨) ---
with tab2:
    st.header("PDF를 이미지로 변환")
    col1, col2 = st.columns(2) # 2분할 적용
    
    with col1:
        pdf_to_img_file = st.file_uploader("이미지로 변환할 PDF 선택", type="pdf", key="pdf_img_conv_up")
        
    with col2:
        if pdf_to_img_file:
            st.info(f"선택된 파일: {pdf_to_img_file.name}")
            img_format = st.selectbox("변환할 이미지 포맷 선택", ["PNG", "JPEG"])
            
            if st.button("🖼️ 변환 시작 및 다운로드(ZIP)", use_container_width=True, type="primary"):
                try:
                    doc = fitz.open(stream=pdf_to_img_file.getvalue(), filetype="pdf")
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        progress_text = "이미지 변환 중..."
                        my_bar = st.progress(0, text=progress_text)
                        
                        for i in range(len(doc)):
                            page = doc.load_page(i)
                            pix = page.get_pixmap(dpi=200)
                            img_data = pix.tobytes(img_format.lower())
                            zf.writestr(f"page_{i+1}.{img_format.lower()}", img_data)
                            my_bar.progress((i + 1) / len(doc), text=f"변환 중... ({i+1}/{len(doc)})")
                            
                    st.success(f"✅ 총 {len(doc)}페이지 변환 완료!")
                    st.download_button("📥 변환된 이미지(ZIP) 다운로드", data=zip_buffer.getvalue(), file_name=f"{pdf_to_img_file.name.replace('.pdf', '')}_images.zip", mime="application/zip", use_container_width=True)
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# --- (3) PDF 파일 병합 ---
with tab3:
    st.header("여러 PDF 파일 병합")
    col1, col2 = st.columns([1.2, 1]) # 좌측(파일 업로드)을 살짝 더 넓게 분할
    
    with col1:
        uploaded_pdfs = st.file_uploader("PDF 파일을 추가하세요", type="pdf", accept_multiple_files=True, key="pdf_merge_up")
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
                c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
                c1.write(f"**{i+1}. {pdf_file.name}**")
                if c2.button("↑", key=f"up_{i}"): to_move_up = i
                if c3.button("↓", key=f"down_{i}"): to_move_down = i

            if to_move_up is not None and to_move_up > 0:
                st.session_state.pdf_list[to_move_up], st.session_state.pdf_list[to_move_up-1] = st.session_state.pdf_list[to_move_up-1], st.session_state.pdf_list[to_move_up]
                st.rerun()
            if to_move_down is not None and to_move_down < len(st.session_state.pdf_list)-1:
                st.session_state.pdf_list[to_move_down], st.session_state.pdf_list[to_move_down+1] = st.session_state.pdf_list[to_move_down+1], st.session_state.pdf_list[to_move_down]
                st.rerun()

    with col2:
        if st.session_state.pdf_list:
            st.subheader("⚙️ 페이지 범위 설정")
            pdf_configs = []
            for i, pdf_file in enumerate(st.session_state.pdf_list):
                with st.expander(f"📄 {pdf_file.name}", expanded=False):
                    reader = PdfReader(pdf_file)
                    mode = st.radio(f"추출 범위", ["전체", "일부"], key=f"m_{i}", horizontal=True)
                    page_selection = st.text_input("페이지 (예: 1, 3-5)", key=f"p_{i}") if mode == "일부" else ""
                    pdf_configs.append({"reader": reader, "mode": mode, "selection": page_selection})

            st.divider()
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
                    st.download_button("📥 병합된 PDF 다운로드", data=output.getvalue(), file_name="merged.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"오류: {e}")

# --- (4) PDF 파일 분할 ---
with tab4:
    st.header("PDF 파일 분할")
    col1, col2 = st.columns(2) # 2분할 적용
    
    with col1:
        split_file = st.file_uploader("분할할 PDF 파일을 선택하세요", type="pdf", key="pdf_split_up")
        if split_file:
            reader = PdfReader(split_file)
            total_pages = len(reader.pages)
            st.info(f"선택된 파일: {split_file.name} (총 {total_pages} 페이지)")
            
    with col2:
        if split_file:
            split_mode = st.radio("분할 방식 선택", ["모두 한 장씩 분할", "사용자 지정 범위로 분할"])
            custom_range = ""
            if split_mode == "사용자 지정 범위로 분할":
                custom_range = st.text_input("분할 범위 입력 (예: 1, 2-3)", placeholder="예: 1, 2-3")
            
            st.write("") # 간격 띄우기
            if st.button("✂️ PDF 분할 시작", use_container_width=True, type="primary"):
                try:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        if split_mode == "모두 한 장씩 분할":
                            for i in range(total_pages):
                                writer = PdfWriter()
                                writer.add_page(reader.pages[i])
                                pdf_out = io.BytesIO()
                                writer.write(pdf_out)
                                zf.writestr(f"page_{i+1}.pdf", pdf_out.getvalue())
                        else:
                            if not custom_range:
                                st.warning("분할 범위를 입력해주세요.")
                                st.stop()
                            ranges = custom_range.replace(" ", "").split(",")
                            for idx, r in enumerate(ranges):
                                writer = PdfWriter()
                                if "-" in r:
                                    start, end = map(int, r.split("-"))
                                    for p in range(start-1, end): writer.add_page(reader.pages[p])
                                else:
                                    writer.add_page(reader.pages[int(r)-1])
                                pdf_out = io.BytesIO()
                                writer.write(pdf_out)
                                zf.writestr(f"split_{idx+1}_(pages_{r}).pdf", pdf_out.getvalue())
                    st.success("✅ 분할 완료!")
                    st.download_button("📥 분할 파일(ZIP) 다운로드", data=zip_buffer.getvalue(), file_name=f"split_{split_file.name.replace('.pdf', '')}.zip", mime="application/zip", use_container_width=True)
                except Exception as e:
                    st.error(f"오류: {e}")

# --- (5) PDF 회전 및 삭제 ---
with tab5:
    st.header("PDF 페이지 회전 및 삭제")
    edit_file = st.file_uploader("편집할 PDF 파일 선택", type="pdf", key="pdf_edit_up")
    
    if edit_file:
        reader = PdfReader(edit_file)
        total_pages = len(reader.pages)
        st.info(f"선택된 파일: {edit_file.name} (총 {total_pages} 페이지)")
        
        col1, col2 = st.columns(2) # 이미 2분할 되어있던 부분
        with col1:
            st.subheader("🔄 페이지 회전")
            rotate_mode = st.radio("회전 범위", ["적용 안함", "전체 페이지", "일부 페이지"], key="rot_mode")
            rotate_angle = st.selectbox("회전 각도", [90, 180, 270], format_func=lambda x: f"{x}도 회전")
            rotate_pages = ""
            if rotate_mode == "일부 페이지":
                rotate_pages = st.text_input("회전할 페이지 (예: 1, 3-5)", key="rot_pages")
                
        with col2:
            st.subheader("🗑️ 페이지 삭제")
            delete_pages = st.text_input("삭제할 페이지 (예: 2, 4-6)", key="del_pages")

        st.divider()
        if st.button("✨ 편집 적용 및 다운로드", type="primary", use_container_width=True, key="edit_btn"):
            writer = PdfWriter()
            try:
                del_set = set()
                if delete_pages:
                    for part in delete_pages.replace(" ", "").split(","):
                        if "-" in part:
                            s, e = map(int, part.split("-"))
                            del_set.update(range(s-1, e))
                        else:
                            del_set.add(int(part)-1)
                            
                rot_set = set()
                if rotate_mode == "전체 페이지":
                    rot_set.update(range(total_pages))
                elif rotate_mode == "일부 페이지" and rotate_pages:
                    for part in rotate_pages.replace(" ", "").split(","):
                        if "-" in part:
                            s, e = map(int, part.split("-"))
                            rot_set.update(range(s-1, e))
                        else:
                            rot_set.add(int(part)-1)
                            
                for i in range(total_pages):
                    if i in del_set:
                        continue 
                        
                    page = reader.pages[i]
                    if i in rot_set:
                        page.rotate(rotate_angle) 
                        
                    writer.add_page(page)
                    
                output = io.BytesIO()
                writer.write(output)
                st.success("✅ 회전 및 삭제 완료!")
                st.download_button("📥 편집된 PDF 다운로드", data=output.getvalue(), file_name=f"edited_{edit_file.name}", use_container_width=True)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
