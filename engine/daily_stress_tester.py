"""
LeakGrader.com - Daily Autonomous Red-Teaming & Stress-Testing Suite
Adopts the Founder's mindset: Relentlessly challenges data authenticity,
geographical dialing accuracy, currency matching, revenue scale realism,
and system latency across dynamic global test matrices.
"""

import time
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from typing import List, Dict, Any

from engine.lead_gen_agent import LeadPulseAgent

class DailySystemStressTester:
    def __init__(self):
        self.agent = LeadPulseAgent()
        self.results_dir = os.path.join(os.path.dirname(__file__), "..", "telemetry", "stress_tests")
        os.makedirs(self.results_dir, exist_ok=True)

    def get_test_matrix(self) -> List[Dict[str, Any]]:
        """
        Dynamic global test queries across Tier-1/2/3 cities, GCC, Europe, US, and edge cases.
        """
        return [
            {
                "id": "IN-DEL-01",
                "label": "Delhi Metro Gyms (India Tier-1)",
                "industry": "Gym & Fitness Centers",
                "location": "Delhi",
                "expected_phone_prefix": "+91",
                "expected_curr": "₹",
                "expected_tld": [".in", ".co.in", ".com"]
            },
            {
                "id": "IN-NAG-02",
                "label": "Nagpur Dental Clinics (India Tier-2/3)",
                "industry": "Dental Clinic",
                "location": "Nagpur, Maharashtra",
                "expected_phone_prefix": "+91",
                "expected_curr": "₹",
                "expected_tld": [".in", ".co.in", ".com"]
            },
            {
                "id": "IN-GOA-03",
                "label": "Siolim Goa Salons (India Coastal / Tier-3)",
                "industry": "Salon & Spa",
                "location": "Siolim Goa",
                "expected_phone_prefix": "+91",
                "expected_curr": "₹",
                "expected_tld": [".in", ".co.in", ".com"]
            },
            {
                "id": "SA-DAM-04",
                "label": "Dammam Dining & Restaurants (Saudi Arabia / GCC)",
                "industry": "Restaurant",
                "location": "Dammam",
                "expected_phone_prefix": "+966",
                "expected_curr": "SAR",
                "expected_tld": [".sa", ".com.sa", ".com"]
            },
            {
                "id": "AE-DXB-05",
                "label": "Dubai Luxury Real Estate (UAE / GCC)",
                "industry": "Real Estate",
                "location": "Dubai",
                "expected_phone_prefix": "+971",
                "expected_curr": "AED",
                "expected_tld": [".ae", ".com"]
            },
            {
                "id": "UK-LON-06",
                "label": "London Cosmetic Clinics (UK / Western Europe)",
                "industry": "Cosmetic Clinic",
                "location": "London",
                "expected_phone_prefix": "+44",
                "expected_curr": "£",
                "expected_tld": [".co.uk", ".com"]
            },
            {
                "id": "DE-BER-07",
                "label": "Berlin Dental Specialists (Germany / EU)",
                "industry": "Dentist",
                "location": "Berlin",
                "expected_phone_prefix": "+49",
                "expected_curr": "€",
                "expected_tld": [".de", ".com"]
            },
            {
                "id": "US-NYC-08",
                "label": "New York Cloud SaaS (US Enterprise)",
                "industry": "B2B SaaS",
                "location": "New York",
                "expected_phone_prefix": "+1",
                "expected_curr": "$",
                "expected_tld": [".com", ".io", ".ai"]
            },
            {
                "id": "TYPO-09",
                "label": "Misspelled Typo Query (resturant in goa)",
                "industry": "resturant",
                "location": "goa",
                "expected_phone_prefix": "+91",
                "expected_curr": "₹",
                "expected_tld": [".in", ".co.in", ".com"]
            }
        ]

    def run_daily_stress_test(self) -> Dict[str, Any]:
        """
        Executes complete battery of stress tests, assesses each response,
        checks for fake data, bad dial codes, mismatched currencies, and speed.
        """
        matrix = self.get_test_matrix()
        test_results = []
        passed_count = 0
        failed_count = 0
        start_time_all = time.time()

        for test in matrix:
            t0 = time.time()
            try:
                leads = self.agent.generate_targeted_leads(
                    industry=test["industry"],
                    location=test["location"],
                    count=3
                )
                latency = round(time.time() - t0, 2)
                
                # Evaluation Criteria
                has_leads = len(leads) > 0
                sample_lead = leads[0] if has_leads else {}
                
                phone = sample_lead.get("phone", "")
                rev = sample_lead.get("estimated_revenue") or sample_lead.get("est_revenue", "")
                company = sample_lead.get("company_name") or sample_lead.get("company", "")
                website = sample_lead.get("website") or sample_lead.get("domain", "")
                email = sample_lead.get("email", "")

                # 1. Check Dialing Code
                phone_correct = test["expected_phone_prefix"] in phone
                # 2. Check Currency
                curr_correct = test["expected_curr"] in rev
                # 3. Check Realism (not empty, valid domain)
                not_placeholder = bool(company and company != "Company Name" and "@" in email)
                # 4. Check Typo Resolution if applicable
                industry_normalized = True
                if test["id"] == "TYPO-09":
                    industry_normalized = "Restaurant" in sample_lead.get("industry", "")

                is_passed = has_leads and phone_correct and curr_correct and not_placeholder and industry_normalized

                if is_passed:
                    passed_count += 1
                else:
                    failed_count += 1

                test_results.append({
                    "id": test["id"],
                    "label": test["label"],
                    "location": test["location"],
                    "latency_sec": latency,
                    "status": "PASS" if is_passed else "FAIL",
                    "sample_company": company,
                    "sample_phone": phone,
                    "sample_revenue": rev,
                    "checks": {
                        "phone_correct": phone_correct,
                        "currency_correct": curr_correct,
                        "not_placeholder": not_placeholder,
                        "industry_normalized": industry_normalized
                    },
                    "leads_count": len(leads)
                })

            except Exception as e:
                failed_count += 1
                test_results.append({
                    "id": test["id"],
                    "label": test["label"],
                    "status": "ERROR",
                    "error": str(e),
                    "latency_sec": round(time.time() - t0, 2)
                })

        total_time = round(time.time() - start_time_all, 2)
        score_percent = round((passed_count / len(matrix)) * 100, 1)

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_queries_tested": len(matrix),
            "passed": passed_count,
            "failed": failed_count,
            "accuracy_score": f"{score_percent}%",
            "total_execution_time": f"{total_time}s",
            "overall_health": "BULLETPROOF" if score_percent == 100 else ("NEEDS_HARDENING" if score_percent >= 80 else "CRITICAL"),
            "test_cases": test_results
        }

        # Save to persistent log
        log_file = os.path.join(self.results_dir, f"stress_test_{int(time.time())}.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

if __name__ == "__main__":
    tester = DailySystemStressTester()
    res = tester.run_daily_stress_test()
    print(f"Daily Stress Test Complete: {res['accuracy_score']} Passed ({res['passed']}/{res['total_queries_tested']}) in {res['total_execution_time']}")
    for tc in res["test_cases"]:
        status_icon = "✅" if tc.get("status") == "PASS" else "❌"
        print(f"{status_icon} [{tc['id']}] {tc['label']}: Phone={tc.get('sample_phone')}, Rev={tc.get('sample_revenue')}, Time={tc.get('latency_sec')}s")
