# LaTeX-template-converter

Convert your LaTeX academic article to a different journal article template

将你的 LaTeX 文章快速更改为另一种期刊格式

## Usage:

Replace the following two folder paths with the folder of your LaTeX article and the target template folder:

- `your_work_folder = './CVPR 2022'`
- `target_template_folder = './ECCV 2016'`

After running the Python code, the contents of the `converted_result` folder will contain the formatted output.

After running the Python code, the contents in the `converted_result` folder will be the result of the format modification.

Open the `.tex` file in the `converted_result` folder for compilation. Comment out all the red error sections, then delete the `.bbl` file. Finally, compile the `.tex` file twice to obtain the desired `.pdf`.

---

## 使用方法：

将以下两个文件夹路径替换为你自己 LaTeX 文章的文件夹和目标模板文件夹：

- `your_work_folder = './CVPR 2022'`
- `target_template_folder = './ECCV 2016'`

运行 Python 代码后，`converted_result` 文件夹中的内容将是格式修改后的结果。

打开 `converted_result` 文件夹中的 `.tex` 文件进行编译，注释掉所有红色错误部分后，删除`.bbl`文件，再编译两次 `.tex` 文件，即能得到你想要的`.pdf`。

---

## 以下是针对模板 **CVPR2022**，**ECCV2016**，**NeurIPS2024** 模板做出的补丁修改：

### Bug 1:

`\begin{document}` 前加入 `\usepackage[OT1]{fontenc}`

```python
add_fontenc_package(yourwork_main_tex)
```

### Bug 2:

使用 `subfigure` 时会报错

在 `\begin{document}` 之前插入 `\usepackage{subcaption}`

```python
add_subcaption_package_before_document(yourwork_main_tex)
```

### Bug 3:

当一个文档出现两次 `hyperref` 包时会报错

出现两次 `\usepackage{hyperref}`，删掉后一个 `\usepackage{hyperref}`

```python
remove_second_hyperref(yourwork_main_tex)
```

更新：
因为有些 `hyperref` 是自带在 `.sty` 中的，所以这个方法并不合理。手动注释掉报错的 `hyperref` 就可以了。

### Bug 4:

`\author{...}` 中有换行，会报错，添加以下行在 `\begin{document}` 之前：

注意：如果你的\author没有涉及到换行，因为添加了这些tex代码，会报错说你没有用到它，你可以自行删去。保留它不会影响你的编译

```tex
\pdfstringdefDisableCommands{%
  \def\\{}%
  \def\texttt#1{<#1>}%
}
```

add_pdfstringdef_before_document(yourwork_main_tex)



### Bug 5:

当出现 `\eg` 等在原 `.sty` 文件中的定义时出现 bug，加入：

```tex
\def\onedot{.}  % 定义 \onedot 为句点
% 定义缩写命令
\def\eg{\emph{e.g}\onedot} 
\def\Eg{\emph{E.g}\onedot}
\def\ie{\emph{i.e}\onedot} 
\def\Ie{\emph{I.e}\onedot}
\def\cf{\emph{cf}\onedot} 
\def\Cf{\emph{Cf}\onedot}
\def\etc{\emph{etc}\onedot} 
\def\vs{\emph{vs}\onedot}
\def\wrt{w.r.t\onedot} 
\def\dof{d.o.f\onedot}
\def\iid{i.i.d\onedot} 
\def\wolog{w.l.o.g\onedot}
\def\etal{\emph{et al}\onedot}
```

```python
add_custom_macros_before_document(yourwork_main_tex)
```



### Bug 6:

（已完成，在 `.sty` 改动函数中已修改）`sty` 包受到大小写影响，比如 `emnlp2023.sty`，要删掉 `\usepackage[review]{EMNLP2023}`，因为大写所以没删成功。



### Bug 7:

（已完成，在 `.bib` 改动函数中已修改）若被修改的latex文件夹中不包含`.bib`文件，会自动新建一个新的`yourbib.bib`文件并引用目标模板的引用格式，以供用户放入bibtex参考文献。由于空的`.bib`文件会在tex文件中报错：“没有检测到任何引用”，故而在新建的.bib文件中添加了参考引用，并在文章末尾加入了一句标注应删去的引用语句。

------

## 未完成的 bug 修改:

### Bug 1:

改到 NeurIPS 2024 模板要把 bibstyle 改成 `\bibliographystyle{rusnat}`，或者其他 natbib 兼容且NeurIPS接受的格式。

### Bug 2:

bib 的 `\cite` 错误，解决方法：

法一：删掉 `.bbl` 文件，进入 `.bib` 文件保存一下，再到 `.tex` 中编译。

法二：删掉所有红色错误，多编译几次文件。

法三：编译顺序选择为：xlatex *2 -> bibtex -> xlatex 或者 pdflatex *2 -> bibtex -> pdflatex。如果你用的是 VS Code，即点击`fn + Command + P`，搜索latex workshop: build with recipe，选择上述编译顺序。

---

# 测试日志：

## 测试 1:
- `your_work_folder = './NeurIPS 2024'`
- `target_template_folder = './ECCV 2016'`
- `\ack` 环境未定义，删了就行

## 测试 2:
- `your_work_folder = './ECCV 2016'`
- `target_template_folder = './NeurIPS 2024'`
- 删掉 `institute`、`keyword`
- 改成 `\bibliographystyle{rusnat}`

## 测试 3:
- `your_work_folder = './ECCV 2016'`
- `target_template_folder = './CVPR 2022'`
- （已完成）`\begin{document}` 前加入 `\usepackage[OT1]{fontenc}`
- （已完成）复制 `.bst` 文件过来

## 测试 4:
- `your_work_folder = './CVPR 2022'`
- `target_template_folder = './ECCV 2016'`
- （已完成）删除原本的 `.sty` 文件
- （已完成）`subfigure` 出现 bug，加入 `\usepackage{subcaption}`
- （已完成）`\eg` 等出现 bug，加入 `\def`

## 测试 5:
- `your_work_folder = './NeurIPS 2024'`
- `target_template_folder = './CVPR 2022'`
- `ack` 的问题

## 测试 6:
- `your_work_folder = './CVPR 2022'`
- `target_template_folder = './NeurIPS 2024'`
- （已完成）删除后一个 `hyperref`
- 改成 `\bibliographystyle{rusnat}`
- bib 的格式错误，进入 `.bib` 文件保存一下，再到 `.tex` 中编译就可以了

## 测试 7:
- `your_work_folder = './CVPR 2022'`
- `target_template_folder = './EMNLP 2023'`
- 删掉 `hyperref` 和 `\pdfoutput=1`
- 删掉 `.bbl`，到 `.bib` 保存再跑

## 测试 8:
- `your_work_folder = './EMNLP 2023'`
- `target_template_folder = './CVPR 2022'`
- （已完成）修改因 `.sty` 文件名删除包的大小写不敏感问题
- 把报错的 `cite` 都注释掉就可以跑了，其实是要把 `cite...` 改成正规的 `cite` 或 `citep` 这种格式

