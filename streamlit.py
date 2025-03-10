# streamlit run streamlit.py

import streamlit as st
import os
import zipfile
import tempfile
import shutil
import sys
import io
from main import process_latex_files

# 预设模板文件夹
TEMPLATE_FOLDER = "./templates"

def get_available_templates():
    """获取 `./templates` 目录下所有的 .zip 模板文件"""
    return [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.zip')]  # 保留完整的文件名，包括.zip后缀


def extract_zip(uploaded_zip):
    """解压 ZIP 文件，并删除 macOS 的 __MACOSX 文件夹"""
    temp_dir = tempfile.mkdtemp()

    # 解压 ZIP 文件
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # 删除 macOS 特有的 __MACOSX 文件夹（如果存在）
    macosx_folder = os.path.join(temp_dir, '__MACOSX')
    if os.path.exists(macosx_folder):
        shutil.rmtree(macosx_folder)  # 递归删除

    # 检查解压后的结构，避免 macOS 额外嵌套文件夹的问题
    extracted_folders = os.listdir(temp_dir)

    if len(extracted_folders) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_folders[0])):
        # 只有一个子文件夹的情况，返回该文件夹路径
        return os.path.join(temp_dir, extracted_folders[0])

    return temp_dir  # 返回解压后的文件夹路径

def get_tex_files_from_zip(uploaded_zip):
    """解压 ZIP 并返回其中的所有 .tex 文件路径"""
    temp_dir = extract_zip(uploaded_zip)
    tex_files = []

    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".tex"):
                tex_files.append(os.path.relpath(os.path.join(root, file), temp_dir))

    return tex_files, temp_dir  # 返回所有 .tex 文件名和解压路径

# 捕获 print() 输出
def capture_output(func, *args, **kwargs):
    """捕获函数执行过程中所有 print() 输出"""
    buffer = io.StringIO()
    sys.stdout = buffer  # 重定向标准输出
    try:
        return func(*args, **kwargs), buffer.getvalue()  # 执行函数并捕获输出
    finally:
        sys.stdout = sys.__stdout__  # 还原标准输出

def main():
    st.title("LaTeX模板转换工具")
    
    # 初始化 session_state 存储变量
    if "main_tex_file" not in st.session_state:
        st.session_state.main_tex_file = None
    if "show_tex_selector" not in st.session_state:
        st.session_state.show_tex_selector = False

    # 上传源文件的压缩包
    uploaded_source_zip = st.file_uploader("选择包含 LaTeX 文件的压缩包 (ZIP)", type="zip")

    extracted_temp_dir = None
    tex_files = []

    if uploaded_source_zip:
        # 选择 LaTeX 结构类型
        latex_type = st.radio("请选择您上传的LaTex文件的结构类型", ["单一tex文件", "多个tex文件"])

        if latex_type == "多个tex文件":
            tex_files, extracted_temp_dir = get_tex_files_from_zip(uploaded_source_zip)
            
            if tex_files:
                # 按钮用于显示下拉菜单
                if st.button("选择主tex文件"):
                    st.session_state.show_tex_selector = True

                # 如果用户点击过按钮，则显示下拉菜单
                if st.session_state.show_tex_selector:
                    # 更新选择的tex文件
                    st.session_state.main_tex_file = st.selectbox(
                        "请选择主tex文件", tex_files, index=tex_files.index(st.session_state.main_tex_file) if st.session_state.main_tex_file in tex_files else 0
                    )
            else:
                st.error("ZIP 文件中未找到 .tex 文件，请检查内容。")
        else:
            # 如果是单一 tex 文件，直接设定为该文件
            tex_files = get_tex_files_from_zip(uploaded_source_zip)[0]
            if tex_files:
                st.session_state.main_tex_file = tex_files[0]
            else:
                st.error("ZIP 文件中未找到 .tex 文件，请检查内容。")

    # 选择目标模板（从预设模板中选）
    available_templates = get_available_templates()
    selected_template_name = st.selectbox("选择目标模板", [os.path.splitext(f)[0] for f in available_templates])
    selected_template = f"{selected_template_name}.zip"

    # 触发按钮
    if st.button('开始转换'):
        if uploaded_source_zip is not None and selected_template:
            try:
                # 目标模板的压缩包路径
                template_zip_path = os.path.join(TEMPLATE_FOLDER, selected_template)

                # 调用封装后的函数进行处理
                # 捕获 process_latex_files() 的输出，并获取生成的 zip 文件路径
                zip_output_path, output_text = capture_output(
                    process_latex_files, uploaded_source_zip, template_zip_path, st.session_state.main_tex_file
                )
                
                # 显示下载按钮
                with open(zip_output_path, 'rb') as f:
                    st.download_button(
                        label="下载修改后的 LaTeX 文件压缩包",
                        data=f,
                        file_name="converted_result.zip",
                        mime="application/zip"
                    )
                # 在页面底部显示日志
                st.text_area("程序运行日志:", output_text, height=300)

            except Exception as e:
                st.error(f"处理过程中发生错误: {e}")
        else:
            st.error("请上传源文件压缩包并选择目标模板")

if __name__ == "__main__":
    main()
