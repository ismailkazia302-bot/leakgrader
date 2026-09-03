# 🧠 OmniBrain AI — Enterprise Smart Document & Knowledge Agent

> **Next-Generation Autonomous Second-Brain & Document Intelligence SaaS.**
> Outperforms Quivr, ChatPDF, and Danswer in **operating cost (near $0)**, **search accuracy (Hybrid RRF)**, and **feature versatility (Citations, Risk Audit, Table Extraction)**.

---

## 🌟 Key Features & Competitor Edge

| Feature | Typical Tools (Quivr / ChatPDF / Danswer) | **OmniBrain AI** |
| :--- | :--- | :--- |
| **Operating Cost** | $50–$100/mo + heavy Pinecone/Weaviate bills | **Near $0** (Self-contained hybrid store + Gemini Flash) |
| **Search Precision** | Only Vector Similarity (misses exact numbers/IDs) | **Hybrid Search: BM25 + Vector Embeddings with RRF** |
| **Hallucination Control** | High | **Zero-Hallucination Grounded Mode with Exact Source Citations** |
| **Automated Intelligence** | Basic Q&A only | **1-Click Executive Summary, Legal Risk Audit & Table Extractor** |
| **File Formats** | PDF only | **PDF, TXT, Markdown, CSV, JSON, and Web URLs** |
| **Deployment** | 10+ Docker containers | **1-Click Run (`run_agent.bat`) or Python Webhook API** |

---

## 🚀 Quick Start (Running Locally)

### 1. Launch Server
Double-click `run_agent.bat` or run:
```bash
cd c:\Users\Administrator\Downloads\mastermind\omnibrain
python app.py
```

### 2. Open Web Dashboard
Open your browser at:
👉 **[http://localhost:8090](http://localhost:8090)**

---

## 💼 How to Monetize & Make Money with OmniBrain AI

### 1. AI Automation Agency (AAA Retainer Model)
* **Target Clients**: Law firms, Real Estate agencies, Accounting firms, E-commerce brands.
* **Pitch**: *"We integrate your internal contracts, manuals, and FAQs into a private, 100% secure AI assistant that answers employee/client queries in seconds with zero data leaks."*
* **Pricing**:
  * Setup Fee: **$1,500 – $3,500** (one-time setup & document indexing).
  * Monthly Retainer: **$300 – $800/month** (maintenance & updates).

### 2. Micro-SaaS Product (White-Label)
* Rebrand the UI with client's logo & theme.
* Sell seat-based subscriptions ($29/month per team).

---

## 🔌 REST API Endpoints

- `GET /api/documents` : List all indexed files & knowledge vault statistics.
- `POST /api/upload` : Multipart upload files (PDF, DOCX, TXT, CSV, JSON).
- `POST /api/upload-url` : Index web page directly via URL (`{"url": "https://..."}`).
- `POST /api/query` : Hybrid search + grounded Q&A with citations (`{"query": "..."}`).
- `POST /api/summary` : Instant Executive Briefing across all indexed knowledge.
- `POST /api/risk-audit` : Compliance, Legal Liability, & Contract Risk Audit.
- `POST /api/extract-tables` : Extract structured tables, dates, and financial figures.
- `DELETE /api/documents/{id}` : Remove document & auto re-index.
- `POST /api/clear` : Wipe knowledge base.
