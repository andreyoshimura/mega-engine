"""
Mega-Engine — Image Generator (Mega-Sena)

Versão Blindada:

✔ Gera imagem semanal apenas se não existir
✔ Sempre atualiza mega_atual.png
✔ Evita inconsistência entre histórico e atual
✔ Seguro para múltiplas execuções na mesma semana
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from openai import OpenAI


# ============================================================
# CONFIG
# ============================================================

OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)


# ============================================================
# LOAD DATA
# ============================================================

with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)


# ============================================================
# WEEK LOGIC
# ============================================================

week = datetime.now().isocalendar().week
weekly_filename = OUTPUT_DIR / f"mega_semana_{week}.png"
current_filename = OUTPUT_DIR / "mega_atual.png"


# ============================================================
# SE JÁ EXISTE IMAGEM DA SEMANA
# NÃO REGERA HISTÓRICO
# ============================================================

generate_weekly = not weekly_filename.exists()


# ============================================================
# THEME VARIATION
# ============================================================

themes = [
    "luxury gold premium",
    "green energy modern",
    "dark minimalistic black and green",
    "neon futuristic digital",
    "explosion of money vibrant",
    "tech blue digital interface"
]

theme = themes[week % len(themes)]


# ============================================================
# PROMPT
# ============================================================

prompt = f"""
Instagram post 1024x1024 for Mega-Sena lottery.
Theme: {theme}.
Modern Brazilian design.
Floating lottery balls.
High contrast lighting.
Professional marketing look.
Clean composition.
No excessive text.
Only small subtle 'Mega-Sena'.
"""


# ============================================================
# GENERATE IMAGE
# ============================================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)


# ============================================================
# SAVE FILES
# ============================================================

# 1️⃣ Atual sempre sobrescreve
with open(current_filename, "wb") as img_file:
    img_file.write(image_bytes)

print(f"✅ mega_atual.png atualizado")

# 2️⃣ Histórico semanal só cria se não existir
if generate_weekly:
    with open(weekly_filename, "wb") as img_file:
        img_file.write(image_bytes)
    print(f"✅ mega_semana_{week}.png criado")
else:
    print(f"ℹ️ mega_semana_{week}.png já existe — histórico preservado")
