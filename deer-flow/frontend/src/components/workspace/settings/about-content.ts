/**
 * About Meridian markdown content. Inlined to avoid raw-loader dependency
 * (Turbopack cannot resolve raw-loader for .md imports).
 */
export const aboutMarkdown = `# About Meridian

> **AI-Powered GTM Research Agent**

Meridian is a Go-to-Market research agent that produces structured market intelligence reports with TAM/SAM/SOM analysis, competitive landscapes, confidence-scored insights, and full source citations.

---

## Core Capabilities

* **Market Sizing**: Bottom-up and top-down TAM/SAM/SOM estimates with growth projections.
* **Competitive Intelligence**: Key player mapping, market share estimates, and positioning matrices.
* **Customer Segments**: Target segment identification with persona profiles and pain points.
* **Confidence Scoring**: Every claim is cross-referenced and scored: High (3+ sources), Medium (2), or Low (1).
* **PDF & Data Ingestion**: Upload proprietary reports for RAG-powered enrichment.

---

## Built On

Meridian is built on [DeerFlow](https://github.com/bytedance/deer-flow), an open-source super agent framework by ByteDance.

### Core Frameworks
- **[LangChain](https://github.com/langchain-ai/langchain)**: Powers LLM interactions and chains.
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Enables multi-agent orchestration.
- **[Next.js](https://nextjs.org/)**: Frontend framework.

---

## License

Distributed under the **MIT License**.
`;
