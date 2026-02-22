"""
============================================================
Mega-Engine — Image Generator (Mega-Sena)

Atualizado:
- Prompt "mascote analista" (ultra seguro / educativo)
- Adiciona logo pequena (Sorte Fácil) automaticamente no canto

Este script:

1. Lê os jogos gerados em:
   -> out/jogos_gerados.json

2. Detecta automaticamente a semana do ano

3. Escolhe um tema visual diferente baseado na semana

4. Gera uma imagem 1024x1024 via OpenAI

5. Aplica a logo no canto inferior direito (discreta, com transparência)

6. Salva a imagem em:
   -> out/images/mega_semana_<NUMERO_DA_SEMANA>.png

Requisitos:
- Secret OPENAI_API_KEY configurado no GitHub Actions
- Pasta out/images/ será criada automaticamente se não existir
- pip install pillow
============================================================
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path

from openai import OpenAI

# NEW: para aplicar logo com controle total
from PIL import Image


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Diretório onde as imagens serão salvas
OUTPUT_DIR = Path("out/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Caminho da logo (coloque seu arquivo aqui no repositório)
# Sugestão: crie a pasta assets/ e adicione a logo como PNG com transparência.
LOGO_PATH = Path("assets/sorte_facil_logo.png")

# Tamanho relativo da logo (percentual da largura da imagem final)
LOGO_WIDTH_RATIO = 0.14  # 14% da largura
LOGO_OPACITY = 0.78      # 0.0 a 1.0
LOGO_MARGIN_RATIO = 0.03 # margem em % da largura

# Inicializa cliente OpenAI usando SECRET do GitHub
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ============================================================
# 1️⃣ LÊ O ARQUIVO DE JOGOS GERADOS
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
    "modern emerald gradient, clean brazilian design",
    "deep blue tech editorial, minimal and premium",
    "dark purple premium, subtle neon highlights",
    "green and navy corporate, high contrast soft lighting",
    "teal and graphite modern, sleek analytical look",
    "midnight blue interface vibe, minimal geometry"
]

theme = themes[week % len(themes)]


# ============================================================
# 3️⃣ MONTA O PROMPT (MASCOTE ANALISTA — ULTRA SEGURO)
# ============================================================

# Observação:
# - Mantém o conteúdo como "análise numérica / probabilidade"
# - Evita termos diretos de aposta/prêmio
# - A associação de marca fica pela logo aplicada via código
prompt = f"""
Você é um gerador de imagens profissional para marketing educativo.

Crie uma imagem 1024x1024 para Instagram.
Estilo: desenho animado moderno, clean, sofisticado (não infantil).
Tema visual: {theme}.

Tema central: análise estatística de números e padrões probabilísticos.
A imagem deve transmitir estratégia, estudo e organização matemática,
sem qualquer referência direta a apostas, prêmios, dinheiro, urgência ou celebração.

Personagem (mascote analista):
- Mascote original estilo cartoon moderno
- Aparência simpática e inteligente
- Óculos e postura confiante
- Segurando tablet/prancheta digital com números organizados
- Expressão focada e analítica

Elementos visuais:
- Números flutuando de forma organizada ao redor do mascote
- Linhas de conexão entre números (estilo mapa mental/gráfico)
- Pequenos gráficos sutis (barras/linha de tendência), bem discretos
- Iluminação suave com alto contraste equilibrado
- Composição minimalista e profissional
- Sem poluição visual

Texto (mínimo, neutro, sem gatilhos de jogo):
Escolher apenas UMA frase pequena:
"Análise de Padrões" OU "Estratégia Numérica" OU "Probabilidade Aplicada"

Restrições:
- Não incluir dinheiro, prêmios, troféus, fogos, comemoração
- Não incluir bolas de sorteio tradicionais nem máquina de sorteio
- Não sugerir ganho financeiro
"""


# ============================================================
# 4️⃣ GERA IMAGEM COM IA
# ============================================================

result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)


# ============================================================
# 5️⃣ APLICA LOGO PEQUENA NO CANTO (DISCRETA)
# ============================================================

def apply_logo(base_image_bytes: bytes, logo_path: Path) -> bytes:
    """Aplica a logo no canto inferior direito, com transparência e margem."""
    base = Image.open(BytesIO(base_image_bytes)).convert("RGBA")

    if not logo_path.exists():
        # Se não tiver logo no repo, salva a imagem sem logo (não quebra o pipeline)
        return base_image_bytes

    logo = Image.open(logo_path).convert("RGBA")

    # Redimensiona a logo proporcionalmente
    target_w = int(base.width * LOGO_WIDTH_RATIO)
    scale = target_w / logo.width
    target_h = max(1, int(logo.height * scale))
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    # Aplica opacidade (mantém alpha original)
    if LOGO_OPACITY < 1.0:
        r, g, b, a = logo.split()
        a = a.point(lambda px: int(px * LOGO_OPACITY))
        logo = Image.merge("RGBA", (r, g, b, a))

    margin = int(base.width * LOGO_MARGIN_RATIO)
    x = base.width - logo.width - margin
    y = base.height - logo.height - margin

    base.alpha_composite(logo, (x, y))

    out = BytesIO()
    base.convert("RGBA").save(out, format="PNG")
    return out.getvalue()


# BytesIO import aqui para evitar poluir topo do arquivo
from io import BytesIO

final_bytes = apply_logo(image_bytes, LOGO_PATH)


# ============================================================
# 6️⃣ SALVA IMAGEM NO REPOSITÓRIO
# ============================================================

filename = OUTPUT_DIR / f"mega_semana_{week}.png"

with open(filename, "wb") as img_file:
    img_file.write(final_bytes)

print(f"✅ Image generated: {filename}")
if LOGO_PATH.exists():
    print(f"✅ Logo applied: {LOGO_PATH}")
else:
    print(f"⚠️ Logo not found at: {LOGO_PATH} (saved without logo)")
