import os
from flask import Flask, request, render_template, send_file, url_for
from werkzeug.utils import secure_filename
import fitz

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 

def is_valid_extension(filename, valid_extensions):
    return any(filename.lower().endswith(ext) for ext in valid_extensions)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", download_link=None)

@app.route("/convert", methods=["POST"])
def convert():
    file = request.files.get("file")

    if not file:
        return "Erro: Arquivo não selecionado.", 400

    input_filename = secure_filename(file.filename)
    if not is_valid_extension(input_filename, [".pdf"]):
        return "Erro: O arquivo enviado deve ser um PDF.", 400

    input_path = os.path.join(app.config["UPLOAD_FOLDER"], input_filename)
    file.save(input_path)

    if not os.path.exists(input_path):
        return "Erro: Arquivo não salvo corretamente.", 400

    output_folder = os.path.join(app.config["UPLOAD_FOLDER"], os.path.splitext(input_filename)[0])
    os.makedirs(output_folder, exist_ok=True)

    output_format = request.form.get("outputFormat", "PNG").upper()

    if output_format not in ["PNG", "JPG"]:
        return "Erro: Formato inválido. Apenas PNG e JPG são suportados.", 400

    try:
        convert_pdf_to_images(input_path, output_folder, output_format)
    except Exception:
        return "Erro ao converter o PDF.", 500

    output_folder_name = os.path.basename(output_folder)
    download_link = url_for("download_folder", folder=output_folder_name)
    return render_template("index.html", download_link=download_link)

@app.route("/download/<folder>")
def download_folder(folder):
    folder_path = os.path.join(app.config["UPLOAD_FOLDER"], folder)
    if not os.path.exists(folder_path):
        return "Erro: Pasta não encontrada.", 404

    zip_path = f"{folder_path}.zip"
    if not os.path.exists(zip_path):
        import shutil
        shutil.make_archive(folder_path, 'zip', folder_path)

    return send_file(zip_path, as_attachment=True)

def convert_pdf_to_images(input_path, output_folder, output_format):
    try:
        pdf_document = fitz.open(input_path)
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap()

            output_file = os.path.join(output_folder, f"page_{page_number + 1}.{output_format.lower()}")
            pix.save(output_file)
        pdf_document.close()
    except Exception as e:
        raise Exception(f"Erro ao converter PDF para imagens: {str(e)}")

if __name__ == "_main_":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
