import requests

TOKEN = open("token.txt").read().strip()
headers = {"Authorization": f"Bearer {TOKEN}"}

r = requests.get("https://www.emtpalma.cat/maas/api/v1/agency/lines/", headers=headers)
print("STATUS:", r.status_code)
print("BODY:", r.text[:400])


