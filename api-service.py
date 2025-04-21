import fastapi
import uvicorn
import os
import zipfile
import tempfile
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List

try:
    from main import process_latex_files
except ImportError:
    logging.error("Error: Could not import 'process_latex_files' from main.py.")
    logging.error("Make sure main.py is in the same directory or accessible.")
    def process_latex_files(*args, **kwargs):
        raise RuntimeError("process_latex_files function not loaded.")

TEMPLATE_FOLDER = "./templates"
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="LaTeX Template Converter API",
    description="API to convert LaTeX projects using predefined templates.",
)

def detect_main_tex(directory):
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith('.tex'):
                with open(os.path.join(root, f)) as tex_file:
                    if r'\documentclass' in tex_file.read():
                        return os.path.relpath(os.path.join(root, f), directory)
    return None

@app.get(
    "/api/v1/templates",
    summary="Get Available Templates",
    description="Returns a list of available LaTeX templates.",
    response_description="A list of available LaTeX template names."
)
def get_available_templates() -> List[str]:
    """Gets available template names (without .zip extension)"""
    try:
        return [
            os.path.splitext(f)[0]
            for f in os.listdir(TEMPLATE_FOLDER)
            if f.endswith('.zip') and os.path.isfile(os.path.join(TEMPLATE_FOLDER, f))
        ]
    except FileNotFoundError:
        logging.warning(f"Template folder '{TEMPLATE_FOLDER}' not found.")
        return []
    except Exception as e:
        logging.error(f"Error listing templates: {e}")
        return []

def extract_zip(zip_file_path: str, target_dir: str):
    """Extracts ZIP file to a target directory, removing __MACOSX."""
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(target_dir)

        macosx_folder = os.path.join(target_dir, '__MACOSX')
        if os.path.exists(macosx_folder) and os.path.isdir(macosx_folder):
            logging.info(f"Removing __MACOSX folder from {target_dir}")
            shutil.rmtree(macosx_folder)

        extracted_items = os.listdir(target_dir)
        if len(extracted_items) == 1:
            potential_subdir = os.path.join(target_dir, extracted_items[0])
            if os.path.isdir(potential_subdir):
                logging.info(f"Moving contents up from nested folder: {potential_subdir}")
                for item in os.listdir(potential_subdir):
                    shutil.move(os.path.join(potential_subdir, item), target_dir)
                os.rmdir(potential_subdir)

    except zipfile.BadZipFile:
        logging.error(f"Error: Bad zip file: {zip_file_path}")
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted ZIP file provided: {os.path.basename(zip_file_path)}")
    except Exception as e:
        logging.error(f"Error extracting zip {zip_file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract ZIP file: {os.path.basename(zip_file_path)}")


def get_tex_files_from_dir(directory: str) -> List[str]:
    """Finds all .tex files relative to the given directory."""
    tex_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".tex"):
                    relative_path = os.path.relpath(os.path.join(root, file), directory)
                    tex_files.append(relative_path)
        return tex_files
    except Exception as e:
        logging.error(f"Error scanning for .tex files in {directory}: {e}")
        return []

def cleanup_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logging.info(f"Background task: Successfully removed temporary file: {path}")
        else:
            logging.warning(f"Background task: File not found or already removed: {path}")
    except Exception as e:
        logging.error(f"Background task: Error removing file {path}: {e}")

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

@app.post(
    "/api/v1/upload",
    summary="Upload LaTeX Project",
    description="Upload a LaTeX project as a ZIP file. Returns the list of .tex files in the project.",
)
async def upload_latex_project(
    template: UploadFile = File(..., description="LaTeX template ZIP file."),
    template_name: str = Form(..., description="Name for the template (without .zip extension)."),
    main_tex: str = Form(..., description="Name of the main .tex file in the template (e.g., 'main.tex')."),
    recommended_compile: str = Form(..., description="Recommended compile method for the template.")
):
    logging.info(f"Received template upload request: '{template_name}'")
    
    # Check if template name is already used
    available_templates = get_available_templates()
    if template_name in available_templates:
        raise HTTPException(status_code=400, detail=f"Template name '{template_name}' already exists. Please choose a different name.")
    
    # Validate the file is a zip
    if not template.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a ZIP file.")
    
    # Validate main_tex path safety
    if main_tex and (os.path.isabs(main_tex) or '..' in main_tex):
        raise HTTPException(400, detail="Main tex path contains invalid characters.")
    
    temp_dir = None
    template_zip_path = None
    
    try:
        # Save the uploaded zip temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            shutil.copyfileobj(template.file, temp_file)
            template_zip_path = temp_file.name
        
        # Extract to check contents
        temp_dir = tempfile.mkdtemp()
        extract_zip(template_zip_path, temp_dir)
        
        # Verify the main tex file exists
        tex_files = get_tex_files_from_dir(temp_dir)
        if not tex_files:
            raise HTTPException(status_code=400, detail="No .tex files found in the uploaded template.")
        
        if main_tex not in tex_files:
            raise HTTPException(
                status_code=400, 
                detail=f"Specified main_tex file '{main_tex}' not found in the template. Available .tex files: {', '.join(tex_files)}"
            )
            
        # Save the template to the templates folder
        full_template_name = f"{template_name}.zip"
        template_path = os.path.join(TEMPLATE_FOLDER, full_template_name)
        shutil.copy(template_zip_path, template_path)
        
        # Update the targetTemplateMainTexMapping.py file
        mapping_file = "targetTemplateMainTexMapping.py"
        if os.path.exists(mapping_file):
            add_template_to_mapping(mapping_file, full_template_name, main_tex)
            
        # Update the targetTemplateRecCompileMapping.py file
        compile_mapping_file = "targetTemplateRecCompileMapping.py"
        if os.path.exists(compile_mapping_file):
            add_template_to_mapping(compile_mapping_file, full_template_name, recommended_compile)
            
        return {
            "status": "success",
            "message": f"Template '{template_name}' uploaded successfully",
            "template_name": template_name,
            "main_tex": main_tex,
            "recommended_compile": recommended_compile
        }
        
    except Exception as e:
        logging.error(f"Error processing template upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading template: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        if template_zip_path and os.path.exists(template_zip_path):
            os.remove(template_zip_path)


@app.post(
    "/api/v1/convert",
    summary="Convert LaTeX Source to Target Template",
    description="Upload a source LaTeX project zip, select a target template, "
                "and optionally specify the main .tex file. Returns the converted project as a zip.",
    response_description="A ZIP file containing the converted LaTeX project."
)
async def convert_latex_endpoint(
    background_tasks: BackgroundTasks,
    source: UploadFile = File(..., description="Source LaTeX project as a ZIP file."),
    template_name: str = Form(..., description="Name of the target template (e.g., 'templateA', without .zip)."),
    main_tex: Optional[str] = Form(None, description="Optional: Name of the main .tex file in the source zip (e.g., 'main.tex', 'document.tex'). If not provided, attempts to auto-detect.")
):
    logging.info(f"Received conversion request for template: '{template_name}'")
    # 添加路径安全检验
    if main_tex and (os.path.isabs(main_tex) or '..' in main_tex):
        raise HTTPException(400, "Main tex path contains invalid characters")
    
    available_templates = get_available_templates()
    if template_name not in available_templates:
        logging.error(f"Template '{template_name}' not found. Available: {available_templates}")
        raise HTTPException(
            status_code=404,
            detail=f"Target template '{template_name}' not found. Available templates: {', '.join(available_templates)}"
        )
    template_zip_name = f"{template_name}.zip"
    template_zip_path = os.path.join(TEMPLATE_FOLDER, template_zip_name)
    if not os.path.exists(template_zip_path):
        raise HTTPException(404, f"Template {template_name} not found")
    logging.info(f"Using template file: {template_zip_path}")

    source_temp_dir = None
    output_zip_path = None
    source_zip_temp_file = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            shutil.copyfileobj(source.file, temp_file)
            source_zip_temp_file = temp_file.name
        logging.info(f"Source ZIP saved temporarily to: {source_zip_temp_file}")

        if not main_tex:
            logging.info("Main TeX file not specified, attempting auto-detection.")
            source_temp_dir = tempfile.mkdtemp()
            try: # 添加 try...finally 来确保 source_temp_dir 在出错时也能清理
                extract_zip(source_zip_temp_file, source_temp_dir)
                tex_files = get_tex_files_from_dir(source_temp_dir)

                if not tex_files:
                    logging.error("No .tex files found in the uploaded source zip.")
                    raise HTTPException(status_code=400, detail="No .tex files found in the source ZIP.")
                elif len(tex_files) == 1:
                    main_tex = tex_files[0]
                    logging.info(f"Auto-detected single main TeX file: {main_tex}")
                else:
                    main_tex = detect_main_tex(source_temp_dir)
                    if main_tex:
                        logging.info(f"Auto-detected main TeX file: {main_tex}")
                    else:
                        logging.error(f"Multiple .tex files found, main_tex needs to be specified: {tex_files}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Multiple .tex files found ({', '.join(tex_files)}). Please specify the main file using the 'main_tex' parameter."
                        )
            finally:
                if source_temp_dir and os.path.exists(source_temp_dir):
                    logging.info(f"Removing temporary extraction directory: {source_temp_dir}")
                    shutil.rmtree(source_temp_dir)
                    source_temp_dir = None # 标记为已清理
        else:
             logging.info(f"Using specified main TeX file: {main_tex}")


        logging.info(f"Calling process_latex_files with source='{source_zip_temp_file}', template='{template_zip_path}', main='{main_tex}'")

        output_zip_path = process_latex_files(
            source_zip=source_zip_temp_file,
            template_zip=template_zip_path,
            main_tex_file=main_tex,
            selected_template=template_zip_name # 注意：这里之前是 template_zip_name，确认是否正确
        )

        if not output_zip_path or not os.path.exists(output_zip_path):
             logging.error("process_latex_files did not return a valid output path.")
             raise HTTPException(status_code=500, detail="Conversion process failed to produce an output file.")

        logging.info(f"Conversion successful. Output ZIP: {output_zip_path}")

        download_filename = f"converted_{source.filename.replace('.zip', '')}_using_{template_name}.zip"

        # 添加后台任务来删除 output_zip_path
        background_tasks.add_task(cleanup_file, output_zip_path)

        return FileResponse(
            path=output_zip_path,
            media_type='application/zip',
            filename=download_filename,
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}",
                "X-Conversion-Status": "success"
            }
            # 注意：FileResponse 自身也有 background 参数，但使用注入的 background_tasks 更灵活
            # background=BackgroundTask(cleanup_file, path=output_zip_path) # 另一种方式
        )

    except HTTPException as e:
        # 如果 output_zip_path 在异常发生前已生成，也需要清理
        if output_zip_path and os.path.exists(output_zip_path):
             cleanup_file(output_zip_path) # 直接清理，因为不会返回 FileResponse
        raise e
    except Exception as e:
        logging.exception("An unexpected error occurred during conversion.")
        # 如果 output_zip_path 在异常发生前已生成，也需要清理
        if output_zip_path and os.path.exists(output_zip_path):
             cleanup_file(output_zip_path) # 直接清理
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
    finally:
        logging.info("Starting final cleanup (source files)...")
        # 清理临时的源 zip 文件
        if source_zip_temp_file and os.path.exists(source_zip_temp_file):
            logging.info(f"Removing temporary source zip: {source_zip_temp_file}")
            os.remove(source_zip_temp_file)
        # 确保临时的解压目录也被清理 (如果之前没有清理)
        if source_temp_dir and os.path.exists(source_temp_dir):
             logging.info(f"Removing temporary extraction directory (final check): {source_temp_dir}")
             shutil.rmtree(source_temp_dir)
        # 注意：output_zip_path 的清理现在由后台任务处理，不再需要在 finally 中处理

        logging.info("Final cleanup finished.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=12345)
