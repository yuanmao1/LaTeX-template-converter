# 这个文件用来放函数

# 导入包
import os
import shutil
import re


# 对文件、文件夹操作的一些基本函数

# 创建文件夹副本
def create_copy_folder(folder_path, copy_folder_path):
    # 检查备份文件夹是否已经存在，若存在则删除
    if os.path.exists(copy_folder_path):
        shutil.rmtree(copy_folder_path)
    # 复制整个文件夹
    shutil.copytree(folder_path, copy_folder_path)
    print(f"备份已成功创建: {copy_folder_path}")

# 获取文件列表
def get_tex_files(folder):
    tex_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.tex'):
                tex_files.append(os.path.join(root, file))
    return tex_files

# 让用户选择主文件
def choose_main_tex_file(tex_files):
    print("文件夹中有多个.tex文件，请选择你的主文件：")
    for idx, file in enumerate(tex_files, 1):
        print(f"{idx}. {file}")
    choice = int(input("请输入对应的数字选择主文件: "))
    return tex_files[choice - 1]

# 读取文件内容
def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

# 写入文件内容
def write_file(file_path, lines):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

# 修改tex内容用到的一些函数

# 找maketitle在第几行
def find_maketitle_line(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):  # 从第1行开始
        if '\\maketitle' in line:
            return i  # 返回找到的行号
    
    return -1  # 如果没有找到\maketitle，返回-1

# 删除 \maketitle 上方的所有注释
def remove_comments_before_maketitle(file_path):
    # 打开文件并读取所有行
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # 查找\maketitle所在的行号
    maketitle_line = -1
    for i, line in enumerate(lines):
        if '\\maketitle' in line:
            maketitle_line = i
            break
    
    if maketitle_line == -1:
        print("没有找到\\maketitle")
        return

    # 删除开头到\maketitle之间的注释
    new_lines = []
    for line in lines[:maketitle_line]:
        # 只保留非注释行
        if not line.strip().startswith('%'):
            new_lines.append(line)

    # 添加从\maketitle开始的其余内容
    new_lines.extend(lines[maketitle_line:])

    # 保存修改后的内容回文件
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    

# 把\begin{document}放到\maketitle的上面
def move_begindocument_before_maketitle(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 定位到 \begin{document}
    begindocument_pattern = r'\\begin\{document\}'
    begindocument_match = re.search(begindocument_pattern, content)

    if begindocument_match:
        begindocument_start = begindocument_match.start()
        begindocument_end = begindocument_match.end()

        # 将 \begin{document} 删除
        content = content[:begindocument_start] + content[begindocument_end:]

        # 定位到 \maketitle
        maketitle_pattern = r'\\maketitle'
        maketitle_match = re.search(maketitle_pattern, content)

        if maketitle_match:
            maketitle_start = maketitle_match.start()

            # 在 \maketitle 上面一行插入 \begin{document}
            content = content[:maketitle_start] + '\n' + r'\begin{document}' + '\n' + content[maketitle_start:]

    # 将修改后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


# 修改\title{...},\author{...}, \institution{...}的位置到\maketitle上面

# 因为可能有跨行等情况，所以先定义一个辅助的函数
# 定义一个函数来解析 LaTeX 命令，并确保匹配整个内容，包括换行符、嵌套的 {}

def modify_command_position(file_path, command):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 定义一个函数来解析 LaTeX 命令，并确保匹配整个内容，包括换行符、嵌套的 {}
    def extract_latex_command(content, command):
        # 匹配类似 \command{...} 的结构
        pattern = rf'\\{command}\{{'
        match = re.search(pattern, content)
        
        if not match:
            return None, content
        
        # 找到命令开始的索引
        start_idx = match.start()
        end_idx = start_idx + len(match.group(0))
        
        # 计数括号，处理嵌套的 {}
        open_braces = 1  # 计数开括号
        for i in range(end_idx, len(content)):
            if content[i] == '{':
                open_braces += 1
            elif content[i] == '}':
                open_braces -= 1
            
            # 当括号平衡时，表示整个命令已结束
            if open_braces == 0:
                end_idx = i + 1
                break
        
        # 返回提取的命令内容
        return content[start_idx:end_idx], content[:start_idx] + content[end_idx:]
    

    # 提取指定命令的内容
    command_content, content = extract_latex_command(content, command)

    if command_content:
        print(f"找到了\\{command}，命令内容: {command_content}")
        # 这里可以执行后续的修改操作，比如替换命令等
    else:
        print(f"没有找到 \\{command} 命令")


    if command_content:
        # 找到 \maketitle
        maketitle_pattern = r'\\maketitle'
        maketitle_match = re.search(maketitle_pattern, content)

        if maketitle_match:
            # 在 \maketitle 之前插入整个命令
            content = content[:maketitle_match.start()] + '\n' + command_content + '\n' + content[maketitle_match.start():]
            print(f"成功插入 \\{command} 命令")

    # 将修改后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


# 删除\documentclass行
def remove_documentclass(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 查找包含 \documentclass 的行并删除
    documentclass_lines = [line for line in content if line.strip().startswith(r'\documentclass')]
    
    # 打印删除的 \documentclass 行
    if documentclass_lines:
        print("删除了 \documentclass 行:")
        for line in documentclass_lines:
            print(line.strip())

    # 保留其他行
    content = [line for line in content if not line.strip().startswith(r'\documentclass')]

    # 将修改后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(content)

# 获取旧模板文件夹中的所有 .sty 文件
def get_sty_files(old_template_folder):
    return [f for f in os.listdir(old_template_folder) if f.endswith('.sty')]

# 删除含有 sty 文件名的 \usepackage 语句的函数
def remove_userpackage_sty_lines(old_template_folder, tex_file_path):
    # 获取 .sty 文件名（不包括 .sty 后缀）
    sty_files = get_sty_files(old_template_folder)

    # 打开 .tex 文件并读取内容
    with open(tex_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 遍历所有 .sty 文件并查找对应的 \usepackage{...sty_file_name} 语句
    for sty_file in sty_files:
        sty_file_name = sty_file.replace('.sty', '')  # 获取文件名（不包含 .sty 后缀）
        
        # 打印正在处理的 sty 文件
        print(f"正在处理的 sty 文件: {sty_file_name}.sty")
        
        # 定义匹配模式，查找带选项和不带选项的 \usepackage{...sty_file_name} 语句
        # 更新正则表达式：支持 \usepackage{sty_file_name} 或 \usepackage[...]{sty_file_name}
        package_pattern = rf'\\usepackage(?:\[[^\]]*\])?\s?\{{\s*{re.escape(sty_file_name)}\s*\}}'

        # 找到所有符合条件的行（使用 re.IGNORECASE 使匹配不区分大小写）
        matching_lines = [line for line in content if re.search(package_pattern, line, re.IGNORECASE)]


        # 打印找到的匹配行
        if matching_lines:
            print("找到的匹配行：")
            for line in matching_lines:
                print(line.strip())
        
        # 删除这些行并打印删除的内容
        if matching_lines:
            print(f"删除的 sty 包内容：")
            for line in matching_lines:
                print(line.strip())
            
            # 保留未匹配的行
            content = [line for line in content if not re.search(package_pattern, line, re.IGNORECASE)]
        
        
        else:
            print(f"没有找到匹配的 {sty_file_name} 包")

    # 将修改后的内容写回 .tex 文件
    with open(tex_file_path, 'w', encoding='utf-8') as file:
        file.writelines(content)


# 在 tex 文件中删除包含 mm 的 \usepackage{...} 语句，改成了以下
# 在 tex 文件中删除包含 mm 或 cm 的 \usepackage{...} 语句
def remove_userpackage_mm_cm_lines(tex_file_path):
    # 打开 .tex 文件并读取内容
    with open(tex_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 定义匹配模式，查找带有 mm 或 cm 的 \usepackage{...} 语句
    # 例如：\usepackage[width=122mm,...]{geometry} 或 \usepackage[width=12cm,...]{geometry}
    package_pattern = r'\\usepackage\[[^\]]*(mm|cm)[^\]]*\]?\{[^\}]*\}'

    # 找到所有符合条件的行
    matching_lines = [line for line in content if re.search(package_pattern, line)]

    # 删除这些行并打印删除的内容
    if matching_lines:
        print(f"删除包含mm或cm的包的内容：")
        for line in matching_lines:
            print(line.strip())

        # 保留未匹配的行
        content = [line for line in content if not re.search(package_pattern, line)]
    else:
        print("没有删除包含mm或cm的包")

    # 将修改后的内容写回 .tex 文件
    with open(tex_file_path, 'w', encoding='utf-8') as file:
        file.writelines(content)

# 删除 \begin{document} 之前的所有行，保留 \usepackage和\def开头的行
def remove_lines_before_document(tex_file_path):
    with open(tex_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 查找 \begin{document} 的位置
    begin_document_index = None
    for i, line in enumerate(content):
        if '\\begin{document}' in line:
            begin_document_index = i
            break

    if begin_document_index is None:
        print("未找到 \\begin{document}")
        return

    # 保留以 \usepackage 或 \def 开头的行，并删除 \begin{document} 之前的其他行
    new_content = []
    for i in range(begin_document_index):
        line = content[i]  # 获取当前行内容
        if line.startswith('\\usepackage') or line.startswith('\\def'):
            new_content.append(line)  # 保留 \usepackage 和 \def 开头的行


    # 保留从 \begin{document} 开始的所有行
    new_content.extend(content[begin_document_index:])

    # 将修改后的内容写回文件
    with open(tex_file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_content)

def manage_sty_files(target_folder, modified_folder):
    """删除被修改文件夹中的所有 .sty 文件，并复制目标模板文件夹中的所有 .sty 文件到被修改文件夹中"""
    # 删除被修改文件夹中的所有 .sty 文件
    for root, dirs, files in os.walk(modified_folder):
        for file in files:
            if file.endswith('.sty'):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"已删除文件: {file_path}")

    # 获取目标模板文件夹中的所有 .sty 文件
    sty_files = [f for f in os.listdir(target_folder) if f.endswith('.sty')]

    # 复制每个 .sty 文件到被修改文件夹
    for sty_file in sty_files:
        source_path = os.path.join(target_folder, sty_file)
        destination_path = os.path.join(modified_folder, sty_file)

        # 复制文件
        shutil.copy(source_path, destination_path)
        print(f"已复制文件: {sty_file}")

# 复制 new_template_folder 中的所有 .cls 文件到 old_template_folder 中
def copy_cls_files(new_template_folder, old_template_folder):
    # 获取 new_template_folder 中所有的 .sty 文件
    cls_files = [f for f in os.listdir(new_template_folder) if f.endswith('.cls')]

    # 复制每个 .sty 文件到 old_template_folder
    for cls_file in cls_files:
        source_path = os.path.join(new_template_folder, cls_file)
        destination_path = os.path.join(old_template_folder, cls_file)

        # 复制文件
        shutil.copy(source_path, destination_path)
        print(f"已复制文件: {cls_file}")

# 把new_main_tex的begindocument的前面的部分全部复制到old_main_tex中
def copy_pre_document_to_first_line(new_main_tex, old_main_tex):
    # 读取 new_main_tex 文件
    with open(new_main_tex, 'r', encoding='utf-8') as file:
        content_new = file.readlines()

    # 查找 \begin{document} 的位置
    begin_document_index = None
    for i, line in enumerate(content_new):
        if '\\begin{document}' in line:
            begin_document_index = i
            break

    if begin_document_index is None:
        print("未找到 \\begin{document}")
        return

    # 提取 \begin{document} 之前的部分
    pre_document_content = content_new[:begin_document_index]

    # 读取 old_main_tex 文件
    with open(old_main_tex, 'r', encoding='utf-8') as file:
        content_old = file.readlines()

    # 将 pre_document_content 插入到 old_main_tex 文件的第一行之前
    new_content = pre_document_content + content_old

    # 将修改后的内容写回 old_main_tex 文件
    with open(old_main_tex, 'w', encoding='utf-8') as file:
        file.writelines(new_content)

    print(f"已将 {new_main_tex} 中 \\begindocument 前的部分复制到 {old_main_tex} 的第一行之前。")

# 获取目标模板文件夹下的所有.bst文件并复制到被修改文件夹
def copy_bst_files(target_folder, modified_folder):
    # 获取目标文件夹下的所有.bst文件
    bst_files = []
    for root, dirs, files in os.walk(target_folder):
        for file in files:
            if file.endswith('.bst'):
                bst_files.append(os.path.join(root, file))

    # 如果找到了 .bst 文件，则复制到被修改文件夹
    if bst_files:
        for bst_file in bst_files:
            # 获取文件名并构造目标路径
            bst_filename = os.path.basename(bst_file)
            target_path = os.path.join(modified_folder, bst_filename)
            
            # 复制文件
            shutil.copy(bst_file, target_path)
            print(f"已复制 {bst_filename} 到 {modified_folder}")
    else:
        print("目标模板文件夹没有找到 .bst 文件")

# 找tex文件的\bibliographystyle{...}
def find_bibliographystyle(tex_file_path):
    """查找文件中的 \bibliographystyle{...}"""
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if '\\bibliographystyle{' in line:
            # 返回找到的 bibliographystyle 的内容
            start = line.find('{') + 1
            end = line.find('}')
            return line[start:end]
    return None  # 如果没有找到 \bibliographystyle{...}


# 修改bib内容
def modify_bibliography(tex_file_path, target_bibliographystyle):
    """修改被修改的 tex 文件中的 bibliographystyle"""
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    bibliographystyle_line = None
    end_document_line = None

    # 查找 \bibliographystyle{...} 和 \end{document} 的行号
    for i, line in enumerate(lines, 1):
        if '\\bibliographystyle{' in line:
            bibliographystyle_line = i
        elif '\\end{document}' in line:
            end_document_line = i

    # 如果没有找到 \bibliographystyle{...}，就需要插入
    if bibliographystyle_line is None and end_document_line:
        # 在 \end{document} 之前插入 \bibliographystyle 和 \bibliography
        lines.insert(end_document_line - 1, f"\\bibliographystyle{{{target_bibliographystyle}}}\n")
        lines.insert(end_document_line, "\\bibliography{yourbib}\n")
        # 创建一个空的 yourbib.bib 文件
        with open(os.path.join(os.path.dirname(tex_file_path), 'yourbib.bib'), 'w', encoding='utf-8') as bib_file:
            bib_file.write("% Please add references to yourbib.bib file\n")
        print(f"已在 \\end{{document}} 之前插入 \\bibliographystyle{{{target_bibliographystyle}}} 和 \\bibliography{{yourbib}}")
        print("已创建了一个空的yourbib.bib文件，请放入你的引用文献")
    
    # 如果找到 \bibliographystyle{...}，进行修改
    elif bibliographystyle_line is not None:
        old_bibliographystyle = lines[bibliographystyle_line - 1].strip().split('{')[1].split('}')[0]
        if old_bibliographystyle != target_bibliographystyle:
            lines[bibliographystyle_line - 1] = f"\\bibliographystyle{{{target_bibliographystyle}}}\n"
            print(f"已将 \\bibliographystyle{{{old_bibliographystyle}}} 修改为 \\bibliographystyle{{{target_bibliographystyle}}}")
        else:
            print("bibliographystyle 已经是目标的格式，无需修改")
    
    # 将修改后的内容写回文件
    with open(tex_file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def process_tex_files(modified_tex_path, target_tex_path):
    # 查找被修改文件和目标模板文件中的 \bibliographystyle{...}
    modified_bibliographystyle = find_bibliographystyle(modified_tex_path)
    target_bibliographystyle = find_bibliographystyle(target_tex_path)

    if target_bibliographystyle:
        print(f"在目标模板文件中找到了 bibliographystyle 为：{target_bibliographystyle}")
        
        if modified_bibliographystyle:
            print(f"在被修改文件中找到了 bibliographystyle 为：{modified_bibliographystyle}")
            modify_bibliography(modified_tex_path, target_bibliographystyle)
        else:
            print("在被修改文件中没有找到 bibliographystyle")
            modify_bibliography(modified_tex_path, target_bibliographystyle)
    else:
        print("目标模板没有 \\bibliographystyle{...}，请根据目标模板官方文档手动修改 bib")

# -------------------
# 改bug

# \begin{document}前加入\usepackage[OT1]{fontenc} 
def add_fontenc_package(tex_file_path):
    """在 \\begin{document} 之前插入 \\usepackage[OT1]{fontenc}"""
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    begindocument_line = None

    # 查找 \\begin{document} 的行号，转义反斜杠
    for i, line in enumerate(lines, 1):
        if '\\begin{document}' in line:  # 使用双反斜杠
            begindocument_line = i
            break

    # 如果找到 \\begin{document}，就插入 \\usepackage[OT1]{fontenc}
    if begindocument_line:
        lines.insert(begindocument_line - 1, "\\usepackage[OT1]{fontenc}\n")  # 转义反斜杠
        print("已在 \\begin{document} 之前插入 \\usepackage[OT1]{fontenc}")
    else:
        print("没有找到 \\begin{document}，无法插入 \\usepackage[OT1]{fontenc}")

    # 将修改后的内容写回文件
    with open(tex_file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# 在\begin{document}之前插入\usepackage{subcaption}
def add_subcaption_package_before_document(file_path):
    # 读取文件内容
    lines = read_file(file_path)
    
    # 查找 \begin{document} 的位置
    begin_document_line = None
    for i, line in enumerate(lines):
        if '\\begin{document}' in line:
            begin_document_line = i
            break
    
    if begin_document_line is not None:
        # 要插入的包
        package_to_insert = '\\usepackage{subcaption}\n'
        
        # 检查是否已经存在 \usepackage{subcaption}
        if any('\\usepackage{subcaption}' in line for line in lines):
            print("文件中已包含 \\usepackage{subcaption}，无需重复添加。")
        else:
            # 在 \begin{document} 前插入 \usepackage{subcaption}
            lines = lines[:begin_document_line] + [package_to_insert] + lines[begin_document_line:]
            
            # 写回修改后的文件
            write_file(file_path, lines)
            print("已在 \\begin{document} 前添加 \\usepackage{subcaption}。")
    else:
        print("未找到 \\begin{document}，无法插入 \\usepackage{subcaption}。")




# 删除第二个hyperref包
def remove_second_hyperref(file_path):
    lines = read_file(file_path)  # 读取文件内容
    new_lines = []
    hyperref_count = 0  # 用于计数遇到的 \usepackage{hyperref} 次数

    # 遍历每一行，检查是否包含 \usepackage{hyperref}
    for line in lines:
        # 正则表达式用于匹配 \usepackage{hyperref} 和带选项的 \usepackage[...]{hyperref}
        if re.match(r'\\usepackage(\[.*\])?{hyperref}', line):
            hyperref_count += 1
            if hyperref_count == 2:  # 如果是第二次出现
                continue  # 跳过第二次出现的 \usepackage{hyperref}，相当于删除该行
        new_lines.append(line)  # 保留其他行

    # 写回修改后的内容
    write_file(file_path, new_lines)
    print("已删除第二个 \\usepackage{hyperref}")

# 添加//的定义，防止\author换行无法识别
def add_pdfstringdef_before_document(file_path):
    # 读取文件内容
    lines = read_file(file_path)
    
    # 查找 \begin{document} 的位置
    begin_document_line = None
    for i, line in enumerate(lines):
        if '\\begin{document}' in line:
            begin_document_line = i
            break
    
    if begin_document_line is not None:
        # 在 \begin{document} 前插入 \pdfstringdefDisableCommands
        pdfstringdef_lines = [
            '\\pdfstringdefDisableCommands{%\n',
            '  \\def\\\\{}%\n',
            '  \\def\\texttt#1{<#1>}%\n',
            '}%\n'
        ]
        lines = lines[:begin_document_line] + pdfstringdef_lines + lines[begin_document_line:]
        
        # 写回修改后的文件
        write_file(file_path, lines)
        print("已在 \\begin{document} 前添加 \\pdfstringdefDisableCommands。")
    else:
        print("未找到 \\begin{document}，无法插入 \\pdfstringdefDisableCommands。")

# 添加\eg等符号的定义
def add_custom_macros_before_document(file_path):
    # 读取文件内容
    lines = read_file(file_path)
    
    # 查找 \begin{document} 的位置
    begin_document_line = None
    for i, line in enumerate(lines):
        if '\\begin{document}' in line:
            begin_document_line = i
            break
    
    if begin_document_line is not None:
        # 定义缩写命令和 \onedot 的宏
        custom_macros = [
            '\\def\\onedot{.} % 定义 \\onedot 为句点\n',
            '% 定义缩写命令\n',
            '\\def\\eg{\\emph{e.g}\\onedot}\n',
            '\\def\\Eg{\\emph{E.g}\\onedot}\n',
            '\\def\\ie{\\emph{i.e}\\onedot}\n',
            '\\def\\Ie{\\emph{I.e}\\onedot}\n',
            '\\def\\cf{\\emph{cf}\\onedot}\n',
            '\\def\\Cf{\\emph{Cf}\\onedot}\n',
            '\\def\\etc{\\emph{etc}\\onedot}\n',
            '\\def\\vs{\\emph{vs}\\onedot}\n',
            '\\def\\wrt{w.r.t\\onedot}\n',
            '\\def\\dof{d.o.f\\onedot}\n',
            '\\def\\iid{i.i.d\\onedot}\n',
            '\\def\\wolog{w.l.o.g\\onedot}\n',
            '\\def\\etal{\\emph{et al}\\onedot}\n'
        ]
        
        # 在 \begin{document} 前插入宏定义
        lines = lines[:begin_document_line] + custom_macros + lines[begin_document_line:]
        
        # 写回修改后的文件
        write_file(file_path, lines)
        print("已在 \\begin{document} 前添加自定义宏定义。")
    else:
        print("未找到 \\begin{document}，无法插入自定义宏定义。")
