import jwt
import datetime
import os

# A titkos kulcsot környezeti változóból olvassuk be a biztonság érdekében
SECRET_KEY = os.environ.get("VPS_JWT_SECRET", "default-fallback-key-do-not-use-in-prod")

def generate_token():
    payload = {
        "sub": "jules_local_agent",
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return "Token lejárt!"
    except jwt.InvalidTokenError:
        return "Érvénytelen token!"

if __name__ == "__main__":
    t = generate_token()
    print("General JWT Token:", t)
    print("Verifikacio:", verify_token(t))
