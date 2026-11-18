"""Generate every figure used in the CivicConnect project report."""
import json
import collections
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

BLUE, ORANGE, GREEN, RED, GREY = "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8C8C8C"
PURPLE = "#7A5EA8"
FILL_B, FILL_O, FILL_G, FILL_R, FILL_P = "#E8EDF6", "#FBEDE3", "#E7F2EB", "#F8E7E7", "#EFE9F5"


def box(ax, x, y, w, h, text, fill, edge, fontsize=7.2, weight="normal"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor=fill, edgecolor=edge, linewidth=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, linespacing=1.45, color="#1a1a1a")


def arrow(ax, p, q, color="#555555", ls="-", rad=0.0, lw=1.0):
    ax.add_patch(FancyArrowPatch(
        p, q, arrowstyle="-|>", mutation_scale=10, color=color,
        linestyle=ls, linewidth=lw,
        connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def blank(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------- Figure 1
def fig_architecture():
    fig, ax = blank((7.2, 4.0))
    cx0, cw = 0.345, 0.27           # main column
    h = 0.125

    box(ax, cx0, 0.865, cw, 0.095, "User question", "#F2F2F2", GREY)
    box(ax, cx0, 0.675, cw, h, "Query understanding\njurisdiction · date · intent", FILL_B, BLUE)
    box(ax, 0.025, 0.675, 0.245, h, "Clarification exit\n“which state are you in?”", FILL_O, ORANGE, weight="bold")
    box(ax, cx0, 0.475, cw, h, "Hybrid retrieval\nFAISS + BM25 → RRF", FILL_B, BLUE)
    box(ax, cx0, 0.275, cw, h, "Synthesis\nGroq LLM, grounded prompt", FILL_B, BLUE)
    box(ax, cx0, 0.075, cw, h, "Verification\ncited § ⊆ retrieved §", FILL_B, BLUE)
    box(ax, 0.715, 0.175, 0.26, h, "increment_retry\nat most 2 re-writes", FILL_R, RED)
    box(ax, 0.025, 0.080, 0.245, 0.115, "Answer + citations", FILL_G, GREEN, weight="bold")

    arrow(ax, (cx0 + cw / 2, 0.865), (cx0 + cw / 2, 0.800))
    arrow(ax, (cx0, 0.7375), (0.270, 0.7375), color=ORANGE)
    arrow(ax, (cx0 + cw / 2, 0.675), (cx0 + cw / 2, 0.600))
    arrow(ax, (cx0 + cw / 2, 0.475), (cx0 + cw / 2, 0.400))
    arrow(ax, (cx0 + cw / 2, 0.275), (cx0 + cw / 2, 0.200))
    arrow(ax, (cx0 + cw, 0.115), (0.715, 0.215), color=RED, rad=-0.18)
    arrow(ax, (0.715, 0.272), (cx0 + cw, 0.330), color=RED, rad=-0.18)
    arrow(ax, (cx0, 0.1375), (0.270, 0.1375), color=GREEN)

    ax.text(0.1475, 0.818, "question is state-specific,\nno state known",
            fontsize=6.6, color=ORANGE, style="italic", ha="center", linespacing=1.5)
    ax.text(0.845, 0.135, "citation not in sources", fontsize=6.6, color=RED,
            style="italic", ha="center")
    ax.text(0.845, 0.330, "re-write the answer", fontsize=6.6, color=RED,
            style="italic", ha="center")
    ax.text(0.3075, 0.165, "grounded", fontsize=6.6, color=GREEN,
            style="italic", ha="center")
    ax.text(0.5, 0.985, "LangGraph StateGraph — five nodes, two conditional edges",
            fontsize=7.6, ha="center", color="#444444")
    fig.savefig(OUT / "fig1_architecture.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 2
def fig_hybrid():
    fig, ax = blank((7.2, 3.6))

    box(ax, 0.015, 0.685, 0.155, 0.150, "User query", "#F2F2F2", GREY)
    box(ax, 0.215, 0.845, 0.245, 0.150,
        "Function-word filter\n→ BM25 (rank_bm25)\nsparse, lexical", FILL_O, ORANGE)
    box(ax, 0.215, 0.525, 0.245, 0.150,
        "MiniLM-L6-v2, 384-d\n→ FAISS inner product\ndense, semantic", FILL_B, BLUE)
    box(ax, 0.515, 0.670, 0.21, 0.175,
        "Reciprocal Rank\nFusion\n$k$=5 · dense ×3.0", FILL_P, PURPLE, weight="bold")
    box(ax, 0.775, 0.670, 0.21, 0.175,
        "Jurisdiction and\ndate filters\n→ top-10 chunks", FILL_G, GREEN)

    arrow(ax, (0.170, 0.800), (0.215, 0.900), color=ORANGE, rad=0.12)
    arrow(ax, (0.170, 0.720), (0.215, 0.625), color=BLUE, rad=-0.12)
    arrow(ax, (0.460, 0.900), (0.515, 0.800), color=ORANGE, rad=-0.12)
    arrow(ax, (0.460, 0.625), (0.515, 0.715), color=BLUE, rad=0.12)
    arrow(ax, (0.725, 0.7575), (0.775, 0.7575))

    ax.text(0.5, 0.205,
            "RRF score  =  Σ  weight / ($k$ + rank)\n\n"
            "The constant decides how far agreement between the two arms outweighs confidence "
            "within one of them.\nAt the library default $k$=60, a chunk ranked 50th by both arms "
            "(2/110 = 0.0182) only barely outscored\none ranked 1st by a single arm (1/61 = 0.0164), "
            "so fusion behaved almost like a union of two lists.\n"
            "Lowering $k$ to 5 and weighting the dense arm ×3 made agreement decisive.",
            fontsize=6.9, ha="center", va="center", color="#222222", linespacing=1.75,
            bbox=dict(boxstyle="round,pad=0.55", facecolor="#FAFAFA", edgecolor="#DDDDDD"))
    fig.savefig(OUT / "fig2_hybrid.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 3
def fig_corpus():
    chunks = json.loads((REPO / "data/ingestion/seed_chunks.json").read_text())
    counts = collections.Counter(c["act"] for c in chunks)
    schemes = json.loads((REPO / "data/ingestion/seed_schemes.json").read_text())

    short = {
        "Bharatiya Nyaya Sanhita, 2023": "BNS\n2023",
        "Motor Vehicles Act, 1988": "MV Act\n1988",
        "Consumer Protection Act, 2019": "CPA\n2019",
        "Right to Information Act, 2005": "RTI\n2005",
    }
    labels = [short[a] for a, _ in counts.most_common()] + ["Welfare\nschemes"]
    values = [n for _, n in counts.most_common()] + [len(schemes)]
    colors = [BLUE, BLUE, BLUE, BLUE, GREEN]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.7),
                                   gridspec_kw={"width_ratios": [1, 1.1]})
    bars = ax1.bar(labels, values, color=colors, edgecolor="white", linewidth=0.8, width=0.68)
    for b, v in zip(bars, values):
        ax1.text(b.get_x() + b.get_width() / 2, v + 12, str(v),
                 ha="center", fontsize=7.5, fontweight="bold")
    ax1.set_ylabel("Indexed chunks")
    ax1.set_title(f"Corpus composition — {sum(values)} chunks")
    ax1.set_ylim(0, max(values) * 1.20)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax1.set_axisbelow(True)

    lengths = [len(c["text"]) for c in chunks]
    ax2.hist(lengths, bins=45, color=BLUE, edgecolor="white", linewidth=0.3)
    med = sorted(lengths)[len(lengths) // 2]
    ax2.axvline(med, color=RED, linestyle="--", linewidth=1.1, label=f"median {med} chars")
    ax2.axvline(1500, color="#444444", linestyle=":", linewidth=1.2, label="split threshold 1 500")
    ax2.set_xlabel("Characters per chunk")
    ax2.set_ylabel("Chunks")
    ax2.set_title("Chunk length distribution")
    ax2.legend(frameon=False, loc="upper right")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax2.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_corpus.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 4
def fig_recall_scale():
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    arms = ["Dense\n(FAISS)", "Hybrid\n(RRF, tuned)", "Sparse\n(BM25)"]
    pilot, full = [97, 91, 71], [77, 77, 42]
    x = range(len(arms)); wd = 0.35
    b1 = ax.bar([i - wd / 2 for i in x], pilot, wd, color="#A9BEDC", edgecolor="white",
                label="Pilot corpus — 75 chunks, 69 questions")
    b2 = ax.bar([i + wd / 2 for i in x], full, wd, color=BLUE, edgecolor="white",
                label="Full corpus — 963 chunks, 109 questions")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2,
                    f"{int(b.get_height())}%", ha="center", fontsize=7.4, fontweight="bold")
    ax.set_xticks(list(x)); ax.set_xticklabels(arms)
    ax.set_ylabel("Recall@10 (%)")
    ax.set_ylim(0, 120)
    ax.set_title("Retrieval recall before and after the corpus grew 12.8×")
    ax.legend(frameon=False, loc="upper center", ncol=1, bbox_to_anchor=(0.5, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_recall_scale.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 5
def fig_per_act():
    acts = ["Welfare\nschemes", "Consumer\nProtection", "Motor\nVehicles",
            "Right to\nInformation", "BNS\n2023"]
    dense, bm25, hybrid = [100, 78, 78, 64, 64], [84, 50, 28, 29, 14], [100, 78, 78, 64, 64]

    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    x = range(len(acts)); wd = 0.26
    ax.bar([i - wd for i in x], dense, wd, label="Dense", color=BLUE, edgecolor="white")
    ax.bar(list(x), bm25, wd, label="BM25", color=ORANGE, edgecolor="white")
    ax.bar([i + wd for i in x], hybrid, wd, label="Hybrid", color=GREEN, edgecolor="white")
    for i, (d, b, h) in enumerate(zip(dense, bm25, hybrid)):
        ax.text(i - wd, d + 2, str(d), ha="center", fontsize=6.6, color=BLUE, fontweight="bold")
        ax.text(i, b + 2, str(b), ha="center", fontsize=6.6, color=ORANGE, fontweight="bold")
        ax.text(i + wd, h + 2, str(h), ha="center", fontsize=6.6, color=GREEN, fontweight="bold")
    ax.set_xticks(list(x)); ax.set_xticklabels(acts)
    ax.set_ylabel("Recall@10 (%)")
    ax.set_ylim(0, 126)
    ax.set_title("Recall@10 by source Act — the hybrid column reproduces dense exactly")
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.02))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_per_act.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 6
def fig_tuning():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.0))

    for ax, vals, cols, labels, title, note, top in [
        (ax1, [30, 55], ["#D9D9D9", ORANGE], ["before", "after"],
         "BM25: dropping function words from the query",
         "+25 points\n17 questions fixed, none broken", 86),
        (ax2, [68, 77], ["#D9D9D9", GREEN], ["$k$=60, equal weights\n(library default)",
                                             "$k$=5, dense ×3\n(tuned)"],
         "Hybrid: retuning the fusion constant",
         "+9 points\nhybrid rises to match dense", 108),
    ]:
        ax.bar(labels, vals, color=cols, edgecolor="white", width=0.5)
        for i, v in enumerate(vals):
            ax.text(i, v + 1.8, f"{v}%", ha="center", fontsize=8.5, fontweight="bold")
        ax.set_ylim(0, top)
        ax.set_title(title, fontsize=8.4)
        ax.text(0.5, top * 0.90, note, ha="center", va="top", fontsize=7.0,
                color=RED, linespacing=1.6, transform=ax.transData)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25, linewidth=0.6)
        ax.set_axisbelow(True)
    ax1.set_ylabel("Recall@10 (%)")
    fig.tight_layout()
    fig.savefig(OUT / "fig6_tuning.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 7
def fig_deployment():
    fig, ax = blank((7.2, 3.8))

    box(ax, 0.015, 0.700, 0.155, 0.16, "Browser\nphone / desktop", "#F2F2F2", GREY)
    box(ax, 0.215, 0.700, 0.225, 0.16,
        "Cloudflare Pages\nAstro 7 static build\n12 pages · global CDN", FILL_O, ORANGE, weight="bold")
    box(ax, 0.495, 0.670, 0.300, 0.225,
        "Hugging Face Space\nZeroGPU · Gradio SDK\nFastAPI + Gradio on :7860\nGET /health · POST /query",
        FILL_B, BLUE, weight="bold")
    box(ax, 0.845, 0.700, 0.140, 0.16, "Groq API\nqwen3.8-27b", FILL_G, GREEN)

    arrow(ax, (0.170, 0.780), (0.215, 0.780))
    arrow(ax, (0.440, 0.780), (0.495, 0.780))
    arrow(ax, (0.795, 0.780), (0.845, 0.780))
    ax.text(0.4675, 0.918, "HTTPS\n+ CORS", fontsize=6.3, ha="center", color="#666666",
            linespacing=1.4)

    ax.text(0.645, 0.610, "on every cold start, inside the Space container",
            fontsize=6.9, ha="center", color="#444444", style="italic")
    xs = [0.370, 0.560, 0.750]
    for i, (x0, label) in enumerate(zip(xs, [
            "seed SQLite\n963 chunks", "embed corpus\nMiniLM-L6-v2", "build FAISS\n+ BM25"])):
        box(ax, x0, 0.405, 0.165, 0.140, label, "#F7F7F7", "#BBBBBB", fontsize=6.9)
        if i:
            arrow(ax, (x0 - 0.025, 0.475), (x0, 0.475), color="#999999")
    arrow(ax, (0.645, 0.670), (0.645, 0.550), color="#999999", ls="--")

    ax.text(0.5, 0.175,
            "No index artifacts are shipped to the Space. Hugging Face rejects binary files in a Space\n"
            "repository whatever their size, and pushed through Git LFS they did not materialise in the\n"
            "running container. The indexes are therefore derived at boot from the corpus just seeded —\n"
            "which also makes it impossible for them to fall out of step with the corpus.",
            fontsize=6.9, ha="center", va="center", color="#222222", linespacing=1.75,
            bbox=dict(boxstyle="round,pad=0.55", facecolor="#FAFAFA", edgecolor="#DDDDDD"))
    fig.savefig(OUT / "fig7_deployment.png")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 8
def fig_verification():
    fig, ax = plt.subplots(figsize=(6.4, 2.7))
    stages = ["Retrieved\nchunks", "Sections the\nanswer names",
              "Grounded?\n(⊆ retrieved)", "Returned to\nuser"]
    note = ["top-k = 10", "extracted by regex", "set containment", "verified: true"]
    xs = [0.5, 1.5, 2.5, 3.5]
    colors = [BLUE, BLUE, PURPLE, GREEN]
    fills = [FILL_B, FILL_B, FILL_P, FILL_G]
    for x, s, n, c, f in zip(xs, stages, note, colors, fills):
        ax.add_patch(FancyBboxPatch((x - 0.42, 0.34), 0.84, 0.34,
                                    boxstyle="round,pad=0.015,rounding_size=0.04",
                                    facecolor=f, edgecolor=c, linewidth=1.0))
        ax.text(x, 0.51, s, ha="center", va="center", fontsize=7.2, linespacing=1.4)
        ax.text(x, 0.25, n, ha="center", va="center", fontsize=6.3, color="#666666", style="italic")
    for a, b in zip(xs, xs[1:]):
        ax.add_patch(FancyArrowPatch((a + 0.42, 0.51), (b - 0.42, 0.51),
                                     arrowstyle="-|>", mutation_scale=10, color="#555555",
                                     shrinkA=0, shrinkB=0))
    # failure path routed above the boxes so it crosses nothing
    ax.add_patch(FancyArrowPatch((2.5, 0.68), (1.5, 0.68), arrowstyle="-|>",
                                 mutation_scale=10, color=RED, shrinkA=0, shrinkB=0,
                                 connectionstyle="arc3,rad=0.55"))
    ax.text(2.0, 0.93, "no → send back to synthesis, at most twice",
            ha="center", fontsize=6.8, color=RED)
    ax.text(3.0, 0.72, "yes", ha="center", fontsize=6.6, color=GREEN, style="italic")
    ax.set_xlim(0, 4); ax.set_ylim(0.14, 1.04); ax.axis("off")
    ax.set_title("Verification: an answer may only cite what retrieval actually returned",
                 fontsize=8.4)
    fig.tight_layout()
    fig.savefig(OUT / "fig8_verification.png")
    plt.close(fig)


for fn in (fig_architecture, fig_hybrid, fig_corpus, fig_recall_scale,
           fig_per_act, fig_tuning, fig_deployment, fig_verification):
    fn()
    print("ok:", fn.__name__)
print("\nwritten to", OUT)
