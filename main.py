# 这个程序的目的是快速进行latex模板的修改
# 引入包
import os
import zipfile
import tempfile
from shutil import rmtree
# 引入函数
from function import *

# 在总文件夹中，有很多个从外部下载下来的期刊latex模板作为例子
# 你可以新建一个文件夹来放你需要被修改的latex文件，例如可以给这个文件夹起名叫做your_work_to_be_converted
# 你也可以新建一个文件夹来放你需要修改成的期刊latex模板，例如可以给这个文件夹起名叫做target_converted_template

# 选择需要被修改的文件夹路径

# 由于这里我想把CVPR 2022模板作为我需要被修改的latex文件，把NeurIPS 2024模板作为目标模板，我直接选择了这两个模板的文件夹
# 如果你想要放你的文件夹和别的目标模板的话，你也可以自行修改下面的两行代码为：
# your_work_folder = './your_work_to_be_converted'
# target_template_folder = './target_converted_template'

# your_work_folder = './CVPR 2022'
# target_template_folder = './ECCV 2016'


# 解压zip文件并删除 macOS 特有的 __MACOSX 文件夹
def extract_zip(uploaded_zip):
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()

    # 解压 ZIP 文件
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # 删除 macOS 特有的 __MACOSX 文件夹（如果存在）
    macosx_folder = os.path.join(temp_dir, '__MACOSX')
    if os.path.exists(macosx_folder):
        rmtree(macosx_folder)  # 递归删除 __MACOSX 文件夹及其中的内容

    # 检查解压后的文件夹结构，如果最外层文件夹包含多个文件夹，返回原目录
    extracted_folders = os.listdir(temp_dir)

    # 如果解压后的内容是多个文件或文件夹，并且需要保留原结构
    if len(extracted_folders) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_folders[0])):
        # 如果只有一个文件夹，返回该文件夹路径
        temp_dir = os.path.join(temp_dir, extracted_folders[0])

    return temp_dir  # 返回解压后的文件夹路径

# 压缩文件夹为.zip
def zip_folder(folder_path, output_zip_path):
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):  # 不需要 dirs，所以用 `_` 占位
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

# 删除原本的'./converted_result'文件夹并创建一个新的文件夹
def reset_converted_result_folder(folder_path='./converted_result'):
    # 删除已存在的文件夹及其内容
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"已删除文件夹: {folder_path}")

    # 创建新的空文件夹
    os.makedirs(folder_path)
    print(f"已创建新的文件夹: {folder_path}")

# 删除原本的'./converted_result.zip'文件（如果存在）
def delete_existing_zip(zip_path='./converted_result.zip'):
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"已删除文件: {zip_path}")
    else:
        print(f"没有找到文件: {zip_path}")

# 把整个python文件封装成一个函数以便调用
def process_latex_files(source_zip, template_zip):
    # 解压源文件和目标模板的.zip文件
    your_work_folder = extract_zip(source_zip)
    target_template_folder = extract_zip(template_zip)

    # 为了不影响原始的文件，我们新建两个副本文件夹来放要被修改的文件和目标模板
    # 之后的操作我们都在这两个副本文件夹上操作，最终的结果会储存在converted_result_folder文件夹中
    
    # 先删除原有的'./converted_result'文件夹并重新创建
    reset_converted_result_folder('./converted_result')
    # 删除原本的'./converted_result.zip'文件（如果存在）
    delete_existing_zip('./converted_result.zip')

    converted_result_folder = './converted_result'
    target_template_folder_copy = './target_template_copy'

    create_copy_folder(your_work_folder,converted_result_folder)
    create_copy_folder(target_template_folder,target_template_folder_copy)

    # 获取需修改文件和目标模板的tex文件
    yourwork_tex_files = get_tex_files(converted_result_folder)
    target_tex_files = get_tex_files(target_template_folder_copy)

    # 在实际操作中，发现一个完整的latex文件夹中可能出现多个tex文件，所以在这种情况时需要让用户手动选择以下哪个tex文件是论文主体的tex文件

    # 检查需修改的latex文件夹中是否有.tex文件
    if not yourwork_tex_files:
        print("需修改的文件夹中没有 .tex 文件！")
    else:
        if len(yourwork_tex_files) > 1:
            print(f"需修改的文件夹中有 {len(yourwork_tex_files)} 个.tex文件：")
            yourwork_main_tex = choose_main_tex_file(yourwork_tex_files)
            print(f"选择的需修改的主文件: {yourwork_main_tex}\n")
        else:
            yourwork_main_tex = yourwork_tex_files[0]
            print(f"需修改的文件夹中只有一个.tex文件，自动选择: {yourwork_main_tex}\n")

    # 检查目标模板是否有.tex文件
    if not target_tex_files:
        print("目标模板文件夹中没有 .tex 文件！")
    else:
        if len(target_tex_files) > 1:
            print(f"目标模板文件夹中有 {len(target_tex_files)} 个.tex文件：")
            target_main_tex = choose_main_tex_file(target_tex_files)
            print(f"选择的目标模板主文件: {target_main_tex}\n")
        else:
            target_main_tex = target_tex_files[0]
            print(f"目标模板文件夹中只有一个.tex文件，自动选择: {target_main_tex}\n")

    # 至此，我们已经新建了副本文件夹作为工作区，并找到了需修改和目标模板文件夹中的tex文件，下面我们需要对工作区中的tex文件内容进行一些修改
    # 做以下修改顺序的操作是为了分开\maketitle的部分和论文最开头定义排版格式的部分

    # 需要对\maketitle, \begin{document}, title{...}, \author{...}, \institution{...}进行位置上的更改操作
    # 想要基于\maketitle的位置，得到以下顺序：

    # \begin{document}
    # title{...}
    # \author{...}
    # \institution{...}
    # \maketitle

    # 对于被修改的文件夹中的论文主体tex文件：

    # （调试部分可删去）先来看一下最开始\maketitle在什么位置
    origin_maketitle_line = find_maketitle_line(yourwork_main_tex)
    print(f"最初\\maketitle 在第{origin_maketitle_line}行")

    # 为了防止注释对后续操作进行影响，我们先将\maketitle上方的注释给删掉
    remove_comments_before_maketitle(yourwork_main_tex)

    # （调试部分可删去）看一下删除注释后的\maketitle在什么位置
    afterdeletecomment_maketitle_line = find_maketitle_line(yourwork_main_tex)
    print(f"删除注释后新的\\maketitle 在第{afterdeletecomment_maketitle_line}行")

    # 将\begin{document}放到\maketitle的上面
    move_begindocument_before_maketitle(yourwork_main_tex)

    # 将\title{...},\author{...}, \institution{...}依次放到\maketitle的上面
    modify_command_position(yourwork_main_tex, 'title')
    modify_command_position(yourwork_main_tex, 'author')
    modify_command_position(yourwork_main_tex, 'institute')

    # 除此之外，对于目标模板文件夹，我们也做一样的操作
    # 做该操作的目的相同，是为了分开\maketitle的部分和论文最开头定义排版格式的部分
    remove_comments_before_maketitle(target_main_tex)
    move_begindocument_before_maketitle(target_main_tex)
    modify_command_position(target_main_tex, 'title')
    modify_command_position(target_main_tex, 'author')
    modify_command_position(target_main_tex, 'institute')

    # 我们已经做好了准备工作，下面正式来修改格式

    # 对于被修改的文件夹中的论文主体tex文件：
    # 删除被修改tex文件的\documentclass， \userpackage{sty_file_name}, 包含 mm 的 \usepackage{...} 语句
    remove_documentclass(yourwork_main_tex)
    remove_userpackage_sty_lines(your_work_folder, yourwork_main_tex)
    remove_userpackage_mm_lines(yourwork_main_tex)

    # 删掉\begin{document}上面除了\userpackage和\def之外的行
    remove_lines_before_document(yourwork_main_tex)

    # 识别新模板的sty和cls文件复制到旧模板里
    manage_sty_files(target_template_folder_copy, converted_result_folder)
    copy_cls_files(target_template_folder_copy, converted_result_folder)

    # 把目标模板的tex文件中的\begin{document}的前面的部分全部复制到old_main_tex中，即把目标模板的格式代码复制到被修改的tex文件最前面
    copy_pre_document_to_first_line(target_main_tex, yourwork_main_tex)

    # ------------------------------
    # 将目标文件夹下的.bst文件复制到被修改文件夹
    copy_bst_files(target_template_folder_copy, converted_result_folder)

    # 将bibstyle改成目标模板的格式
    process_tex_files(yourwork_main_tex, target_main_tex)

    # ------------------------------
    # 以下是针对模板CVPR2022，ECCV2016，NeurIPS2024模板做出的补丁
    # 如果你没有使用这些模板，也可以不加载下面的内容

    print("以下是针对模板CVPR2022，ECCV2016，NeurIPS2024模板做出的补丁修改")

    # bug 1:
    # \begin{document}前加入\usepackage[OT1]{fontenc} 
    add_fontenc_package(yourwork_main_tex)

    # bug 2:
    # 使用subfigure时会报错
    # 在\begin{document}之前插入\usepackage{subcaption}
    add_subcaption_package_before_document(yourwork_main_tex)

    # bug 3:
    # 当一个文档出现两次hyperref包时会报错
    # 出现两次\userpackage{hyperref}，删掉后一个\userpackage{hyperref}
    # remove_second_hyperref(yourwork_main_tex)
    # 更新：
    # 因为有些hyperref是自带在sty中的，所以这个方法并不合理
    # 手动注释掉报错的hyperref就可以了



    # bug 4:
    # \author{...}中有换行，会报错，添加以下行在\begin{document}之前：
    # \pdfstringdefDisableCommands{%
    #   \def\\{}%
    #   \def\texttt#1{<#1>}%
    # }
    add_pdfstringdef_before_document(yourwork_main_tex)

    # bug 5:
    # 当出现\eg等在原sty文件中的定义时出现bug，加入：
    # \def\onedot{.} % 定义 \onedot 为句点
    # % 定义缩写命令
    # \def\eg{\emph{e.g}\onedot} 
    # \def\Eg{\emph{E.g}\onedot}
    # \def\ie{\emph{i.e}\onedot} 
    # \def\Ie{\emph{I.e}\onedot}
    # \def\cf{\emph{cf}\onedot} 
    # \def\Cf{\emph{Cf}\onedot}
    # \def\etc{\emph{etc}\onedot} 
    # \def\vs{\emph{vs}\onedot}
    # \def\wrt{w.r.t\onedot} 
    # \def\dof{d.o.f\onedot}
    # \def\iid{i.i.d\onedot} 
    # \def\wolog{w.l.o.g\onedot}
    # \def\etal{\emph{et al}\onedot}
    add_custom_macros_before_document(yourwork_main_tex)

    # bug 6:
    # sty包受到大小写影响，比如emnlp2023.sty，要删掉\usepackage[review]{EMNLP2023}，因为大写所以没删成功

    # ------------------------------
    # 未完成的debug

    # bug 1:
    # 改到NeurIPS 2024模板要把bibstyle改成\bibliographystyle{rusnat}，或者其他natbib兼容的格式

    # bug 2:
    # bib的\cite错误，解决方法：
    # 删掉bbl文件，进入bib文件保存一下，再到tex中编译就可以了

    # 最终将处理结果压缩为一个zip文件
    zip_output_path = './converted_result.zip'
    zip_folder(converted_result_folder, zip_output_path)

    return zip_output_path  # 返回处理好的zip文件路径










    # ------------------------------
    # 测试日志：

    # 测试1:
    # your_work_folder = './NeurIPS 2024'
    # target_template_folder = './ECCV 2016'
    # \ack环境未定义，删了就行

    # 测试2:
    # your_work_folder = './ECCV 2016'
    # target_template_folder = './NeurIPS 2024'
    # 删掉institute、keyword
    # 改成\bibliographystyle{rusnat}

    # 测试3:
    # your_work_folder = './ECCV 2016'
    # target_template_folder = './CVPR 2022'
    #（已完成） \begin{document}前加入\usepackage[OT1]{fontenc} 
    # （已完成）复制.bst文件过来 

    # 测试4:
    # your_work_folder = './CVPR 2022'
    # target_template_folder = './ECCV 2016'
    # （已完成）删除原本的.sty文件
    # （已完成）subfigure出现bug，加入\usepackage{subcaption}
    # （已完成）\eg等出现bug，加入def

    # 测试5:
    # your_work_folder = './NeurIPS 2024'
    # target_template_folder = './CVPR 2022'
    # ack的问题

    # 测试6:
    # your_work_folder = './CVPR 2022'
    # target_template_folder = './NeurIPS 2024'
    # （已完成）删除后一个hyperref
    # 改成\bibliographystyle{rusnat}
    # bib的格式错误，进入bib文件保存一下，再到tex中编译就可以了

    # 测试 7:
    # your_work_folder = './CVPR 2022'
    # target_template_folder = './EMNLP 2023'
    # 删掉hyperref和\pdfoutput=1
    # 删掉bbl，到bib保存再跑

    # 测试 8:
    # your_work_folder = './EMNLP 2023'
    # target_template_folder = './CVPR 2022'
    # （已完成）修改因sty文件名删除包的大小写不敏感问题
    # 把报错的cite都注释掉就可以跑了，其实是要把cite...改成正规的cite或citep这种格式

    # ------------------------------
    # 结论：目前还不支持ICML

    # 测试 8:
    # your_work_folder = './ECCV 2016'
    # target_template_folder = './ICML 2021'

    # 这个ICML不是按照title，author，maketitle来写的
    # 逻辑：如果目标模板没有找到\title,\author,\maketitle，就先把\author,title,maketitle给注释掉，\make{document}前面的东西贴到最前面，把\make{document}后面的东西贴到\make{document}之后，然后title之类的要手动改

    # 如果自己没有maketitle，...




    # ------------------------------

    # converted_result文件夹中的内容就是修改格式完成后的结果
    # 如果你的电脑安装了模糊编译latex文件的插件，此时在converted_result中的pdf文件就是修改完的tex文件编译后的pdf
    # 如果没有自动生成pdf文件，请使用你的模糊编译latex文件的插件再次对tex文件进行编译
    # 如果有红色错误，请把红色的部分给注释掉，再跑就能成功跑起来了




