from __future__ import annotations

import base64
import json
import os
import random
from datetime import datetime
from io import BytesIO

from openai import OpenAI
from PIL import Image

from core.config import IMAGE_OUTPUT_DIR, OUT_GAMES_PATH

OUTPUT_DIR = IMAGE_OUTPUT_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY nao encontrada.")

client = OpenAI(api_key=api_key)

with OUT_GAMES_PATH.open("r", encoding="utf-8") as f:
    data = json.load(f)

metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
concurso_ref = metadata.get("target_concurso") or metadata.get("latest_known_concurso")
ticket_size = int(data.get("ticket_size", 6))

week = datetime.now().isocalendar().week
weekly_filename = OUTPUT_DIR / f"mega_semana_{week}.png"
current_filename = OUTPUT_DIR / "mega_atual.png"
generate_weekly = not weekly_filename.exists()

seed = int(concurso_ref) if str(concurso_ref).isdigit() else week
random.seed(seed)

themes = [
    "futuristic AI laboratory analyzing numbers",
    "high tech analytics control room",
    "robot mathematician studying probability",
    "scientist research lab studying number patterns",
    "cyberpunk data center with floating numbers",
    "modern analytics office with giant dashboards",
    "space station data lab studying statistics",
    "minimal whiteboard with probability equations",
]
styles = [
    "clean flat illustration",
    "modern cartoon illustration",
    "isometric digital illustration",
    "neon cyberpunk illustration",
    "corporate tech vector art",
]
layouts = [
    "analyst studying numbers on tablet",
    "floating numbers forming data network",
    "large digital dashboard with charts",
    "probability graphs surrounding analyst",
]
headline_options = [
    "Analise de Padroes",
    "Estrategia Numerica",
    "Probabilidade Aplicada",
]

theme = random.choice(themes)
style = random.choice(styles)
layout = random.choice(layouts)
headline = random.choice(headline_options)

prompt = f"""
Instagram illustration about statistical analysis of Mega-Sena numbers.

Scene: {theme}
Style: {style}
Layout: {layout}

Include:
analyst mascot with glasses,
floating numbers,
data charts and probability patterns.

Headline: \"{headline}\"
Footer text: Mega-Sena
Reference contest: {concurso_ref}
Ticket size: {ticket_size}

Rules:
no money, no prizes, no lottery machines, no gambling tone
"""

print("[IMAGE] Gerando imagem com OpenAI...")
result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

image = Image.open(BytesIO(image_bytes))
image = image.resize((800, 800), Image.LANCZOS)
image.save(current_filename, "PNG", optimize=True)
print("[IMAGE] mega_atual.png atualizado")

if generate_weekly:
    image.save(weekly_filename, "PNG", optimize=True)
    print(f"[IMAGE] {weekly_filename.name} criado")
else:
    print(f"[IMAGE] {weekly_filename.name} ja existe")
