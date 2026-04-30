# generate_token.py
import jwt
import time
import requests
import json
import sys
import argparse
# ⚙️ CONFIG
CONSUMER_KEY = "3MVG9z5xLJmws289Fbf3FRY6YoboU5Cbr9pgtKxJDJGAqjBqPCfnWgshCzLxuRj_z0uXdSIOzm7.vy3yDIyhH"
PRIVATE_KEY_PATH = "server.key"
TOKEN_OUTPUT_PATH = "token.txt"

def generate_token(username):
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iss": CONSUMER_KEY,
        "sub": username,
        "aud": "https://test.salesforce.com",
        "exp": int(time.time()) + 300
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")

    response = requests.post(
        "https://test.salesforce.com/services/oauth2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }
    )

    data = response.json()

    if "access_token" in data:
        with open(TOKEN_OUTPUT_PATH, "w") as f:
            f.write(data["access_token"])
        print("✅ Token généré avec succès !")
        return data["access_token"], data.get("instance_url")
    else:
        with open(TOKEN_OUTPUT_PATH, "w") as f:
            f.write("ERREUR: " + json.dumps(data))
        print("❌ Erreur : ", data)
        return None, None

def test_token(access_token, instance_url):
    print("\n🔍 Test du token en cours...")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Test 1 — Vérification API
    response = requests.get(
        f"{instance_url}/services/data/v59.0/",
        headers=headers
    )

    if response.status_code == 200:
        print("✅ Token valide !")
    else:
        print(f"❌ Échec — Status {response.status_code}")
        print(response.text)
        return

    # Test 2 — Query Contact
    print("\n📋 Query SOQL : SELECT Id, FirstName FROM Contact LIMIT 1")

    query = "SELECT+Id,+FirstName+FROM+Contact+LIMIT+1"
    query_response = requests.get(
        f"{instance_url}/services/data/v59.0/query?q={query}",
        headers=headers
    )

    if query_response.status_code == 200:
        data = query_response.json()
        records = data.get("records", [])
        if records:
            contact = records[0]
            print("✅ Contact trouvé :")
            print(f"   Id        : {contact.get('Id')}")
            print(f"   FirstName : {contact.get('FirstName')}")
        else:
            print("⚠️  Aucun contact trouvé dans l'org")
    else:
        print(f"❌ Erreur query — Status {query_response.status_code}")
        print(query_response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="Salesforce username")
    parser.add_argument("--test", action="store_true", help="Teste le token après génération")
    args = parser.parse_args()

    access_token, instance_url = generate_token(args.username)

    if args.test and access_token:
        test_token(access_token, instance_url)
