import requests
import os

REST_API_KEY = "7f6b37e79af97a137e34123c32b0a8fe"
CLIENT_SECRET = "hGq71RHi1PZK6M5hXvfqqYIOSOplZG0P"

def get_fresh_token(refresh_token):
    """리프레시 토큰으로 새 액세스 토큰 발급"""
    res = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": REST_API_KEY,
            "refresh_token": refresh_token,
            "client_secret": CLIENT_SECRET,
        }
    )
    data = res.json()
    if "access_token" not in data:
        raise Exception(f"토큰 갱신 실패: {data}")
    return data["access_token"]

def load_tokens():
    """환경변수 또는 .env 파일에서 리프레시 토큰 로드 후 새 액세스 토큰 발급"""
    wife_refresh    = os.environ.get("KAKAO_REFRESH_TOKEN")
    husband_refresh = os.environ.get("KAKAO_REFRESH_TOKEN_HUSBAND")

    if not (wife_refresh and husband_refresh):
        env_path = os.path.expanduser("~/가계부분析/.env")
        tokens = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, val = line.split("=", 1)
                    tokens[key] = val
        wife_refresh    = tokens["KAKAO_REFRESH_TOKEN"]
        husband_refresh = tokens["KAKAO_REFRESH_TOKEN_HUSBAND"]

    token_wife    = get_fresh_token(wife_refresh)
    token_husband = get_fresh_token(husband_refresh)
    return token_wife, token_husband
