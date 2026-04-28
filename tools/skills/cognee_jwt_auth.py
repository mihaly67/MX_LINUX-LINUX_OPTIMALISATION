import argparse
import jwt
import time

def generate_agent_token(user_id: str, minutes_valid: int = 60, secret_key: str = "jules-secret-agent-key-32bytes-long!"):
    """
    A Chatbot RAG-ban talált `cognee-main/cognee/get_token.py` JWT logika
    alapján épített biztonsági modul a Fő Agent számára.
    Ez a modul lehetővé teszi, hogy időkorlátos tokenekkel authentikáljuk
    a jövőbeni belső mikroszerveres API kéréseket (Zero-Trust security).
    """
    expiration_time = time.time() + (minutes_valid * 60)
    payload = {
        "user_id": user_id,
        "exp": expiration_time,
        "role": "autonomous_agent"
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def verify_agent_token(token: str, secret_key: str = "jules-secret-agent-key-32bytes-long!"):
    try:
        decoded_payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return True, decoded_payload
    except jwt.ExpiredSignatureError:
        return False, "Lejárt token."
    except jwt.InvalidTokenError:
        return False, "Érvénytelen token."

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["generate", "verify"], required=True)
    parser.add_argument("--user", type=str, default="jules")
    parser.add_argument("--token", type=str)

    args = parser.parse_args()

    if args.action == "generate":
        t = generate_agent_token(args.user)
        print(f"Generált JWT Token a '{args.user}' számára:\\n{t}")
    elif args.action == "verify":
        if not args.token:
            print("Hiányzó --token paraméter.")
        else:
            success, payload = verify_agent_token(args.token)
            if success:
                print(f"✅ Token érvényes! Payload: {payload}")
            else:
                print(f"❌ Token hiba: {payload}")
