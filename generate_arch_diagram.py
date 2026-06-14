"""
Architecture diagram for Python Programming Q&A Assistant.
Saves to data/architecture_diagram.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0D1117"
CARD     = "#161B22"
BORDER   = "#30363D"
WHITE    = "#FFFFFF"
LIGHT    = "#E2E8F0"
MUTED    = "#8B949E"
DIM      = "#4B5563"
BLUE     = "#38BDF8"
GREEN    = "#34D399"
ORANGE   = "#FB923C"
PURPLE   = "#A78BFA"
PINK     = "#F472B6"
YELLOW   = "#FBBF24"

fig, ax = plt.subplots(figsize=(18, 11))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis("off")

# ── Helpers ───────────────────────────────────────────────────────────────────

def rounded_rect(ax, x, y, w, h, color=CARD, edge=BORDER, lw=1.2, radius=0.22, zorder=2):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=edge, linewidth=lw, zorder=zorder,
    )
    ax.add_patch(box)
    return box

def left_stripe(ax, x, y, h, color, width=0.13, zorder=3):
    box = FancyBboxPatch(
        (x, y), width, h,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=color, edgecolor=color, linewidth=0, zorder=zorder,
    )
    ax.add_patch(box)

def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.8, style="-|>"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color,
            lw=lw, connectionstyle="arc3,rad=0.0",
        ),
        zorder=5,
    )

def label(ax, x, y, text, size=10, color=WHITE, bold=False, ha="center", va="center", zorder=6):
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder, fontfamily="monospace" if "`" in text else "sans-serif")

def tag(ax, x, y, text, bg, fg=BG, size=8.5, zorder=7):
    ax.text(x, y, text, fontsize=size, color=fg, fontweight="bold",
            ha="center", va="center", zorder=zorder,
            bbox=dict(boxstyle="round,pad=0.22", facecolor=bg, edgecolor=bg))

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
ax.text(9, 10.45, "Python Q&A Assistant — System Architecture",
        fontsize=19, color=WHITE, fontweight="bold", ha="center", va="center", zorder=6)
# Blue underline
ax.plot([4.6, 13.4], [10.18, 10.18], color=BLUE, lw=2.5, solid_capstyle="round", zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# TOP ROW — end-to-end flow  (y = 8.2–9.6)
# ══════════════════════════════════════════════════════════════════════════════
flow_items = [
    ("User\nQuestion",    "#1C2736", BLUE,   "Q"),
    ("Next.js UI\n:3000", "#1A2E3B", BLUE,   "UI"),
    ("FastAPI\n:8000",    "#142B1F", GREEN,  "API"),
    ("RAG\nPipeline",     "#22183A", PURPLE, "RAG"),
    ("Answer +\nSources", "#1C2736", GREEN,  "ANS"),
]

flow_y  = 8.25
flow_h  = 1.3
flow_w  = 2.6
gap     = 0.42
start_x = 0.7

for i, (lbl, bg, clr, ico) in enumerate(flow_items):
    x = start_x + i * (flow_w + gap)
    rounded_rect(ax, x, flow_y, flow_w, flow_h, color=bg, edge=clr, lw=1.8)
    # Icon circle
    circle = plt.Circle((x + 0.38, flow_y + flow_h - 0.32), 0.22, color=clr, zorder=4)
    ax.add_patch(circle)
    ax.text(x + 0.38, flow_y + flow_h - 0.32, ico, fontsize=10, ha="center", va="center", zorder=5)
    # Label
    ax.text(x + flow_w / 2, flow_y + flow_h / 2 - 0.06,
            lbl, fontsize=10.5, color=WHITE, fontweight="bold",
            ha="center", va="center", zorder=6, linespacing=1.4)
    # Arrow to next box
    if i < len(flow_items) - 1:
        ax.annotate("", xy=(x + flow_w + gap, flow_y + flow_h / 2),
                    xytext=(x + flow_w, flow_y + flow_h / 2),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.8), zorder=5)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION LABEL
# ══════════════════════════════════════════════════════════════════════════════
ax.text(9, 7.82, "RAG Pipeline — Internal Steps",
        fontsize=11, color=MUTED, fontweight="bold", ha="center", va="center", zorder=6)
ax.plot([2.8, 15.2], [7.6, 7.6], color=BORDER, lw=1, linestyle="--", zorder=3)

# ══════════════════════════════════════════════════════════════════════════════
# RAG STEP CARDS  (y = 4.3–7.4)
# ══════════════════════════════════════════════════════════════════════════════
rag_steps = [
    {
        "n": "01", "label": "EMBED",
        "tech": "sentence-transformers\nall-MiniLM-L6-v2",
        "detail": "User question → 384-dim\nfloat vector (CPU, <50 ms)",
        "color": BLUE,
        "bg": "#0F1E2E",
    },
    {
        "n": "02", "label": "SEARCH",
        "tech": "FAISS Cosine Similarity",
        "detail": "50K+ SO vectors searched;\nTop-5 results returned",
        "color": GREEN,
        "bg": "#0C1F17",
    },
    {
        "n": "03", "label": "AUGMENT",
        "tech": "Strict RAG Prompt",
        "detail": '"Answer ONLY from context"\ntemp=0.1 → deterministic',
        "color": PURPLE,
        "bg": "#1A1128",
    },
    {
        "n": "04", "label": "GENERATE",
        "tech": "google-genai SDK",
        "detail": "gemini-2.5-flash →\nMarkdown answer + code",
        "color": ORANGE,
        "bg": "#251508",
    },
    {
        "n": "05", "label": "RETURN",
        "tech": "JSON Response",
        "detail": "answer · sources\nlatency_ms · timestamp",
        "color": PINK,
        "bg": "#22091A",
    },
]

card_y  = 4.3
card_h  = 3.1
card_w  = 2.8
gap2    = 0.15
start2  = 0.45

for i, step in enumerate(rag_steps):
    x = start2 + i * (card_w + gap2)
    clr = step["color"]

    # Card body
    rounded_rect(ax, x, card_y, card_w, card_h, color=step["bg"], edge=clr, lw=1.8, radius=0.18)
    # Top accent bar
    ax.add_patch(FancyBboxPatch(
        (x, card_y + card_h - 0.065), card_w, 0.065,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=clr, edgecolor=clr, linewidth=0, zorder=3,
    ))

    # Number badge
    circle = plt.Circle((x + card_w / 2, card_y + card_h - 0.42), 0.3, color=clr, zorder=4)
    ax.add_patch(circle)
    ax.text(x + card_w / 2, card_y + card_h - 0.42, step["n"],
            fontsize=11, color=BG, fontweight="bold", ha="center", va="center", zorder=5)

    # Step name
    ax.text(x + card_w / 2, card_y + card_h - 0.95,
            step["label"], fontsize=13, color=clr, fontweight="bold",
            ha="center", va="center", zorder=5)

    # Tech name
    ax.text(x + card_w / 2, card_y + card_h - 1.5,
            step["tech"], fontsize=9.5, color=LIGHT,
            ha="center", va="center", zorder=5, linespacing=1.45)

    # Divider
    ax.plot([x + 0.25, x + card_w - 0.25],
            [card_y + 1.45, card_y + 1.45],
            color=BORDER, lw=0.8, zorder=4)

    # Detail text
    ax.text(x + card_w / 2, card_y + 0.82,
            step["detail"], fontsize=9, color=MUTED,
            ha="center", va="center", zorder=5, linespacing=1.5)

    # Arrow between cards
    if i < len(rag_steps) - 1:
        ax.annotate("", xy=(x + card_w + gap2, card_y + card_h / 2),
                    xytext=(x + card_w, card_y + card_h / 2),
                    arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.5), zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# TECH STACK LEGEND  (bottom row)
# ══════════════════════════════════════════════════════════════════════════════
legend_y  = 0.35
legend_h  = 3.55
legend_items = [
    ("Backend",    BLUE,   ["FastAPI + Uvicorn", "Python 3.9+", "Pydantic v2", "CORS / Lifespan"]),
    ("Embeddings", GREEN,  ["all-MiniLM-L6-v2", "sentence-transformers", "384-dim vectors", "CPU inference"]),
    ("Vector DB",  PURPLE, ["FAISS in-process", "Cosine similarity", "~50K SO docs", "→ Pinecone at scale"]),
    ("LLM / AI",   ORANGE, ["Google GenAI SDK", "gemini-2.5-flash", "temp = 0.1", "Strict RAG prompt"]),
    ("Frontend",   PINK,   ["Next.js 14 App Router", "TypeScript + Tailwind", "react-markdown", "Syntax highlighting"]),
]

leg_w     = 3.05
leg_gap   = 0.18
leg_start = 0.45

for i, (cat, clr, bullets) in enumerate(legend_items):
    x = leg_start + i * (leg_w + leg_gap)
    rounded_rect(ax, x, legend_y, leg_w, legend_h, color=CARD, edge=clr, lw=1.6, radius=0.16)
    left_stripe(ax, x, legend_y, legend_h, clr)

    # Category header
    ax.text(x + leg_w / 2, legend_y + legend_h - 0.32,
            cat, fontsize=12, color=clr, fontweight="bold",
            ha="center", va="center", zorder=6)
    # Divider
    ax.plot([x + 0.22, x + leg_w - 0.22],
            [legend_y + legend_h - 0.56, legend_y + legend_h - 0.56],
            color=BORDER, lw=0.7, zorder=4)

    # Bullet items
    for j, b in enumerate(bullets):
        by = legend_y + legend_h - 0.88 - j * 0.6
        ax.text(x + 0.32, by, "›", fontsize=11, color=clr, ha="left", va="center", zorder=6)
        ax.text(x + 0.52, by, b,   fontsize=9.5, color=LIGHT, ha="left", va="center", zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# Vertical connector from top flow → RAG cards
# ══════════════════════════════════════════════════════════════════════════════
# "RAG Pipeline" box center  ≈  x= start_x + 3*(flow_w+gap) + flow_w/2
rag_box_cx = start_x + 3 * (flow_w + gap) + flow_w / 2   # ~11.16
ax.annotate("", xy=(rag_box_cx, card_y + card_h),
            xytext=(rag_box_cx, flow_y),
            arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.8,
                            connectionstyle="arc3,rad=0"), zorder=5)

# ══════════════════════════════════════════════════════════════════════════════
# Vertical connector from RAG cards → tech legend
# ══════════════════════════════════════════════════════════════════════════════
# Mid-point of RAG steps
mid_cx = start2 + 2 * (card_w + gap2) + card_w / 2
ax.annotate("", xy=(mid_cx, legend_y + legend_h),
            xytext=(mid_cx, card_y),
            arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.5,
                            connectionstyle="arc3,rad=0"), zorder=5)

ax.text(mid_cx + 0.25, (card_y + legend_y + legend_h) / 2,
        "tech stack", fontsize=8, color=DIM, va="center", zorder=6, rotation=90)

# ══════════════════════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════════════════════
ax.plot([0.2, 17.8], [0.26, 0.26], color=BORDER, lw=0.8, zorder=3)
ax.text(9, 0.13, "Python Programming Q&A Assistant  ·  Taniya Aggarwal  ·  Analytics Vidhya 2026",
        fontsize=8.5, color=MUTED, ha="center", va="center", zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
out = "/Users/taniyaaggarwal/Documents/Python Programming Q&A Assistant/data/architecture_diagram.png"
plt.tight_layout(pad=0)
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"✅  Saved → {out}")
