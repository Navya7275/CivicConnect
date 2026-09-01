"""Web scraping and data fetcher module for India Code and MyScheme.

Features:
- Local caching of raw HTML/JSON downloads
- HTTP timeout handling and clean error logging
- MyScheme fallback dataset loading via Hugging Face shrijayan/gov_myscheme or direct API/dataset
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

RAW_DATA_DIR = Path(__file__).parent / "raw_data"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion_scrape")


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch content from HTTP URL with timeout and error logging."""
    try:
        headers = {
            "User-Agent": "CivicConnect-AcademicPipeline/1.0 (Indian Legal & Welfare Research)"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return None


def fetch_myscheme_pilot_data() -> List[Dict[str, Any]]:
    """Fetch or load pilot welfare schemes from MyScheme / Hugging Face shrijayan/gov_myscheme dataset."""
    cache_path = RAW_DATA_DIR / "myscheme_pilot.json"
    if cache_path.exists():
        logger.info(f"Loading MyScheme pilot data from local cache: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info("Attempting to fetch welfare scheme dataset from Hugging Face API...")
    hf_url = "https://datasets-server.huggingface.co/rows?dataset=shrijayan/gov_myscheme&config=default&split=train&offset=0&length=50"
    
    data = fetch_url(hf_url)
    schemes = []

    if data:
        try:
            res_json = json.loads(data)
            rows = res_json.get("rows", [])
            for r in rows:
                row_data = r.get("row", {})
                schemes.append(row_data)
        except Exception as e:
            logger.warning(f"Could not parse HF API response: {e}")

    # Fallback pilot scheme records if network dataset is unreachable/different format
    if not schemes:
        logger.info("Using embedded pilot MyScheme welfare data...")
        schemes = [
            {
                "scheme_name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
                "description": "National Mission for Financial Inclusion to ensure access to financial services namely Banking/Savings & Deposit Accounts, Remittance, Credit, Insurance, Pension in an affordable manner.",
                "eligibility": "Must be a citizen of India. Minimum age of applicant is 10 years. Should not hold any other bank account.",
                "benefits": "Accidental Insurance Cover of Rs. 2 Lakh. Life Cover of Rs. 30,000. Overdraft facility up to Rs. 10,000 to eligible account holders.",
                "application_process": "Apply at any bank branch or Business Correspondent outlet by submitting the PMJDY account opening form along with KYC documents.",
                "documents_required": "Aadhaar Card, Passport, Driving License, Voter ID Card, or PAN Card.",
                "category": "Financial Inclusion & Banking",
                "jurisdiction": "Central",
                "effective_date": "2014-08-28",
                "source_url": "https://www.myscheme.gov.in/schemes/pmjdy"
            },
            {
                "scheme_name": "PM Kisan Samman Nidhi (PM-KISAN)",
                "description": "Central Sector scheme to provide income support to all landholding farmers' families in the country to supplement their financial needs for procuring various inputs.",
                "eligibility": "All landholding farmer families having cultivable landholding in their names. Subject to exclusion criteria such as institutional landholders, tax payers.",
                "benefits": "Financial benefit of Rs. 6000/- per year per family payable in three equal installments of Rs. 2000/- every four months.",
                "application_process": "Farmers can register online at PM-KISAN portal or through Farmers Corner, or visit nearest CSC center.",
                "documents_required": "Aadhaar mandatory, Bank account details, Landholding documents.",
                "category": "Agriculture & Farmer Welfare",
                "jurisdiction": "Central",
                "effective_date": "2018-12-01",
                "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan"
            },
            {
                "scheme_name": "Ladli Laxmi Yojana (Madhya Pradesh)",
                "description": "State welfare scheme of Madhya Pradesh to lay firm foundation of girls' future through educational and financial assistance.",
                "eligibility": "Girl child born in Madhya Pradesh. Parents must be native residents of MP and non-income tax payers.",
                "benefits": "Financial assurance certificates issued; milestone payments at Class 6th, 9th, 11th, 12th and lump sum at age 21.",
                "application_process": "Apply online through Ladli Laxmi Portal or via Anganwadi centers in MP.",
                "documents_required": "Birth certificate of girl child, Residence proof of MP, Parents Aadhaar card, Ration card.",
                "category": "Women and Child Development",
                "jurisdiction": "Madhya Pradesh",
                "effective_date": "2007-04-01",
                "source_url": "https://ladlilaxmi.mp.gov.in/"
            }
        ]

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2)

    logger.info(f"Saved {len(schemes)} raw welfare schemes to cache: {cache_path}")
    return schemes


if __name__ == "__main__":
    schemes = fetch_myscheme_pilot_data()
    print(f"Scraped/Loaded {len(schemes)} welfare scheme records.")
