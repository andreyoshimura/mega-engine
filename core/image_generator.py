"""
============================================================
Mega-Engine — Image Generator (Mega-Sena)

O que este script faz:

1. Lê os jogos gerados em:
   -> out/jogos_gerados.json

2. Detecta automaticamente a semana do ano

3. Escolhe um tema visual diferente baseado na semana
   (rotação automática semanal)

4. Gera uma imagem 1024x1024 via OpenAI (compatível com Instagram)

5. Salva dois arquivos:
   - Histórico:
       out/images/mega_semana_<NUMERO_DA_SEMANA>.png
   - Arquivo canônico (sempre sobrescreve):
       out/images/mega_atual.png

IMPORTANTE:
- O n8n deve sempre usar mega_atual.png
- O histórico semanal permanece salvo no repositório

Requisitos:
- Secret OPENAI_API_KEY configurado no GitHub Actions
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

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente.")

client = OpenAI(api_key=api_key)


# ============================================================
# 1️⃣ LÊ ARQUIVO DE JOGOS GERADOS
# Arquivo produzido por: core/generator.py
# ============================================================

with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)


# ============================================================
# 2️⃣ DEFINIÇÃO DE TEMA AUTOMÁTICO (VARIA POR SEMANA)
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

theme = themes[week % len(themes)]


# ============================================================
# 3️⃣ PROMPT DINÂMICO
# Se quiser alterar estilo visual, modifique apenas esta seção
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
# 4️⃣ GERAÇÃO DA IMAGEM
# ============================================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)


# ============================================================
# 5️⃣ SALVA IMAGEM (HISTÓRICO + ATUAL)
# ============================================================

# Histórico semanal
weekly_filename = OUTPUT_DIR / f"mega_semana_{week}.png"
with open(weekly_filename, "wb") as img_file:
    img_file.write(image_bytes)

# Arquivo canônico (sempre sobrescreve)
current_filename = OUTPUT_DIR / "mega_atual.png"
with open(current_filename, "wb") as img_file:
    img_file.write(image_bytes)

print(f"✅ Weekly image generated: {weekly_filename}")
print(f"✅ Current image updated: {current_filename}")
