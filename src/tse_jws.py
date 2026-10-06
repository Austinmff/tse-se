import base64
import json


def _decode(parte):
    parte += "=" * (-len(parte) % 4)
    return base64.urlsafe_b64decode(parte).decode("utf-8")


def read_jws(caminho):
    with open(caminho, encoding="utf-8") as f:
        texto = f.read().strip()
    if texto.startswith("{"):
        payload = json.loads(texto)["payload"]
    else:
        payload = texto.split(".")[1]
    return json.loads(_decode(payload))