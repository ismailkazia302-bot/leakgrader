import os
import sys

from engine.document_parser import parse_file
from engine.hybrid_retriever import HybridRetriever
from engine.agent_intelligence import OmniAgentIntelligence

contract_path = os.path.join(os.path.dirname(__file__), "sample_docs", "enterprise_sla_contract.txt")
with open(contract_path, "rb") as f:
    chunks = parse_file("enterprise_sla_contract.txt", f.read())

print(f"[TEST 1] Parsed {len(chunks)} chunks from contract successfully.")

api_key = os.environ.get("GEMINI_API_KEY", "")
retriever = HybridRetriever(api_key=api_key)
retriever.index(chunks)

query = "What is the penalty for early termination or confidentiality breach?"
results = retriever.search(query, top_k=2)

print(f"\n[TEST 2] Hybrid Search for: '{query}'")
for r in results:
    print(f" -> [{r.get('hybrid_confidence')}% Match] {r.get('content')[:120]}...")

intelligence = OmniAgentIntelligence(api_key=api_key, model="gemini-3.6-flash")
answer_data = intelligence.query_with_citations(query, results)

print(f"\n[TEST 3] AI Agent Grounded Answer with Citations:")
print(answer_data.get("answer"))
print(f"\nTotal Citations Attached: {len(answer_data.get('citations', []))}")
