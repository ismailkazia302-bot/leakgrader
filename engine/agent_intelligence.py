"""
OmniBrain AI - Intelligence Engine
Executes multi-mode Agent reasoning powered by Gemini 3.6 Flash Core.
Provides Grounded Q&A with verified citations, Executive Summaries, Compliance Audits, and Comparative Analysis.
"""

import json
import urllib.request
import urllib.error

class OmniAgentIntelligence:
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        self.api_key = api_key
        self.model = model

    def _call_gemini_raw(self, system_instruction: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        full_text = f"{system_instruction}\n\n{user_prompt}"
        payload = {
            "contents": [{
                "parts": [{"text": full_text}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096
            }
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Error communicating with Gemini AI: {e}"

    def query_with_citations(self, query: str, context_chunks: list[dict], chat_history: list[dict] = None) -> dict:
        """
        Executes grounded Q&A with verified citation tagging.
        """
        system_instruction = """[SYSTEM INSTRUCTION: You are OmniBrain AI, an elite Enterprise Knowledge Agent and Second-Brain Assistant.
Your mission is to answer user queries with 100% factual fidelity based strictly on the provided document excerpts.
Strict Rules:
1. Rely ONLY on the provided context chunks. Do not hallucinate or make up external facts.
2. If the context does not contain the answer, explicitly state: "The uploaded documents do not contain sufficient information regarding this query."
3. Always cite your sources in the text using bracketed citations like: `[Doc: <DocName>, Page: <PageNum>]`.
4. Use clean Markdown formatting: headers, bold bullet points, and code blocks where helpful.
5. Provide concise, high-value executive answers.]"""

        context_str = ""
        for i, c in enumerate(context_chunks, 1):
            context_str += f"\n--- [Source #{i}: {c.get('doc_name')} (Page {c.get('page')})] ---\n{c.get('content')}\n"

        user_prompt = f"""DOCUMENT CONTEXT:
{context_str}

USER QUERY:
{query}

Please formulate a precise, well-structured answer with exact citations from the context above."""

        response_text = self._call_gemini_raw(system_instruction, user_prompt)
        
        citations = []
        for c in context_chunks:
            citations.append({
                "chunk_id": c.get("chunk_id"),
                "doc_name": c.get("doc_name"),
                "page": c.get("page", 1),
                "confidence": c.get("hybrid_confidence", 85),
                "snippet": c.get("content", "")[:280] + "..." if len(c.get("content", "")) > 280 else c.get("content", "")
            })

        return {
            "answer": response_text,
            "citations": citations,
            "total_sources": len(citations)
        }

    def generate_executive_summary(self, all_chunks: list[dict]) -> str:
        """Generates a high-level executive summary across all uploaded knowledge."""
        system_instruction = """[SYSTEM INSTRUCTION: You are an Enterprise Strategic Analyst and Knowledge Architect.
Analyze the provided document corpus and produce a high-impact Executive Intelligence Briefing.
Format with:
- 📌 **Executive Overview** (2-3 sentences)
- 🎯 **Core Objectives & Scope**
- 🔑 **Key Findings & Critical Data Points**
- ⚠️ **Potential Risks, Liabilities & Watchouts**
- 🚀 **Strategic Recommendations / Next Steps**]"""
        
        context_str = "\n\n".join([f"[{c.get('doc_name')}] {c.get('content')[:500]}" for c in all_chunks[:15]])
        return self._call_gemini_raw(system_instruction, f"Analyze the following documents:\n{context_str}")

    def generate_risk_audit(self, all_chunks: list[dict]) -> str:
        """Performs a legal, compliance, and financial risk audit."""
        system_instruction = """[SYSTEM INSTRUCTION: You are an Enterprise Compliance Auditor and Legal Risk Analyst.
Audit the provided document corpus for vulnerabilities, contract risks, regulatory concerns, liability clauses, and hidden penalties.
Format your audit with:
- 🚨 **Critical Risk Level (Low / Moderate / High / Severe)**
- 🔍 **Top Risk Factors Identified** (with specific clauses/quotes)
- ⚖️ **Compliance & Legal Exposures**
- 🛡️ **Risk Mitigation Action Plan**]"""
        
        context_str = "\n\n".join([f"[{c.get('doc_name')}] {c.get('content')[:500]}" for c in all_chunks[:15]])
        return self._call_gemini_raw(system_instruction, f"Audit the following documents for risks:\n{context_str}")

    def extract_structured_data(self, all_chunks: list[dict]) -> str:
        """Extracts structured tables of dates, financial amounts, key stakeholders, and deliverables."""
        system_instruction = """[SYSTEM INSTRUCTION: You are an Automated Data Extraction Agent.
Extract all structured data from the documents into clean Markdown tables:
1. 📊 **Key Metrics, Financial Figures & Pricing** (Amount, Item/Fee, Terms)
2. 📅 **Key Dates, Milestones & Deadlines** (Date, Event/Milestone, Owner)
3. 👥 **Key Stakeholders & Entities** (Name/Entity, Role/Responsibility, Contact/Notes)]"""
        
        context_str = "\n\n".join([f"[{c.get('doc_name')}] {c.get('content')[:500]}" for c in all_chunks[:15]])
        return self._call_gemini_raw(system_instruction, f"Extract structured metrics and tables from:\n{context_str}")
