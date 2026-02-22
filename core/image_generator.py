"""
============================================================
Mega-Engine — Image Generator (Mega-Sena)

Este script:

1. Lê os jogos gerados em:
   -> out/jogos_gerados.json

2. Detecta automaticamente a semana do ano

3. Escolhe um tema visual diferente baseado na semana
   (para variar as imagens automaticamente)

4. Gera uma imagem 1080x1080 via OpenAI

5. Salva a imagem em:
   -> out/images/mega_semana_<NUMERO_DA_SEMANA>.png

Requisitos:
- Secret OPENAI_API_KEY configurado no GitHub Actions
- Pasta out/images/ será criada automaticamente se não existir
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

# Diretório onde as imagens serão salvas
OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Inicializa cliente OpenAI usando SECRET do GitHub
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ============================================================
# 1️⃣ LÊ O ARQUIVO DE JOGOS GERADOS
# Arquivo produzido por: core/generator.py
# ============================================================

with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)


# ============================================================
# 2️⃣ DEFINE TEMA VISUAL AUTOMÁTICO (VARIA POR SEMANA)
# ============================================================

week = datetime.now().isocalendar().week

themes = [
    "luxury gold premium",
    "green energy modern",
    "dark minimalistic black and green",
    "neon futuristic digital",
    "explosion of money vibrant",
    "tech blue digital interface"
]

# Alterna automaticamente o tema a cada semana
theme = themes[week % len(themes)]


# ============================================================
# 3️⃣ MONTA O PROMPT DINÂMICO
# 👉 Se quiser alterar estilo visual, edite APENAS esta parte
# ============================================================

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


# ============================================================
# 4️⃣ GERA IMAGEM COM IA
# ============================================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1080x1080"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)


# ============================================================
# 5️⃣ SALVA IMAGEM NO REPOSITÓRIO
# ============================================================

filename = OUTPUT_DIR / f"mega_semana_{week}.png"

with open(filename, "wb") as img_file:
    img_file.write(image_bytes)

print(f"✅ Image generated: {filename}")
