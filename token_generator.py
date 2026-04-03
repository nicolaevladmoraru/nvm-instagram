import requests

# ==========================================
# 🔐 CONFIG - COMPLETEAZĂ AICI
# ==========================================
APP_ID = "3092322464294174"
APP_SECRET = "42640607ec37f4f45a546fe40c0ba58f"
SHORT_LIVED_TOKEN = "EAAr8c24D5R4BRM8rDIofPtcnLoBtxTeC70Dvbf9ZA08YQTspi7lWeSPtS1YjQGtvuHL1Afe4bG1b0RW1Er8U3rZBbeHX10Qdr9k7wf5UAAR2c1qReyzqXEB1GqLXUMoFutnnuZCIpVEkeBfhWZCkN4mo420i7efUR6No8sdEAJCPven3HSxHqYj7LuqI4pkAMLB8Cq8iZBzG7w49mrVr0LZC1zojZB5D9FOtYwKe7wBI4vapjI2ZCbx7HMfZBZB0fYdPJPvGZAHkz5nE9JQqsKT91BN"

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
