# streamlit run api_test_client.py

import streamlit as st
import requests
import tempfile
import os
import zipfile
import shutil
import io

def extract_zip(uploaded_zip, temp_dir):
    """解压上传的ZIP文件并清理不必要的文件"""
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # 清理MAC系统文件
    macosx_dir = os.path.join(temp_dir, '__MACOSX')
    if os.path.exists(macosx_dir):
        shutil.rmtree(macosx_dir)
    
    # 处理可能的单层嵌套目录
    extracted_items = os.listdir(temp_dir)
    if len(extracted_items) == 1:
        nested_dir = os.path.join(temp_dir, extracted_items[0])
        if os.path.isdir(nested_dir):
            for item in os.listdir(nested_dir):
                shutil.move(os.path.join(nested_dir, item), temp_dir)
            os.rmdir(nested_dir)
    
    return temp_dir

def get_tex_files(directory):
    """获取目录中所有.tex文件的相对路径"""
    tex_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.tex'):
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                tex_files.append(rel_path)
    return tex_files

def main():
    st.title("LaTeX转换服务测试客户端")
    st.markdown("---")
    
    # API配置
    API_URL = "http://localhost:12345/api/v1/convert"
    
    # 文件上传部分
    uploaded_file = st.file_uploader("上传源LaTeX项目ZIP文件", type=["zip"])
    main_tex = None
    temp_dir = None
    
    if uploaded_file:
        # 创建临时目录处理上传文件
        temp_dir = tempfile.mkdtemp()
        try:
            # 解压并处理上传文件
            extract_zip(uploaded_file, temp_dir)
            
            # 获取所有.tex文件
            tex_files = get_tex_files(temp_dir)
            
            if not tex_files:
                st.error("ZIP文件中未找到任何.tex文件！")
            else:
                # 自动检测主文档
                for f in tex_files:
                    if 'main.tex' in f.lower():
                        main_tex = f
                        break
                
                # 显示文件选择器
                if len(tex_files) > 1:
                    main_tex = st.selectbox(
                        "选择主文档文件（或保持自动选择）",
                        tex_files,
                        index=tex_files.index(main_tex) if main_tex else 0
                    )
                else:
                    main_tex = tex_files[0]
                    st.info(f"自动选择主文档: {main_tex}")
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    # 模板选择部分
    template_name = st.text_input(
        "输入目标模板名称",
        help="请确保模板已存在于服务器端的templates目录中"
    )
    
    # 转换按钮
    if st.button("开始转换"):
        if not uploaded_file or not template_name:
            st.error("请先上传文件并输入模板名称！")
            return
        
        # 准备请求数据
        files = {
            'source': (uploaded_file.name, uploaded_file.getvalue(), 'application/zip')
        }
        data = {
            'template_name': template_name,
            'main_tex': main_tex or ''
        }
        
        try:
            with st.spinner("正在转换，请稍候..."):
                # 发送请求到API
                response = requests.post(
                    API_URL,
                    files=files,
                    data=data,
                    timeout=30  # 增加超时时间
                )
            
            # 处理响应
            if response.status_code == 200:
                st.success("转换成功！")
                
                # 提供下载
                output_zip = io.BytesIO(response.content)
                file_name = f"converted_{template_name}_{uploaded_file.name}"
                
                st.download_button(
                    label="下载转换后的项目",
                    data=output_zip,
                    file_name=file_name,
                    mime="application/zip"
                )
            else:
                st.error(f"转换失败 (状态码: {response.status_code})")
                try:
                    error_details = response.json()
                    st.error(f"错误详情: {error_details.get('detail', '未知错误')}")
                except:
                    st.error(f"服务器返回: {response.text}")
        
        except requests.exceptions.Timeout:
            st.error("请求超时，请稍后再试")
        except requests.exceptions.RequestException as e:
            st.error(f"连接服务器失败: {str(e)}")
    
    st.markdown("---")
    st.info("""
    **使用说明：**
    1. 确保转换服务正在运行（端口12345）
    2. 上传LaTeX项目的ZIP文件
    3. 输入服务器上已有的模板名称（不含.zip扩展名）
    4. 选择/确认主文档文件
    5. 点击开始转换
    6. 下载转换后的项目
    """)

if __name__ == "__main__":
    main()