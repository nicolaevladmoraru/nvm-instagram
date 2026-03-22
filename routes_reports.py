from flask import Blueprint, jsonify, request

from cloudinary_service import upload_image
from image_reports import build_report_image
from instagram_api import post_to_instagram

reports_bp = Blueprint("reports_bp", __name__)


@reports_bp.route("/preview-report", methods=["POST"])
def preview_report():
    try:
        data = request.get_json(force=True) or {}

        report_type = str(data.get("report_type", "daily"))
        title = str(data.get("title", "NVM REPORT"))
        date_text = str(data.get("date_text", ""))
        wins = str(data.get("wins", "0"))
        lost = str(data.get("lost", "0"))
        winrate = str(data.get("winrate", "0%"))

        image_path = build_report_image(
            report_type=report_type,
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
        image_url = upload_image(image_path)

        return jsonify({
            "ok": True,
            "preview_only": True,
            "image_url": image_url
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@reports_bp.route("/post-report", methods=["POST"])
def post_report():
    try:
        data = request.get_json(force=True) or {}

        report_type = str(data.get("report_type", "daily"))
        title = str(data.get("title", "NVM REPORT"))
        date_text = str(data.get("date_text", ""))
        wins = str(data.get("wins", "0"))
        lost = str(data.get("lost", "0"))
        winrate = str(data.get("winrate", "0%"))
        caption = str(data.get("caption_message", "")).strip()

        if not caption:
            caption = (
                f"{title}\n"
                f"{date_text}\n\n"
                f"Wins: {wins}\n"
                f"Lost: {lost}\n"
                f"Win Rate: {winrate}\n\n"
                f"@nvm_access_engine_bot"
            )

        image_path = build_report_image(
            report_type=report_type,
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
        image_url = upload_image(image_path)
        result = post_to_instagram(image_url, caption)

        return jsonify({
            "ok": True,
            "image_url": image_url,
            "result": result
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
