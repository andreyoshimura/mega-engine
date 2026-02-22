"""
============================================================
Mega-Engine — Image Generator (Versão sem Pillow)

- Sem dependência de PIL
- Sem aplicação automática de logo
- Ultra seguro contra moderação
- Apenas geração da arte base

Salva em:
out/images/mega_semana_<NUMERO>.png
============================================================
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# ============================================================
# CONFIGURAÇÕES
# ============================================================

OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# 1️⃣ LÊ JOGOS GERADOS
# ============================================================

with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)

# ============================================================
# 2️⃣ DEFINE TEMA POR SEMANA
# ============================================================

week = datetime.now().isocalendar().week

themes = [
    "modern emerald gradient, clean brazilian design",
    "deep blue tech editorial, minimal and premium",
    "dark purple premium, subtle neon highlights",
    "green and navy corporate, high contrast soft lighting",
    "teal and graphite modern, sleek analytical look",
    "midnight blue interface vibe, minimal geometry"
]

theme = themes[week % len(themes)]

# ============================================================
# 3️⃣ PROMPT ULTRA SEGURO
# ============================================================

prompt = f"""
Create a 1024x1024 Instagram image.

Style: modern clean cartoon, sophisticated marketing look.
Visual theme: {theme}.

Main concept: statistical analysis of numerical patterns.

Include:
- A smart cartoon analyst mascot wearing glasses
- Holding a tablet with organized numbers
- Subtle charts and trend lines
- Floating numbers connected by thin lines
- Clean minimal composition
- Soft high contrast lighting

Text (choose only one):
"Análise de Padrões"
or
"Estratégia Numérica"
or
"Probabilidade Aplicada"

Restrictions:
- No money
- No prizes
- No lottery machines
- No celebration
- No gambling references
- No urgency tone
"""

# ============================================================
# 4️⃣ GERA IMAGEM
# ============================================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

# ============================================================
# 5️⃣ SALVA IMAGEM
# ============================================================

filename = OUTPUT_DIR / f"mega_semana_{week}.png"

with open(filename, "wb") as img_file:
    img_file.write(image_bytes)

print(f"✅ Image generated successfully: {filename}")
