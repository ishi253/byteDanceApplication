---
name: gtm-research
description: Use this skill when the user requests Go-to-Market (GTM) research, market analysis, competitive landscape, market sizing, or strategic entry recommendations. Triggers on queries like "GTM analysis for X", "market research for X", "competitive landscape of X", "TAM SAM SOM for X", "go-to-market strategy for X", or any request for structured market/industry research with citations.
---

# GTM (Go-to-Market) Research Skill

## Purpose

Conduct comprehensive Go-to-Market analysis for a given topic. Generate a professional research report with data validation, multi-source cross-reference, and confidence scoring.

## Research Plan Template

When given a GTM research topic, decompose into these sub-tasks:

1. **Market Sizing** — TAM/SAM/SOM estimates with source citations
2. **Competitive Landscape** — Key players, market share, positioning
3. **Customer Segments** — Target demographics, pain points, buying behavior
4. **Regulatory Environment** — Key regulations, compliance requirements
5. **Trends & Outlook** — Growth drivers, emerging trends, forecasts
6. **Go-to-Market Strategy** — Recommended channels, pricing, partnerships

## Data Validation Rules

- Cross-reference every statistic with at least 2 sources when possible
- Flag any data older than 2 years as potentially outdated
- Assign confidence levels:
  - 🟢 **High** — 3+ sources or authoritative single source
  - 🟡 **Medium** — 2 sources
  - 🔴 **Low** — 1 source only
- Note contradictions between sources explicitly in the report

## Report Format

Output a structured report with these sections:

1. **Executive Summary** (3–5 bullet points)
2. **Market Overview & Sizing**
3. **Competitive Landscape** (comparison table where applicable)
4. **Customer & Segment Analysis**
5. **Regulatory & Risk Factors**
6. **Trends & Forward Outlook**
7. **Strategic Recommendations**
8. **Methodology & Sources** (with confidence scores)

## Workflow

1. **Load this skill** at the start of any GTM or market research request.
2. **Use web search** (and optionally `web_fetch` for full articles) to gather data for each sub-task. Prefer recent and authoritative sources.
3. **Apply data validation rules** as you collect and cite data.
4. **Synthesize** into the report format above, including confidence badges (🟢/🟡/🔴) next to key claims where appropriate.
5. If the user has **uploaded documents** (e.g. industry reports), use RAG tools:
   - Prefer **vector RAG** (Milvus):
     - Run `rag_ingest_uploads_vector(thread_id=...)` once after uploads (or after uploads change)
     - Use `rag_search_vector(thread_id=..., query=...)` for each report section to retrieve relevant passages
   - Fallback to **BM25** if vector RAG is not configured/available:
     - Run `rag_ingest_uploads(thread_id=...)` once after uploads (or after uploads change)
     - Use `rag_search(thread_id=..., query=...)` for each report section to retrieve relevant passages
   - Quote retrieved passages and cite the `virtual_path` and `chunk_id` in **Methodology & Sources**

## When to Use

- User asks for market size, TAM/SAM/SOM, or growth rates
- User asks for competitor analysis or competitive landscape
- User asks for go-to-market strategy or entry recommendations
- User asks for industry trends, regulatory overview, or customer segments in a structured way
- User requests a "GTM report", "market research report", or "industry analysis" with citations
