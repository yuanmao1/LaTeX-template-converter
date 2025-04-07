# streamlit run streamlit.py
# 注意，需要安装 pip install streamlit-pdf-viewerß

import streamlit as st
import os
import zipfile
import tempfile
import shutil
import sys
import io
import time
from main import process_latex_files
from main import compile_latex
from streamlit_pdf_viewer import pdf_viewer
from targetTemplateRecCompileMapping import target_template_rec_compile_mapping

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

# 更新 Mapping 文件
def add_template_to_mapping(mapping_file, full_template_name, main_tex_name):
    # 读取现有内容
    with open(mapping_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 查找字典的结尾位置
    for i, line in enumerate(lines):
        if line.strip() == "}":  # 字典的结尾部分
            # 在字典结束符号前插入新的映射
            lines.insert(i, f'    "{full_template_name}": "{main_tex_name}",\n')
            break

    # 重新写回文件
    with open(mapping_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

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
        tex_files, extracted_temp_dir = get_tex_files_from_zip(uploaded_source_zip)
        
        if tex_files:
            # 如果只有一个 .tex 文件，则直接设置主 tex 文件
            if len(tex_files) == 1:
                st.session_state.main_tex_file = tex_files[0]
            else:
                # 如果有多个 .tex 文件，直接显示下拉菜单
                st.session_state.main_tex_file = st.selectbox(
                    "请选择您上传文件的主tex文件", tex_files, index=tex_files.index(st.session_state.main_tex_file) if st.session_state.main_tex_file in tex_files else 0
                )
        else:
            st.error("ZIP 文件中未找到 .tex 文件，请检查内容。")

    # 选择目标模板（从预设模板中选）
    available_templates = get_available_templates()
    available_template_names = [os.path.splitext(f)[0] for f in available_templates]
    selected_template_name = st.selectbox("选择目标模板", available_template_names)
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
                    process_latex_files, uploaded_source_zip, template_zip_path, st.session_state.main_tex_file, selected_template
                )
                
                # 显示下载按钮
                with open(zip_output_path, 'rb') as f:
                    st.download_button(
                        label="下载修改后的 LaTeX 文件压缩包",
                        data=f,
                        file_name=os.path.basename(zip_output_path),
                        mime="application/zip"
                    )
                # 在页面底部显示日志
                st.text_area("程序运行日志:", output_text, height=300)

            except Exception as e:
                st.error(f"处理过程中发生错误: {e}")
        else:
            st.error("请上传源文件压缩包并选择目标模板")






    st.markdown("---")  # 添加分隔线，使其显示在页面底部
    # 这里开始是pdf review
    # PDF 预览部分始终显示
    st.subheader("LaTeX PDF Preview")

    # 确保编译方式选择框也始终可见
    method = st.selectbox(
        "选择编译方式",
        ["pdflatex", "xelatex", "xelatex*2", "xelatex -> bibtex -> xelatex*2"]
    )

    # 给出推荐的编译方式
    if selected_template in target_template_rec_compile_mapping:
        rec_compile_method = target_template_rec_compile_mapping[selected_template]
        st.write(f"该模板推荐的编译方式为：{rec_compile_method}")

    # 只有在 main_tex_file 存在时才允许 PDF 预览
    if st.button("显示 PDF Preview"):

        # 每次点击时清空之前的 PDF 缓存
        if "pdf_binary_data" in st.session_state:
            del st.session_state.pdf_binary_data

        if st.session_state.main_tex_file:
            pdf_path = compile_latex(method, st.session_state.main_tex_file)

            # 调试输出 PDF 生成路径
            # st.write(f"生成的 PDF 路径: {pdf_path}")

            st.text("正在加载...")
            time.sleep(5)  # 暂停5秒，也可以改成暂停更久的情况，这是为了以防还没编译出来就直接报错说没pdf的情况

            # 如果 pdf_path 存在，则直接使用它
            if pdf_path and os.path.exists(pdf_path):
                st.success("编译成功！")
            else:
                # 可能存在部分错误，尝试寻找与 main_tex_file 同名的 PDF
                folder_path = "./converted_result"  # 确保文件夹路径指向 './converted_result'
                fallback_pdf_path = os.path.join(folder_path, os.path.splitext(st.session_state.main_tex_file)[0] + ".pdf")
                # st.write(f"找到 PDF 路径: {fallback_pdf_path}")
                
                if os.path.exists(fallback_pdf_path):
                    st.warning(f"编译有部分报错，初步预览文件如下: ")
                    pdf_path = fallback_pdf_path  # 使用找到的 PDF
                else:
                    st.error(f"编译错误，无法预览。")
                    pdf_path = None  # 置空，避免错误

            # 如果找到了 PDF 文件，就读取并存储数据
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    st.session_state.pdf_binary_data = pdf_file.read()

        # 显示 PDF 预览
        if "pdf_binary_data" in st.session_state:
            with st.expander("PDF 预览前两页，点击展开"):
                pdf_viewer(input=st.session_state.pdf_binary_data, width=700, pages_to_render=list(range(1, 3)))







        
    st.markdown("---")  # 添加分隔线，使其显示在页面底部
    st.subheader("上传新的 LaTeX 模板")

    # 让用户上传模板 zip 文件
    uploaded_template = st.file_uploader("上传新的模板 (.zip)", type=["zip"])

    # 创建一个短输入框，让用户输入模板名称
    template_name = st.text_input("输入模板名称", placeholder="模板名称")  # 仅输入名称

    if template_name:
        if template_name in available_template_names:
            st.warning("已有该名称的模板，请更换名称")
        else:
            st.success("模板名称可用")

    # 让用户输入该模板的主 .tex 文件名称
    main_tex_name = st.text_input("输入该模板的主 .tex 文件名（包括 .tex 后缀）", placeholder="主 .tex 文件名称")

    method_name = st.selectbox(
        "选择推荐编译方式",
        ["none", "pdflatex", "xelatex", "xelatex*2", "xelatex -> bibtex -> xelatex*2"]
    )

    if st.button("上传模板"):
        if template_name and template_name not in available_template_names:
            if uploaded_template and main_tex_name and template_name and method_name:
                # 确保 templates 文件夹存在
                os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

                # 拼接完整的模板文件名
                full_template_name = template_name + ".zip"

                # 保存 zip 文件到 templates 文件夹
                template_path = os.path.join(TEMPLATE_FOLDER, full_template_name)
                with open(template_path, "wb") as f:
                    f.write(uploaded_template.getbuffer())

                # 更新 targetTemplateMainTexMapping.py 文件
                add_template_to_mapping("targetTemplateMainTexMapping.py", full_template_name, main_tex_name)

                # 更新 targetTemplateRecCompileMapping 文件
                add_template_to_mapping("targetTemplateRecCompileMapping.py", full_template_name, method_name)

                st.success(f"模板 {full_template_name} 上传成功，主 .tex 文件设为 {main_tex_name}，推荐编译方式设为 {method_name}！")
                st.info("请刷新页面，在下拉菜单中查看新模板。")
            else:
                st.error("请上传 .zip 文件，并输入模板名称和主 .tex 文件名！")
        else:
            st.error("请修改模板名称")




if __name__ == "__main__":
    main()
