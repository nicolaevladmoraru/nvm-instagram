import requests

# ==========================================
# 🔐 CONFIG - COMPLETEAZĂ AICI
# ==========================================
APP_ID = "3092322464294174"
APP_SECRET = "42640607ec37f4f45a546fe40c0ba58f"
SHORT_LIVED_TOKEN = "EAAr8c24D5R4BRNOczvCsKYVpuHr2c8r3uV7r6CEeFfBCXfLze0b4euHGpOvpI4KalFklGn1wwlo992ffLtjuDQ2XuQKhwyU6scxGO9b8InSKuwK7eBisD55ZAogOkhZAn8Urthak51cRk6sFuunve5ZAWEyQg7VSTdnrZCUymrVf2ZBVF85OunVwRSd2N0uFo"

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
