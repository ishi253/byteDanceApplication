---
name: gtm-research
description: Use this skill when the user requests Go-to-Market (GTM) research, market analysis, competitive landscape, market sizing, or strategic entry recommendations. Triggers on queries like "GTM analysis for X", "market research for X", "competitive landscape of X", "TAM SAM SOM for X", "go-to-market strategy for X", or any request for structured market/industry research with citations.
---

# GTM (Go-to-Market) Research Skill

## Purpose

Conduct comprehensive Go-to-Market analysis for a given topic. Generate a professional research report with source-linked data collection, automated fact-checking, multi-source cross-reference, and confidence scoring.

## Research Plan Template

When given a GTM research topic, decompose into these sub-tasks:

1. **Market Sizing** — TAM/SAM/SOM estimates with source citations
2. **Competitive Landscape** — Key players, market share, positioning
3. **Customer Segments** — Target demographics, pain points, buying behavior
4. **Regulatory Environment** — Key regulations, compliance requirements
5. **Trends & Outlook** — Growth drivers, emerging trends, forecasts
6. **Go-to-Market Strategy** — Recommended channels, pricing, partnerships

## Data Validation Rules

- **Every statistic must be stored** via `store_data_point` with source URL, name, and date
- Cross-reference every statistic with at least 2 sources when possible
- Flag any data older than 2 years as potentially outdated
- Run `fact_check` after data collection to detect contradictions and anomalies
- Assign confidence levels:
  - 🟢 **High** — 3+ sources, verified by fact_check, no flags
  - 🟡 **Medium** — 2 sources, or minor flags resolved
  - 🔴 **Low** — 1 source, unresolved contradiction, or anomaly
- Note contradictions between sources explicitly with both values and citations

## Report Format

Output a structured report with these sections:

1. **Executive Summary** (3–5 bullet points)
2. **Market Overview & Sizing**
3. **Competitive Landscape** (comparison table where applicable)
4. **Customer & Segment Analysis**
5. **Regulatory & Risk Factors**
6. **Trends & Forward Outlook**
7. **Strategic Recommendations**
8. **Methodology & Sources** (with confidence scores and audit trail)

## Workflow

### Step 1: Assess Available Data
- If user uploaded files, run `list_uploaded_data_files(thread_id=...)`
- For spreadsheets/CSVs: use `extract_structured_data(...)` to get table data
- For documents: ingest via RAG (`rag_ingest_uploads_vector` or `rag_ingest_uploads`)

### Step 2: Research with Source Tracking
For each sub-task (Market Sizing, Competitive, etc.):
- Use `web_search` and `web_fetch` to gather data
- Use `rag_search_vector` / `rag_search` to query uploaded documents
- **For every key statistic or claim**, call `store_data_point(...)` with:
  - Full source attribution (URL, name, date)
  - Confidence level based on source authority
  - Source type: "web", "uploaded", or "derived"

### Step 3: Fact-Check & Review Pass
After all research sub-tasks complete:
- Run `fact_check(thread_id=...)` to validate all collected data
- Review the issues report:
  - For contradictions: research further to resolve, or note both values
  - For stale data: search for updated figures
  - For single-source claims: attempt to find corroborating source
  - For outliers: verify the anomalous value is accurate
- Store any corrected values via `store_data_point(...)` with updated source
- **If subagents are enabled**: delegate the review to `fact-check-reviewer` subagent

### Step 4: Assemble Report with Provenance
- Call `get_sourced_data(thread_id=...)` to get all verified data points
- Build each report section using the sourced data
- Every key claim must include inline citation: `[Source Name, Date](URL)`
- Apply confidence badges based on fact-check results:
  - 🟢 High — verified by 2+ sources, no issues flagged
  - 🟡 Medium — single source or minor flag (e.g., data from 2024)
  - 🔴 Low — contradiction unresolved, or significant anomaly

### Step 5: Methodology & Audit Trail
The final section must include:
- Complete source list with URLs and dates
- Data points that were corrected during review (original → corrected)
- Coverage summary: which sections have strong/weak data support
- Confidence distribution: how many claims are 🟢/🟡/🔴

## When to Use

- User asks for market size, TAM/SAM/SOM, or growth rates
- User asks for competitor analysis or competitive landscape
- User asks for go-to-market strategy or entry recommendations
- User asks for industry trends, regulatory overview, or customer segments in a structured way
- User requests a "GTM report", "market research report", or "industry analysis" with citations
