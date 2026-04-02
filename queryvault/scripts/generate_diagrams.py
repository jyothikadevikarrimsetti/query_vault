#!/usr/bin/env python3.12
"""Generate data flow diagrams for QueryVault, XenSQL, and combined architecture."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# ── Colour palette ──────────────────────────────────────────

BG          = "#0F172A"
CARD_BG     = "#1E293B"
CARD_BORDER = "#334155"
WHITE       = "#F8FAFC"
LIGHT_GRAY  = "#94A3B8"
DARK_GRAY   = "#64748B"

BLUE        = "#3B82F6"
LIGHT_BLUE  = "#93C5FD"
GREEN       = "#10B981"
RED         = "#EF4444"
AMBER       = "#F59E0B"
PURPLE      = "#8B5CF6"
PINK        = "#EC4899"
CYAN        = "#06B6D4"
TEAL        = "#14B8A6"
INDIGO      = "#6366F1"
ORANGE      = "#F97316"

# ── Drawing helpers ─────────────────────────────────────────

def draw_box(ax, x, y, w, h, text, color=BLUE, text_color=WHITE,
             fontsize=10, bold=True, alpha=0.9, border_color=None,
             sub_text=None, sub_color=LIGHT_GRAY, sub_size=8,
             rounded=True, fill_color=None):
    """Draw a rounded rectangle with centered text."""
    fc = fill_color or color
    bc = border_color or color

    if rounded:
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.02",
            facecolor=fc, edgecolor=bc,
            linewidth=1.5, alpha=alpha,
            transform=ax.transData,
        )
    else:
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="square,pad=0",
            facecolor=fc, edgecolor=bc,
            linewidth=1.5, alpha=alpha,
        )

    ax.add_patch(box)

    weight = "bold" if bold else "normal"
    ax.text(x, y + (0.15 if sub_text else 0), text,
            ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight=weight, fontfamily="sans-serif")

    if sub_text:
        ax.text(x, y - 0.25, sub_text,
                ha="center", va="center", fontsize=sub_size,
                color=sub_color, fontweight="normal", fontfamily="sans-serif")

    return box


def draw_arrow(ax, x1, y1, x2, y2, color=LIGHT_GRAY, style="-|>",
               linewidth=1.5, linestyle="-", label=None, label_color=None):
    """Draw an arrow between two points."""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        mutation_scale=12,
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
    )
    ax.add_patch(arrow)

    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.2, label,
                ha="center", va="center", fontsize=7,
                color=label_color or color, fontweight="normal",
                fontfamily="sans-serif",
                bbox=dict(boxstyle="round,pad=0.15", facecolor=BG, edgecolor="none", alpha=0.8))


def draw_zone_label(ax, x, y, text, color=BLUE):
    """Draw a zone label badge."""
    ax.text(x, y, text, ha="center", va="center", fontsize=8,
            color=BG, fontweight="bold", fontfamily="sans-serif",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor=color))


def draw_section_bg(ax, x, y, w, h, color=CARD_BG, border=CARD_BORDER, alpha=0.6):
    """Draw a section background."""
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.05",
        facecolor=color, edgecolor=border,
        linewidth=1, alpha=alpha,
    )
    ax.add_patch(box)
    return box


def setup_canvas(figsize=(20, 14), title=""):
    """Set up a dark-themed canvas."""
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-0.5, 20.5)
    ax.set_ylim(-0.5, 14.5)
    ax.set_aspect("equal")
    ax.axis("off")

    if title:
        ax.text(10.25, 14.0, title,
                ha="center", va="center", fontsize=20,
                color=WHITE, fontweight="bold", fontfamily="sans-serif")

    return fig, ax


# ═══════════════════════════════════════════════════════════
# DIAGRAM 1: QueryVault Security Pipeline
# ═══════════════════════════════════════════════════════════

def generate_queryvault_diagram():
    fig, ax = setup_canvas((22, 16), "QueryVault — 5-Zone Security Pipeline Data Flow")

    # ── Entry point ──
    draw_box(ax, 2.5, 13.0, 3.5, 1.0, "User Question", BLUE, WHITE, 12,
             sub_text="Natural Language + JWT Token")
    draw_arrow(ax, 2.5, 12.4, 2.5, 11.8, LIGHT_BLUE, linewidth=2)

    # ── ZONE 1: PRE-MODEL ──
    draw_section_bg(ax, 10.5, 10.8, 20, 2.8)
    draw_zone_label(ax, 0.8, 11.8, "ZONE 1", RED)
    ax.text(2.0, 11.8, "PRE-MODEL", ha="left", va="center", fontsize=11,
            color=RED, fontweight="bold", fontfamily="sans-serif")

    z1_boxes = [
        (3.0, 10.8, "JWT\nValidation", RED, "RS256 verify\nexpiry check"),
        (6.0, 10.8, "Employment\nStatus Check", RED, "ACTIVE/TERMINATED\nverification"),
        (9.0, 10.8, "Injection\nScanner", RED, "212 patterns\n8 categories"),
        (12.0, 10.8, "Schema\nProbing", RED, "24h sliding\nwindow"),
        (15.0, 10.8, "Behavioral\nFingerprint", RED, "30-day user\nprofile"),
        (18.0, 10.8, "Threat\nClassifier", RED, "Weighted score\nCRITICAL→NONE"),
    ]
    for x, y, txt, c, sub in z1_boxes:
        draw_box(ax, x, y, 2.4, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    # Z1 arrows
    for i in range(len(z1_boxes) - 1):
        x1 = z1_boxes[i][0] + 1.2
        x2 = z1_boxes[i+1][0] - 1.2
        draw_arrow(ax, x1, 10.8, x2, 10.8, DARK_GRAY, linewidth=1)

    # Block path from threat classifier
    draw_box(ax, 19.8, 12.5, 1.8, 0.8, "BLOCKED", RED, WHITE, 9,
             fill_color="#7F1D1D", sub_text="+ Audit log")
    draw_arrow(ax, 18.0, 11.6, 19.8, 12.1, RED, linewidth=1.5, label="threat ≥ HIGH")

    # Z1 → Z2
    draw_arrow(ax, 10.5, 9.3, 10.5, 8.8, GREEN, linewidth=2, label="PASSED")

    # ── ZONE 2: MODEL BOUNDARY ──
    draw_section_bg(ax, 10.5, 7.7, 20, 2.6)
    draw_zone_label(ax, 0.8, 8.8, "ZONE 2", AMBER)
    ax.text(2.0, 8.8, "MODEL BOUNDARY", ha="left", va="center", fontsize=11,
            color=AMBER, fontweight="bold", fontfamily="sans-serif")

    z2_boxes = [
        (3.5, 7.7, "RBAC Policy\nResolution", AMBER, "Role→tables,\noperations, filters"),
        (7.5, 7.7, "Column\nScoping", AMBER, "VISIBLE/MASKED\n/HIDDEN per role"),
        (11.5, 7.7, "Context\nMinimization", AMBER, "Filter schema to\nleast-privilege"),
        (15.5, 7.7, "Contextual\nRules", AMBER, "Row filters as\nNL constraints"),
    ]
    for x, y, txt, c, sub in z2_boxes:
        draw_box(ax, x, y, 2.8, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    for i in range(len(z2_boxes) - 1):
        x1 = z2_boxes[i][0] + 1.4
        x2 = z2_boxes[i+1][0] - 1.4
        draw_arrow(ax, x1, 7.7, x2, 7.7, DARK_GRAY, linewidth=1)

    # Neo4j data source
    draw_box(ax, 19.0, 7.7, 2.2, 1.2, "Neo4j\nGraph DB", PURPLE, WHITE, 9,
             sub_text="Policies & roles")
    draw_arrow(ax, 17.8, 7.7, 17.9, 7.7, PURPLE, linewidth=1, linestyle="--")

    # Z2 → XenSQL (AI model)
    draw_arrow(ax, 10.5, 6.3, 10.5, 5.9, AMBER, linewidth=2)

    # ── AI MODEL ──
    draw_box(ax, 10.5, 5.3, 4.0, 1.2, "XenSQL (NL→SQL)", BLUE, WHITE, 13,
             sub_text="Filtered schema + rules → SQL", bold=True)
    draw_arrow(ax, 10.5, 4.6, 10.5, 4.1, BLUE, linewidth=2, label="Generated SQL")

    # ── ZONE 3: POST-MODEL ──
    draw_section_bg(ax, 10.5, 3.0, 20, 2.6)
    draw_zone_label(ax, 0.8, 4.0, "ZONE 3", BLUE)
    ax.text(2.0, 4.0, "POST-MODEL", ha="left", va="center", fontsize=11,
            color=BLUE, fontweight="bold", fontfamily="sans-serif")

    z3_boxes = [
        (3.0, 3.0, "Gate 1:\nStructural", BLUE, "Table/column auth\nsubquery depth"),
        (6.5, 3.0, "Gate 2:\nClassification", BLUE, "Sensitivity vs\nclearance (L1-L5)"),
        (10.0, 3.0, "Gate 3:\nBehavioral", BLUE, "Write ops, UNION,\nsystem tables"),
        (13.5, 3.0, "Hallucination\nDetection", CYAN, "Validate tables &\ncolumns exist"),
        (17.0, 3.0, "Query\nRewriter", TEAL, "Auto-mask, inject\nrow filters, LIMIT"),
    ]
    for x, y, txt, c, sub in z3_boxes:
        draw_box(ax, x, y, 2.6, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    # Parallel indicator for gates 1-3
    ax.text(6.5, 4.05, "▸ Run in parallel", ha="center", va="center",
            fontsize=7, color=DARK_GRAY, fontstyle="italic", fontfamily="sans-serif")

    draw_arrow(ax, 4.3, 3.0, 5.2, 3.0, DARK_GRAY, linewidth=1)
    draw_arrow(ax, 7.8, 3.0, 8.7, 3.0, DARK_GRAY, linewidth=1)
    draw_arrow(ax, 11.3, 3.0, 12.2, 3.0, DARK_GRAY, linewidth=1)
    draw_arrow(ax, 14.8, 3.0, 15.7, 3.0, DARK_GRAY, linewidth=1)

    # Gate fail path
    draw_box(ax, 19.8, 4.0, 1.8, 0.8, "BLOCKED", RED, WHITE, 9,
             fill_color="#7F1D1D", sub_text="+ Violations")
    draw_arrow(ax, 10.0, 3.8, 19.0, 4.0, RED, linewidth=1, linestyle="--", label="Any gate FAIL")

    # Z3 → Z4
    draw_arrow(ax, 10.5, 1.6, 10.5, 1.1, GREEN, linewidth=2, label="Rewritten SQL")

    # ── ZONE 4 & 5 (compact) ──
    draw_section_bg(ax, 10.5, 0.2, 20, 1.4)
    draw_zone_label(ax, 0.8, 0.65, "ZONE 4", GREEN)
    ax.text(2.0, 0.65, "EXECUTION", ha="left", va="center", fontsize=10,
            color=GREEN, fontweight="bold", fontfamily="sans-serif")

    z4_boxes = [
        (4.5, 0.2, "Circuit\nBreaker", GREEN),
        (7.5, 0.2, "Read-Only\nEnforcement", GREEN),
        (10.5, 0.2, "Multi-DB\nRouter", GREEN),
        (13.5, 0.2, "Query\nExecution", GREEN),
    ]
    for x, y, txt, c in z4_boxes:
        draw_box(ax, x, y, 2.2, 1.0, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=8)

    for i in range(len(z4_boxes) - 1):
        x1 = z4_boxes[i][0] + 1.1
        x2 = z4_boxes[i+1][0] - 1.1
        draw_arrow(ax, x1, 0.2, x2, 0.2, DARK_GRAY, linewidth=1)

    # Databases
    dbs = [
        (16.5, 0.6, "ApolloHIS\nMySQL", BLUE),
        (16.5, -0.2, "ApolloHR\nMySQL", PINK),
        (19.0, 0.6, "Financial\nPostgreSQL", GREEN),
        (19.0, -0.2, "Analytics\nPostgreSQL", CYAN),
    ]
    for x, y, txt, c in dbs:
        draw_box(ax, x, y, 2.0, 0.7, txt, fill_color=CARD_BG, border_color=c,
                 text_color=c, fontsize=7)

    draw_arrow(ax, 14.6, 0.2, 15.5, 0.4, DARK_GRAY, linewidth=1)

    # Zone 5 audit trail
    draw_zone_label(ax, 0.8, -0.3, "ZONE 5", LIGHT_BLUE)
    ax.text(2.0, -0.3, "CONTINUOUS — SHA-256 Hash-Chain Audit Trail → Every event logged",
            ha="left", va="center", fontsize=9, color=LIGHT_BLUE,
            fontweight="normal", fontfamily="sans-serif")

    # Save
    out = "QueryVault_DataFlow.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=BG, pad_inches=0.3)
    plt.close(fig)
    print(f"  Generated: {out}")
    return out


# ═══════════════════════════════════════════════════════════
# DIAGRAM 2: XenSQL NL-to-SQL Pipeline
# ═══════════════════════════════════════════════════════════

def generate_xensql_diagram():
    fig, ax = setup_canvas((20, 14), "XenSQL — NL-to-SQL Pipeline Data Flow")

    # ── Input ──
    draw_box(ax, 3, 12.5, 4.0, 1.2, "Natural Language Question", BLUE, WHITE, 12,
             sub_text="\"Show me patient names from cardiology\"")
    draw_arrow(ax, 3, 11.8, 3, 11.2, LIGHT_BLUE, linewidth=2)

    # ── Schema Context ──
    draw_section_bg(ax, 10.5, 10.2, 19, 2.4)
    ax.text(1.3, 11.2, "SCHEMA CONTEXT", ha="left", va="center", fontsize=11,
            color=PURPLE, fontweight="bold", fontfamily="sans-serif")

    schema_boxes = [
        (3.5, 10.2, "Filtered\nSchema", PURPLE, "Tables & columns\nper RBAC policy"),
        (7.5, 10.2, "Contextual\nRules", AMBER, "NL constraints\nrow filters, limits"),
        (11.5, 10.2, "Dialect\nHint", CYAN, "MySQL 8.0 or\nPostgreSQL 16"),
        (15.5, 10.2, "Session\nContext", TEAL, "User ID, roles\nclearance level"),
    ]
    for x, y, txt, c, sub in schema_boxes:
        draw_box(ax, x, y, 2.8, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=10, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    # All feed into pipeline
    for x, _, _, _, _ in schema_boxes:
        draw_arrow(ax, x, 9.4, 10.5, 8.8, DARK_GRAY, linewidth=1)

    # ── Vector Store ──
    draw_box(ax, 19.0, 10.2, 2.2, 1.2, "pgvector\nStore", INDIGO, WHITE, 9,
             sub_text="Schema embeddings")

    # ── Pipeline Core ──
    draw_section_bg(ax, 10.5, 7.3, 19, 3.4)
    ax.text(1.3, 8.7, "XENSQL PIPELINE", ha="left", va="center", fontsize=11,
            color=BLUE, fontweight="bold", fontfamily="sans-serif")

    # Step 1: Schema retrieval
    draw_box(ax, 3.5, 7.5, 3.2, 1.2, "1. Schema Retrieval", BLUE, WHITE, 10,
             sub_text="Vector similarity search\nfind relevant tables")
    draw_arrow(ax, 5.1, 7.5, 6.4, 7.5, LIGHT_BLUE, linewidth=1.5)

    # Step 2: Prompt construction
    draw_box(ax, 8.0, 7.5, 3.0, 1.2, "2. Prompt\nConstruction", AMBER, WHITE, 10,
             sub_text="DDL + rules + question")
    draw_arrow(ax, 9.5, 7.5, 10.8, 7.5, AMBER, linewidth=1.5)

    # Step 3: LLM call
    draw_box(ax, 12.5, 7.5, 3.0, 1.2, "3. LLM Generation", GREEN, WHITE, 10,
             sub_text="Azure OpenAI GPT-4.1")
    draw_arrow(ax, 14.0, 7.5, 15.3, 7.5, GREEN, linewidth=1.5)

    # Step 4: SQL extraction
    draw_box(ax, 17.0, 7.5, 3.0, 1.2, "4. SQL Extraction\n& Validation", TEAL, WHITE, 10,
             sub_text="Parse response → clean SQL")

    # Vector store connection
    draw_arrow(ax, 19.0, 9.5, 19.0, 8.8, INDIGO, linewidth=1, linestyle="--")
    draw_arrow(ax, 4.5, 8.2, 18.5, 9.5, INDIGO, linewidth=1, linestyle="--", label="embedding lookup")

    # ── LLM Detail ──
    draw_section_bg(ax, 10.5, 4.7, 19, 2.4)
    ax.text(1.3, 5.7, "LLM PROCESSING", ha="left", va="center", fontsize=11,
            color=GREEN, fontweight="bold", fontfamily="sans-serif")

    llm_boxes = [
        (3.0, 4.7, "System\nPrompt", GREEN, "SQL expert persona\ndialect-specific rules"),
        (7.0, 4.7, "Schema\nDDL", PURPLE, "CREATE TABLE stmts\nwith column types"),
        (11.0, 4.7, "Row Filter\nRules", AMBER, "\"Include WHERE\nfacility_id = ...\""),
        (15.0, 4.7, "User\nQuestion", BLUE, "Original natural\nlanguage query"),
        (19.0, 4.7, "Generated\nSQL", TEAL, "SELECT p.first_name\nFROM patients p..."),
    ]
    for x, y, txt, c, sub in llm_boxes:
        draw_box(ax, x, y, 2.8, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    for i in range(len(llm_boxes) - 1):
        x1 = llm_boxes[i][0] + 1.4
        x2 = llm_boxes[i+1][0] - 1.4
        draw_arrow(ax, x1, 4.7, x2, 4.7, DARK_GRAY, linewidth=1)

    # Connection from pipeline to LLM
    draw_arrow(ax, 12.5, 6.8, 12.5, 6.0, GREEN, linewidth=1.5)

    # ── Output ──
    draw_section_bg(ax, 10.5, 2.3, 19, 2.0)
    ax.text(1.3, 3.1, "OUTPUT", ha="left", va="center", fontsize=11,
            color=CYAN, fontweight="bold", fontfamily="sans-serif")

    out_boxes = [
        (3.5, 2.3, "SQL\nStatement", CYAN, "Dialect-specific\nvalid SQL"),
        (7.5, 2.3, "Confidence\nScore", GREEN, "0.0 – 1.0\nreliability"),
        (11.5, 2.3, "Ambiguity\nFlags", AMBER, "Multiple possible\ninterpretations"),
        (15.5, 2.3, "Tables\nUsed", PURPLE, "Referenced tables\nfor routing"),
        (19.0, 2.3, "Dialect\nDetected", TEAL, "MySQL / PostgreSQL\nauto-detected"),
    ]
    for x, y, txt, c, sub in out_boxes:
        draw_box(ax, x, y, 2.6, 1.2, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)

    draw_arrow(ax, 17.0, 6.8, 10.5, 3.4, CYAN, linewidth=1.5)

    # Arrow to QueryVault
    draw_box(ax, 10.5, 0.8, 6.0, 1.0, "→ QueryVault Post-Model Validation", BLUE, WHITE, 11,
             sub_text="3-gate validation, hallucination check, rewriting")
    draw_arrow(ax, 10.5, 1.6, 10.5, 1.4, BLUE, linewidth=2)

    out = "XenSQL_DataFlow.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=BG, pad_inches=0.3)
    plt.close(fig)
    print(f"  Generated: {out}")
    return out


# ═══════════════════════════════════════════════════════════
# DIAGRAM 3: Combined Architecture
# ═══════════════════════════════════════════════════════════

def generate_combined_diagram():
    fig, ax = setup_canvas((24, 18), "QueryVault + XenSQL — Combined Architecture Data Flow")
    ax.set_xlim(-1, 25)
    ax.set_ylim(-1.5, 18)

    # ── USER LAYER ──
    draw_section_bg(ax, 12, 16.5, 24, 1.8)
    ax.text(0.3, 17.2, "USER LAYER", ha="left", va="center", fontsize=10,
            color=LIGHT_GRAY, fontweight="bold", fontfamily="sans-serif")

    draw_box(ax, 4, 16.5, 3.5, 1.0, "React Dashboard", BLUE, WHITE, 11,
             sub_text="Login, Query, Policy Config")
    draw_box(ax, 9, 16.5, 3.0, 1.0, "REST API Client", CYAN, WHITE, 11,
             sub_text="JWT authenticated")
    draw_box(ax, 14, 16.5, 3.5, 1.0, "Role-Based Login", PURPLE, WHITE, 11,
             sub_text="17 roles, 5 clearance levels")
    draw_box(ax, 19.5, 16.5, 3.0, 1.0, "Policy Admin", AMBER, WHITE, 11,
             sub_text="Configure RBAC policies")

    draw_arrow(ax, 9, 15.9, 9, 15.2, LIGHT_BLUE, linewidth=2, label="POST /api/v1/gateway/query")

    # ── QUERYVAULT API LAYER ──
    draw_section_bg(ax, 12, 14.2, 24, 1.8)
    ax.text(0.3, 15.0, "QUERYVAULT API", ha="left", va="center", fontsize=10,
            color=RED, fontweight="bold", fontfamily="sans-serif")

    draw_box(ax, 4, 14.2, 3.0, 1.0, "Gateway\nOrchestrator", RED, WHITE, 10, sub_text="FastAPI :8950")
    draw_box(ax, 8.5, 14.2, 2.5, 1.0, "Policy\nRoutes", AMBER, WHITE, 10, sub_text="CRUD endpoints")
    draw_box(ax, 12.5, 14.2, 2.5, 1.0, "Auth\nMiddleware", PURPLE, WHITE, 10, sub_text="JWT + session")
    draw_box(ax, 16.5, 14.2, 2.5, 1.0, "Compliance\nEngine", GREEN, WHITE, 10, sub_text="7 frameworks")
    draw_box(ax, 20.5, 14.2, 2.5, 1.0, "Threat\nAnalytics", RED, WHITE, 10, sub_text="Alerts & reports")

    draw_arrow(ax, 4, 13.6, 4, 12.8, RED, linewidth=2)

    # ── ZONE 1: PRE-MODEL ──
    draw_section_bg(ax, 12, 11.8, 24, 2.2)
    draw_zone_label(ax, 0.5, 12.7, "ZONE 1", RED)
    ax.text(1.5, 12.7, "PRE-MODEL", ha="left", va="center", fontsize=10,
            color=RED, fontweight="bold", fontfamily="sans-serif")

    z1 = [
        (3.5, 11.8, "JWT\nValidation", RED),
        (6.5, 11.8, "Employment\nCheck", RED),
        (9.5, 11.8, "Injection\nScanner", RED),
        (12.5, 11.8, "Schema\nProbing", RED),
        (15.5, 11.8, "Behavioral\nProfile", RED),
        (18.5, 11.8, "Threat\nClassifier", RED),
    ]
    for x, y, txt, c in z1:
        draw_box(ax, x, y, 2.2, 1.0, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=8)
    for i in range(len(z1)-1):
        draw_arrow(ax, z1[i][0]+1.1, 11.8, z1[i+1][0]-1.1, 11.8, DARK_GRAY, linewidth=1)

    # Block path
    draw_box(ax, 22.0, 12.5, 2.0, 0.7, "BLOCKED", RED, WHITE, 8, fill_color="#7F1D1D")
    draw_arrow(ax, 19.6, 12.0, 21.0, 12.4, RED, linewidth=1)

    draw_arrow(ax, 12, 10.6, 12, 10.1, GREEN, linewidth=2)

    # ── ZONE 2: MODEL BOUNDARY ──
    draw_section_bg(ax, 12, 9.2, 24, 2.2)
    draw_zone_label(ax, 0.5, 10.0, "ZONE 2", AMBER)
    ax.text(1.5, 10.0, "MODEL BOUNDARY", ha="left", va="center", fontsize=10,
            color=AMBER, fontweight="bold", fontfamily="sans-serif")

    z2 = [
        (3.5, 9.2, "RBAC Policy\nResolution", AMBER),
        (7.5, 9.2, "Column\nScoping", AMBER),
        (11.5, 9.2, "Context\nMinimization", AMBER),
        (15.5, 9.2, "Contextual\nRules", AMBER),
        (19.5, 9.2, "Dialect\nResolution", AMBER),
    ]
    for x, y, txt, c in z2:
        draw_box(ax, x, y, 2.8, 1.0, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=8)
    for i in range(len(z2)-1):
        draw_arrow(ax, z2[i][0]+1.4, 9.2, z2[i+1][0]-1.4, 9.2, DARK_GRAY, linewidth=1)

    # Neo4j
    draw_box(ax, 22.5, 9.2, 2.2, 1.0, "Neo4j", PURPLE, WHITE, 10,
             sub_text="Graph DB")
    draw_arrow(ax, 20.9, 9.2, 21.4, 9.2, PURPLE, linewidth=1, linestyle="--")

    draw_arrow(ax, 12, 8.1, 12, 7.5, AMBER, linewidth=2, label="filtered schema + rules")

    # ── XENSQL PIPELINE ──
    draw_section_bg(ax, 12, 6.5, 24, 2.4)
    ax.text(0.3, 7.5, "XENSQL PIPELINE", ha="left", va="center", fontsize=10,
            color=BLUE, fontweight="bold", fontfamily="sans-serif")
    ax.text(4.8, 7.5, "(NL → SQL)", ha="left", va="center", fontsize=9,
            color=DARK_GRAY, fontfamily="sans-serif")

    xen = [
        (3.5, 6.3, "Schema\nRetrieval", BLUE, "pgvector\nsimilarity"),
        (7.5, 6.3, "Prompt\nConstruction", AMBER, "DDL + rules\n+ question"),
        (11.5, 6.3, "LLM Call\n(GPT-4.1)", GREEN, "Azure OpenAI\nSQL generation"),
        (15.5, 6.3, "SQL\nExtraction", TEAL, "Parse & clean\nraw SQL"),
        (19.5, 6.3, "Confidence\nScoring", CYAN, "Reliability\n0.0 – 1.0"),
    ]
    for x, y, txt, c, sub in xen:
        draw_box(ax, x, y, 2.8, 1.4, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=9, sub_text=sub, sub_size=7, sub_color=DARK_GRAY)
    for i in range(len(xen)-1):
        draw_arrow(ax, xen[i][0]+1.4, 6.3, xen[i+1][0]-1.4, 6.3, DARK_GRAY, linewidth=1)

    # pgvector
    draw_box(ax, 22.5, 6.8, 2.2, 1.0, "pgvector", INDIGO, WHITE, 10,
             sub_text="Embeddings")
    draw_arrow(ax, 4.5, 7.1, 21.4, 6.8, INDIGO, linewidth=1, linestyle="--")

    draw_arrow(ax, 12, 5.5, 12, 4.9, BLUE, linewidth=2, label="generated SQL")

    # ── ZONE 3: POST-MODEL ──
    draw_section_bg(ax, 12, 3.9, 24, 2.4)
    draw_zone_label(ax, 0.5, 4.9, "ZONE 3", BLUE)
    ax.text(1.5, 4.9, "POST-MODEL", ha="left", va="center", fontsize=10,
            color=BLUE, fontweight="bold", fontfamily="sans-serif")

    z3 = [
        (3.0, 3.7, "Gate 1:\nStructural", BLUE),
        (6.5, 3.7, "Gate 2:\nClassification", BLUE),
        (10.0, 3.7, "Gate 3:\nBehavioral", BLUE),
        (13.5, 3.7, "Hallucination\nDetection", CYAN),
        (17.0, 3.7, "Query\nRewriter", TEAL),
    ]
    for x, y, txt, c in z3:
        draw_box(ax, x, y, 2.6, 1.2, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=8)
    for i in range(len(z3)-1):
        draw_arrow(ax, z3[i][0]+1.3, 3.7, z3[i+1][0]-1.3, 3.7, DARK_GRAY, linewidth=1)

    ax.text(6.5, 4.55, "▸ Gates 1-3 run in parallel", ha="center", va="center",
            fontsize=7, color=DARK_GRAY, fontstyle="italic", fontfamily="sans-serif")

    # Block
    draw_box(ax, 22.0, 4.2, 2.0, 0.7, "BLOCKED", RED, WHITE, 8, fill_color="#7F1D1D")
    draw_arrow(ax, 13.5, 4.4, 21.0, 4.2, RED, linewidth=1, linestyle="--", label="gate FAIL / hallucination")

    draw_arrow(ax, 12, 2.9, 12, 2.4, GREEN, linewidth=2, label="rewritten SQL")

    # ── ZONE 4: EXECUTION ──
    draw_section_bg(ax, 12, 1.5, 24, 2.0)
    draw_zone_label(ax, 0.5, 2.3, "ZONE 4", GREEN)
    ax.text(1.5, 2.3, "EXECUTION", ha="left", va="center", fontsize=10,
            color=GREEN, fontweight="bold", fontfamily="sans-serif")

    z4 = [
        (3.5, 1.3, "Circuit\nBreaker", GREEN),
        (7.0, 1.3, "Read-Only\nCheck", GREEN),
        (10.5, 1.3, "Multi-DB\nRouter", GREEN),
    ]
    for x, y, txt, c in z4:
        draw_box(ax, x, y, 2.4, 1.0, txt, fill_color=CARD_BG, border_color=c,
                 text_color=WHITE, fontsize=8)
    for i in range(len(z4)-1):
        draw_arrow(ax, z4[i][0]+1.2, 1.3, z4[i+1][0]-1.2, 1.3, DARK_GRAY, linewidth=1)

    # Databases
    dbs = [
        (14.5, 1.8, "ApolloHIS\nMySQL 8.0", BLUE),
        (17.5, 1.8, "ApolloHR\nMySQL 8.0", PINK),
        (14.5, 0.6, "Financial\nPostgreSQL", GREEN),
        (17.5, 0.6, "Analytics\nPostgreSQL", CYAN),
    ]
    for x, y, txt, c in dbs:
        draw_box(ax, x, y, 2.5, 0.9, txt, fill_color=CARD_BG, border_color=c,
                 text_color=c, fontsize=8)

    draw_arrow(ax, 11.7, 1.3, 13.2, 1.5, DARK_GRAY, linewidth=1)

    # Results back
    draw_box(ax, 21, 1.3, 3.5, 1.0, "Filtered Results\n+ Security Summary", GREEN, WHITE, 9,
             sub_text="→ Dashboard")
    draw_arrow(ax, 18.8, 1.3, 19.2, 1.3, GREEN, linewidth=1.5)

    # ── ZONE 5: CONTINUOUS ──
    draw_section_bg(ax, 12, -0.5, 24, 1.0)
    draw_zone_label(ax, 0.5, -0.5, "ZONE 5", LIGHT_BLUE)
    ax.text(1.5, -0.5, "CONTINUOUS", ha="left", va="center", fontsize=10,
            color=LIGHT_BLUE, fontweight="bold", fontfamily="sans-serif")

    z5 = [
        (6, -0.5, "SHA-256 Hash-Chain Audit Trail", LIGHT_BLUE),
        (13, -0.5, "Anomaly Detection (6 models)", AMBER),
        (19.5, -0.5, "Compliance Reports (7 frameworks)", GREEN),
    ]
    for x, y, txt, c in z5:
        draw_box(ax, x, y, 4.5, 0.7, txt, fill_color=CARD_BG, border_color=c,
                 text_color=c, fontsize=8)

    # Redis
    draw_box(ax, 23, 11.8, 2.0, 0.8, "Redis", ORANGE, WHITE, 9, sub_text="Sessions & cache")

    out = "Combined_Architecture.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=BG, pad_inches=0.3)
    plt.close(fig)
    print(f"  Generated: {out}")
    return out


# ── Main ────────────────────────────────────────────────────

def main():
    print("\nGenerating data flow diagrams...\n")
    generate_queryvault_diagram()
    generate_xensql_diagram()
    generate_combined_diagram()
    print(f"\nDone! All 3 diagrams saved as PNG.\n")


if __name__ == "__main__":
    main()
