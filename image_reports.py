from image_daily import build_daily_report
from image_weekly import build_weekly_image
from image_monthly import build_monthly_image
from image_milestone import build_milestone_image


def build_report_image(report_type, title, date_text, wins, lost, winrate):
    report_type = str(report_type or "").strip().lower()

    if report_type == "daily":
        return build_daily_report(
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
    elif report_type == "weekly":
        return build_weekly_image(
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
    elif report_type == "monthly":
        return build_monthly_image(
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
    elif report_type == "milestone":
        return build_milestone_image(
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )
    else:
        raise ValueError(f"Unsupported report_type: {report_type}")
