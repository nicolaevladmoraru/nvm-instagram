@app.route("/debug-env", methods=["GET"])
def debug_env():
    token = IG_ACCESS_TOKEN or ""
    return jsonify({
        "ig_user_id": IG_USER_ID,
        "token_prefix": token[:8],
        "token_length": len(token)
    })
