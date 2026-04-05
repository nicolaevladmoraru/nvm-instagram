from flask import Blueprint, jsonify, request

from cloudinary_service import upload_image
from image_alerts import build_alert_image
from instagram_api import post_to_instagram

alerts_bp = Blueprint("alerts_bp", __name__)


def build_manual_tiktok_caption(
    league: str,
    home: str,
    away: str,
    minute: str,
    score: str,
) -> str:
    parts = [
        f"{home} vs {away}",
        f"{league}",
        f"Minute: {minute or 'Live now'}",
        f"Score: {score or 'Match in play'}",
        "",
        "@nvm_access_engine_bot",
    ]
    return "\n".join(parts).strip()


@alerts_bp.route("/preview-alert", methods=["POST"])
def preview_alert():
    try:
        data = request.get_json(force=True) or {}

        league = data.get("league", data.get("league_key", ""))
        home = data.get("home", data.get("home_team", ""))
        away = data.get("away", data.get("away_team", ""))
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", data.get("pick_text", ""))

        home_logo_url = data.get("home_logo_url", data.get("home_logo", ""))
        away_logo_url = data.get("away_logo_url", data.get("away_logo", ""))

        image_path = build_alert_image(
            league=league,
            home=home,
            away=away,
            minute=minute,
            score=score,
            pick=pick,
            home_logo_url=home_logo_url,
            away_logo_url=away_logo_url,
            include_pick=True,
        )

        image_url = upload_image(image_path)

        return jsonify({
            "ok": True,
            "preview_only": True,
            "image_url": image_url
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@alerts_bp.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        league = data.get("league", data.get("league_key", ""))
        home = data.get("home", data.get("home_team", ""))
        away = data.get("away", data.get("away_team", ""))
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", data.get("pick_text", ""))
        caption = data.get("caption_message", "")

        home_logo_url = data.get("home_logo_url", data.get("home_logo", ""))
        away_logo_url = data.get("away_logo_url", data.get("away_logo", ""))

        if not caption:
            caption = (
                f"{league}\n"
                f"{home} vs {away}\n\n"
                f"Minute: {minute}\n"
                f"Score: {score}\n"
                f"Pick: {pick}\n\n"
                f"@nvm_access_engine_bot"
            )

        instagram_image_path = build_alert_image(
            league=league,
            home=home,
            away=away,
            minute=minute,
            score=score,
            pick=pick,
            home_logo_url=home_logo_url,
            away_logo_url=away_logo_url,
            include_pick=True,
        )
        instagram_image_url = upload_image(instagram_image_path)
        instagram_result = post_to_instagram(instagram_image_url, caption)

        telegram_image_path = build_alert_image(
            league=league,
            home=home,
            away=away,
            minute=minute,
            score=score,
            pick="",
            home_logo_url=home_logo_url,
            away_logo_url=away_logo_url,
            include_pick=False,
        )
        telegram_image_url = upload_image(telegram_image_path)

        telegram_caption = build_manual_tiktok_caption(
            league=str(league or "").strip(),
            home=str(home or "").strip(),
            away=str(away or "").strip(),
            minute=str(minute or "").strip(),
            score=str(score or "").strip(),
        )

        return jsonify({
            "ok": True,
            "image_url": instagram_image_url,
            "telegram_image_url": telegram_image_url,
            "telegram_caption": telegram_caption,
            "result": instagram_result
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
