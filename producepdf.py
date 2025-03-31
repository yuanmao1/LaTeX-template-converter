# 这个文件只用作demo测试是否能显示pdf review，后续加入主体ui

# producepdf.py
import subprocess
import os

def compile_latex(method):
    folder_path = os.path.abspath('./converted_result')  # 使用绝对路径
    tex_filename = 'main.tex'

    tex_path = os.path.join(folder_path, tex_filename)

    if not os.path.exists(tex_path):
        return f"Error: {tex_path} not found."

    commands = []

    if method == "pdflatex":
        commands.append(["pdflatex", "-interaction=nonstopmode", tex_filename])
    elif method == "xelatex":
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
    elif method == "xelatex*2":
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
    elif method == "xelatex -> bibtex -> xelatex*2":
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
        commands.append(["bibtex", "main"])  # bibtex 只需要 .aux 文件的前缀
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
        commands.append(["xelatex", "-interaction=nonstopmode", tex_filename])
    else:
        return "Invalid method"

    for cmd in commands:
        result = subprocess.run(cmd, cwd=folder_path, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error in {cmd[0]}: {result.stderr}"

    pdf_path = os.path.join(folder_path, "main.pdf")
    return pdf_path if os.path.exists(pdf_path) else "Error: PDF not generated."
