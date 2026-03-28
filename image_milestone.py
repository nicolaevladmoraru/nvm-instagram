from image_daily import build_daily_image


def build_milestone_image(title, date_text, wins, lost, winrate):
    return build_daily_image(title, date_text, wins, lost, winrate)
