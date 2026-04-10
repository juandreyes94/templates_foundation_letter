"""
Document Generation Service
Generates Word documents from a template by replacing placeholders.
Deploy on Google Cloud Run - up to 2M free calls/month.
"""

import os
import io
import re
import zipfile
import shutil
import tempfile
from flask import Flask, request, jsonify, send_file
from datetime import datetime

app = Flask(__name__)

# Path to the template file (bundled with the container)
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.docx")

# All supported placeholders in the template
PLACEHOLDERS = [
    "date_format_july22-2025",
    "client_name",
    "Address_1",
    "Address_2",
    "Zip_code",
    "subdivision",
    "Project_Address",
    "Block",
    "Lot",
    "City",
    "print_date",
    "print_date_2",
    "IRC",
    "Soils_report_source",
    "Soils_report_number",
    "Soils_report_date_formatted_july9-2024",
]


def replace_in_xml(xml_content: str, replacements: dict) -> str:
    """Replace {placeholder} values, handling Word's XML run fragmentation."""
    for key, value in replacements.items():
        replacement = str(value) if value is not None else ""
        placeholder = "{" + key + "}"
        # Try simple replace first (fastest path)
        if placeholder in xml_content:
            xml_content = xml_content.replace(placeholder, replacement)
        else:
            # Word sometimes splits placeholders across multiple XML runs.
            # Build a regex that matches each character with optional XML tags between them.
            pattern = "".join(re.escape(c) + r"(?:<[^>]+>)*" for c in placeholder)
            xml_content = re.sub(pattern, replacement.replace("\\", "\\\\"), xml_content)
    return xml_content


def generate_document(data: dict) -> bytes:
    """
    Takes a dict of field values, fills the template, and returns
    the generated .docx file as bytes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy template to temp dir
        tmp_docx = os.path.join(tmpdir, "output.docx")
        shutil.copy2(TEMPLATE_PATH, tmp_docx)

        # .docx is a ZIP — open it, patch the XML files, repack
        output_buffer = io.BytesIO()

        with zipfile.ZipFile(tmp_docx, "r") as zin:
            with zipfile.ZipFile(output_buffer, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    content = zin.read(item.filename)

                    # Only process XML files (text-based)
                    if item.filename.endswith(".xml") or item.filename.endswith(".rels"):
                        try:
                            text = content.decode("utf-8")
                            text = replace_in_xml(text, data)
                            content = text.encode("utf-8")
                        except UnicodeDecodeError:
                            pass  # Binary file — keep as-is (images, etc.)

                    zout.writestr(item, content)

        output_buffer.seek(0)
        return output_buffer.read()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "template": os.path.exists(TEMPLATE_PATH)})


@app.route("/generate", methods=["POST"])
def generate():
    """
    Main endpoint. Accepts JSON body with field values.
    Returns the filled .docx file as a download.

    Expected JSON body (all fields optional — missing = left blank):
    {
        "date_format_july22-2025": "July 22, 2025",
        "client_name": "John Smith",
        "Address_1": "123 Main St",
        "Address_2": "Suite 100",
        "Zip_code": "78701",
        "subdivision": "Oak Creek Estates",
        "Project_Address": "456 Oak Lane",
        "Block": "12",
        "Lot": "34",
        "City": "Austin",
        "print_date": "July 22, 2025",
        "print_date_2": "July 22, 2025",
        "IRC": "2021",
        "Soils_report_source": "Geotech Labs",
        "Soils_report_number": "GT-2024-0099",
        "Soils_report_date_formatted_july9-2024": "July 9, 2024",
        "filename": "contract_john_smith.docx"
    }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Build replacement map — use empty string for missing fields
    replacements = {key: data.get(key, "") for key in PLACEHOLDERS}

    try:
        doc_bytes = generate_document(replacements)
    except Exception as e:
        return jsonify({"error": f"Document generation failed: {str(e)}"}), 500

    # Determine output filename
    filename = data.get("filename") or f"document_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
    if not filename.endswith(".docx"):
        filename += ".docx"

    return send_file(
        io.BytesIO(doc_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/fields", methods=["GET"])
def fields():
    """Returns the list of all supported placeholder fields."""
    return jsonify({"fields": PLACEHOLDERS})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
