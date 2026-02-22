# Gerador de imagem post
import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# ============================================
# CONFIG
# ============================================

OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================
# LOAD GENERATED DATA
# ============================================

with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)

# ============================================
# THEME VARIATION (WEEK BASED)
# ============================================

week = datetime.now().isocalendar().week

themes = [
    "luxury gold premium",
    "green energy modern",
    "dark minimalistic black and green",
    "neon futuristic digital",
    "explosion of money vibrant",
    "tech blue digital interface"
]

theme = themes[week % len(themes)]

# ============================================
# DYNAMIC PROMPT
# ============================================

prompt = f"""
Instagram post 1080x1080 for Mega-Sena lottery.
Theme: {theme}.
Modern Brazilian design.
Floating lottery balls.
High contrast lighting.
Professional marketing look.
Clean composition.
No excessive text.
Only small subtle 'Mega-Sena'.
"""

# ============================================
# GENERATE IMAGE
# ============================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1080x1080"
)

image_base64 = result.data[0].b64_json

import base64

image_bytes = base64.b64decode(image_base64)

filename = OUTPUT_DIR / f"mega_semana_{week}.png"

with open(filename, "wb") as img_file:
    img_file.write(image_bytes)

print(f"Image generated: {filename}")
