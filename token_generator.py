import requests

# ==========================================
# 🔐 CONFIG - COMPLETEAZĂ AICI
# ==========================================
APP_ID = "1315986937007707"
APP_SECRET = "528056121ac7931a21ebc268c8947293"
SHORT_LIVED_TOKEN = "EAAr8c24D5R4BRIzCVdBmDmrFFg3QREPsZAqii29FAFz5JtAGcuYGml6VI8G1xTMPypnLFQUHSzKQ4O6Q2PdNLDEZCdFjZCoOf0qIelEC2lhk6QWKtVO2oDampzZCaGZCg35gbYaQRUH3IrWRA9v3dVOolkwLFhhoBzi13DSNJEWPPE2M9UeiyZCMQjnjpkCcQpMUZBDz8pN3m1KNiiEfIfOhU1qOQjaEIrQVT4Qq2I9B9NA0ZCIzOMLcK45qrZCLG2aipIThmjMZCqwmZCseUkcUO8LKAZDZD"

# ==========================================
# 🔄 EXCHANGE TOKEN -> 60 DAYS TOKEN
# ==========================================
url = "https://graph.facebook.com/v19.0/oauth/access_token"

params = {
    "grant_type": "fb_exchange_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "fb_exchange_token": SHORT_LIVED_TOKEN,
}

try:
    response = requests.get(url, params=params, timeout=30)

    print("Status:", response.status_code)
    print("Response:", response.text)

    data = response.json()

    if "access_token" in data:
        print("\n✅ LONG-LIVED TOKEN (60 DAYS):\n")
        print(data["access_token"])
        print("\n⏳ Expires in (seconds):", data.get("expires_in"))
    else:
        print("\n❌ ERROR generating token.")

except Exception as e:
    print("Exception:", str(e))
