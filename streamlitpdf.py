# 这个文件只用作demo测试是否能显示pdf review，后续加入主体ui

# streamlit run streamlitpdf.py
# 注意，需要安装 pip install streamlit-pdf-viewerß
import streamlit as st
import os
from producepdf import compile_latex
from streamlit_pdf_viewer import pdf_viewer

st.title("LaTeX PDF Preview")

method = st.selectbox(
    "选择编译方式",
    ["pdflatex", "xelatex", "xelatex*2", "xelatex -> bibtex -> xelatex*2"]
)

if st.button("显示 PDF Preview"):
    pdf_path = compile_latex(method)
    
    if pdf_path and os.path.exists(pdf_path):
        st.success("编译成功！")

        # **先读取 PDF 文件**
        with open(pdf_path, "rb") as pdf_file:
            binary_data = pdf_file.read()

        # **提供 PDF 下载按钮**
        # st.download_button("下载 PDF", binary_data, file_name="output.pdf", mime="application/pdf")

        # **使用 `streamlit_pdf_viewer` 进行 PDF 预览**
        pdf_viewer(input=binary_data, pages_to_render=list(range(1, 3)))

    else:
        st.error(f"编译失败: {pdf_path}")


