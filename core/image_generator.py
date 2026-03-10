"""
Mega-Engine — Image Generator (Mega-Sena)

Versão otimizada

Melhorias implementadas:

✔ Prompt reduzido (menos tokens da OpenAI)
✔ Variação real de cenários visuais
✔ Seed determinística baseada no concurso
✔ Redimensionamento automático para 800x800
✔ Compressão do PNG (arquivo menor)
✔ Mantém histórico semanal
✔ Sempre atualiza mega_atual.png
✔ Comentários detalhados para manutenção
"""

import os
import json
import base64
import random
from datetime import datetime
from pathlib import Path
from io import BytesIO

from PIL import Image
from openai import OpenAI


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Pasta onde as imagens serão salvas
OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API KEY da OpenAI (definida no GitHub Secrets)
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY não encontrada.")

client = OpenAI(api_key=api_key)


# ============================================================
# CARREGAMENTO DOS DADOS GERADOS
# ============================================================

# Arquivo gerado pelo generator.py
with open("out/jogos_gerados.json", "r", encoding="utf-8") as f:
    data = json.load(f)

concurso = data.get("concurso", "")
ticket_size = data.get("ticket_size", 6)


# ============================================================
# CONTROLE SEMANAL DE IMAGENS
# ============================================================

week = datetime.now().isocalendar().week

weekly_filename = OUTPUT_DIR / f"mega_semana_{week}.png"
current_filename = OUTPUT_DIR / "mega_atual.png"

# evita gerar histórico duplicado
generate_weekly = not weekly_filename.exists()


# ============================================================
# SEED DETERMINÍSTICO
# ============================================================

# garante que o mesmo concurso sempre gere a mesma imagem
seed = int(concurso) if str(concurso).isdigit() else week
random.seed(seed)


# ============================================================
# VARIAÇÃO DE CENÁRIO
# ============================================================

themes = [

    "futuristic AI laboratory analyzing numbers",
    "high tech financial analysis control room",
    "robot mathematician studying probability",
    "scientist research lab studying number patterns",
    "cyberpunk data center with floating numbers",
    "modern analytics office with giant dashboards",
    "space station data lab studying statistics",
    "minimal whiteboard with probability equations",
]

theme = random.choice(themes)


# ============================================================
# VARIAÇÃO DE ESTILO
# ============================================================

styles = [

    "clean flat illustration",
    "modern cartoon illustration",
    "isometric digital illustration",
    "neon cyberpunk illustration",
    "corporate tech vector art",
]

style = random.choice(styles)


# ============================================================
# VARIAÇÃO DE LAYOUT
# ============================================================

layouts = [

    "analyst studying numbers on tablet",
    "floating numbers forming data network",
    "large digital dashboard with charts",
    "probability graphs surrounding analyst",
]

layout = random.choice(layouts)


# ============================================================
# VARIAÇÃO DE HEADLINE
# ============================================================

headline_options = [

    "Análise de Padrões",
    "Estratégia Numérica",
    "Probabilidade Aplicada"

]

headline = random.choice(headline_options)


# ============================================================
# PROMPT OTIMIZADO (REDUZ TOKENS)
# ============================================================

prompt = f"""
Instagram illustration about statistical analysis of Mega-Sena numbers.

Scene: {theme}
Style: {style}
Layout: {layout}

Include:
analyst mascot with glasses,
floating numbers,
data charts and probability patterns.

Headline: "{headline}"

Footer text: Mega-Sena

Rules:
no money, no prizes, no lottery machines, no gambling tone
"""


# ============================================================
# GERAÇÃO DA IMAGEM (OpenAI)
# ============================================================

print("🎨 Gerando imagem com OpenAI...")

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"  # gera maior para melhor qualidade
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)


# ============================================================
# REDIMENSIONAMENTO PARA 800x800
# ============================================================

# abre imagem em memória
image = Image.open(BytesIO(image_bytes))

# redimensiona para tamanho ideal para Instagram
image = image.resize((800, 800), Image.LANCZOS)


# ============================================================
# SALVAR IMAGEM ATUAL
# ============================================================

image.save(
    current_filename,
    "PNG",
    optimize=True
)

print("✅ mega_atual.png atualizado (800x800)")


# ============================================================
# SALVAR HISTÓRICO SEMANAL
# ============================================================

if generate_weekly:

    image.save(
        weekly_filename,
        "PNG",
        optimize=True
    )

    print(f"✅ mega_semana_{week}.png criado")

else:

    print(f"ℹ️ mega_semana_{week}.png já existe — histórico preservado")
