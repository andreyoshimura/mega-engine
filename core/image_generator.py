"""
Mega-Engine — Image Generator (Mega-Sena)

Versão Blindada:

✔ Gera imagem semanal apenas se não existir
✔ Sempre atualiza mega_atual.png
✔ Evita inconsistência entre histórico e atual
✔ Seguro para múltiplas execuções na mesma semana
✔ Prompt institucional estratégico (sem apelo a aposta)
"""

import os
import json
import base64
import random
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

generate_weekly = not weekly_filename.exists()


# ============================================================
# THEME VARIATION
# ============================================================

themes = [
    "luxury gold premium",
    "green energy modern",
    "dark minimalistic black and green",
    "neon futuristic digital",
    "deep emerald sophisticated",
    "tech blue digital interface"
]

theme = themes[week % len(themes)]


# ============================================================
# HEADLINE VARIATION
# ============================================================

headline_options = [
    "Análise de Padrões",
    "Estratégia Numérica",
    "Probabilidade Aplicada"
]

headline = random.choice(headline_options)


# ============================================================
# PROMPT INSTITUCIONAL
# ============================================================

prompt = f"""
Create a 1024x1024 Instagram image.

Style: modern clean cartoon, sophisticated marketing look.
Visual theme: {theme}.

Main concept: statistical analysis of numerical patterns for Mega-Sena.

Include:
- A smart cartoon analyst mascot wearing glasses
- Holding a tablet with organized numbers
- Subtle charts and trend lines in background
- Floating numbers connected by thin lines
- Clean minimal composition
- Soft high contrast lighting

Main headline:
"{headline}"

Footer requirement:
- Write the word: Mega-Sena
- Place it small in the bottom center
- Subtle, clean typography
- Not dominant
- Integrated into the design

Restrictions:
- No money
- No prizes
- No lottery machines
- No celebration
- No gambling references
- No urgency tone
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

# Sempre atualiza mega_atual.png
with open(current_filename, "wb") as img_file:
    img_file.write(image_bytes)

print("✅ mega_atual.png atualizado")

# Histórico semanal preservado
if generate_weekly:
    with open(weekly_filename, "wb") as img_file:
        img_file.write(image_bytes)
    print(f"✅ mega_semana_{week}.png criado")
else:
    print(f"ℹ️ mega_semana_{week}.png já existe — histórico preservado")
