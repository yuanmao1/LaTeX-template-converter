# streamlit run streamlit.py


import streamlit as st
from main import process_latex_files

def main():
    st.title("LaTeX模板转换工具")
    
    # 上传源文件的压缩包
    uploaded_source_zip = st.file_uploader("选择包含LaTeX文件的压缩包 (ZIP)", type="zip")
    
    # 上传目标模板文件夹的压缩包
    uploaded_template_zip = st.file_uploader("选择包含目标模板的压缩包 (ZIP)", type="zip")

    # 触发按钮
    if st.button('开始转换'):
        if uploaded_source_zip is not None and uploaded_template_zip is not None:
            try:
                # 调用封装后的函数进行处理
                zip_output_path = process_latex_files(
                    uploaded_source_zip, uploaded_template_zip
                )
                
                # 显示下载按钮
                with open(zip_output_path, 'rb') as f:
                    st.download_button(
                        label="下载修改后的LaTeX文件压缩包",
                        data=f,
                        file_name="converted_result.zip",
                        mime="application/zip"
                    )
            except Exception as e:
                st.error(f"处理过程中发生错误: {e}")
        else:
            st.error("请上传源文件压缩包和目标模板压缩包")

if __name__ == "__main__":
    main()
