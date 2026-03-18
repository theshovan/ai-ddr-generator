import io
import json
from flask import Blueprint, request, jsonify, send_file
from config import GROQ_API_KEY
from services.extractor import extract
from services.ai import generate_ddr
from services.pdf_builder import build

bp = Blueprint("generate", __name__)


@bp.route("/generate", methods=["POST"])
def generate():
    if not GROQ_API_KEY:
        return jsonify({"error": "GROQ_API_KEY not set in .env"}), 500

    insp_file  = request.files.get("inspection_report")
    therm_file = request.files.get("thermal_report")

    if not insp_file or not therm_file:
        return jsonify({"error": "Both inspection_report and thermal_report are required"}), 400

    try:
        insp_text,  insp_imgs  = extract(insp_file.read(),  "inspection")
        therm_text, therm_imgs = extract(therm_file.read(), "thermal")

        ddr       = generate_ddr(insp_text, therm_text)
        pdf_bytes = build(ddr, insp_imgs + therm_imgs)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=False,
            download_name="DDR_Report.pdf",
        )

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI returned malformed JSON: {e}"}), 500
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500
