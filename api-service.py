# api_service.py

import fastapi
import uvicorn
import os
import zipfile
import tempfile
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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



@app.post(
    "/convert/",
    summary="Convert LaTeX Source to Target Template",
    description="Upload a source LaTeX project zip, select a target template, "
                "and optionally specify the main .tex file. Returns the converted project as a zip.",
    response_description="A ZIP file containing the converted LaTeX project."
)
async def convert_latex_endpoint(
    source: UploadFile = File(..., description="Source LaTeX project as a ZIP file."),
    template_name: str = Form(..., description="Name of the target template (e.g., 'templateA', without .zip)."),
    main_tex: Optional[str] = Form(None, description="Optional: Name of the main .tex file in the source zip (e.g., 'main.tex', 'document.tex'). If not provided, attempts to auto-detect.")
):
    """
    Handles the LaTeX conversion request.
    """
    logging.info(f"Received conversion request for template: '{template_name}'")

    available_templates = get_available_templates()
    if template_name not in available_templates:
        logging.error(f"Template '{template_name}' not found. Available: {available_templates}")
        raise HTTPException(
            status_code=404,
            detail=f"Target template '{template_name}' not found. Available templates: {', '.join(available_templates)}"
        )
    template_zip_name = f"{template_name}.zip"
    template_zip_path = os.path.join(TEMPLATE_FOLDER, template_zip_name)
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
            extract_zip(source_zip_temp_file, source_temp_dir)
            tex_files = get_tex_files_from_dir(source_temp_dir)

            if not tex_files:
                logging.error("No .tex files found in the uploaded source zip.")
                raise HTTPException(status_code=400, detail="No .tex files found in the source ZIP.")
            elif len(tex_files) == 1:
                main_tex = tex_files[0]
                logging.info(f"Auto-detected single main TeX file: {main_tex}")
            else:
                logging.error(f"Multiple .tex files found, main_tex needs to be specified: {tex_files}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Multiple .tex files found ({', '.join(tex_files)}). Please specify the main file using the 'main_tex' parameter."
                )
        else:
             logging.info(f"Using specified main TeX file: {main_tex}")


        logging.info(f"Calling process_latex_files with source='{source_zip_temp_file}', template='{template_zip_path}', main='{main_tex}'")

        output_zip_path = process_latex_files(
            source_zip=source_zip_temp_file,
            template_zip=template_zip_path,
            main_tex_file=main_tex,
            selected_template=template_zip_name
        )

        if not output_zip_path or not os.path.exists(output_zip_path):
             logging.error("process_latex_files did not return a valid output path.")
             raise HTTPException(status_code=500, detail="Conversion process failed to produce an output file.")

        logging.info(f"Conversion successful. Output ZIP: {output_zip_path}")

        download_filename = f"converted_{source.filename.replace('.zip', '')}_using_{template_name}.zip"

        return FileResponse(
            path=output_zip_path,
            media_type='application/zip',
            filename=download_filename
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception("An unexpected error occurred during conversion.") # Log full traceback
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
    finally:
        logging.info("Starting cleanup...")
        if source_zip_temp_file and os.path.exists(source_zip_temp_file):
            logging.info(f"Removing temporary source zip: {source_zip_temp_file}")
            os.remove(source_zip_temp_file)
        if source_temp_dir and os.path.exists(source_temp_dir):
             logging.info(f"Removing temporary extraction directory: {source_temp_dir}")
             shutil.rmtree(source_temp_dir)

        logging.info("Cleanup finished.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=12345)
