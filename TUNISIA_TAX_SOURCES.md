# Tunisia Tax Law — Master Source Reference
## For RAG Knowledge Base Construction (IRPP · IS · TVA · CNSS · CDPF)
### Last verified: January 2025 (LF 2025 in effect)

---

## TIER 1 — PRIMARY LEGAL TEXTS (must have)

| Code | Scope | Direct PDF URL | Source | Year |
|---|---|---|---|---|
| Code IRPP & IS (FR) | Personal + corporate income tax | https://jibaya.tn/wp-content/uploads/2025/07/code-IS-et-IRPP-francais-1.pdf | jibaya.tn | 2025 ✅ |
| Code IRPP & IS (FR backup) | Personal + corporate income tax | https://alliance-tunisie.com/wp-content/uploads/2024/06/CODE-IRPP-IS-2024.pdf | alliance-tunisie | 2024 |
| Code TVA | VAT rates, exemptions, thresholds | https://alliance-tunisie.com/wp-content/uploads/2024/06/CODE-DE-LA-TVA-2024.pdf | alliance-tunisie | 2024 ✅ |
| CDPF | Audit procedures, penalties, deadlines | https://jibaya.tn/wp-content/uploads/2025/02/cdpf-2025.pdf | jibaya.tn | 2025 ✅ |
| CDPF (backup 2023) | Procedures | https://jibaya.tn/wp-content/uploads/2024/02/CODE-DES-DROITS-ET-PROCEDURES-FISCAUX-2023.pdf | jibaya.tn | 2023 |

---

## TIER 2 — NOTES COMMUNES (critical annual updates)

Notes Communes are explanatory circulars published by DGELF after each Loi de Finances.
They are ESSENTIAL — they explain HOW the law applies in practice.

### LF 2025 Notes (Most Important)

| Note | Topic | URL |
|---|---|---|
| NC 02/2025 | Régularisation créances fiscales | https://jibaya.tn/wp-content/uploads/2025/01/Note-Commune-02-1.pdf |
| NC 03/2025 | Allègement IRPP individus (art.36 LF2025) | https://jibaya.tn/wp-content/uploads/2025/01/Note-Commune-03-1.pdf |
| NC 07/2025 | Révision taux TVA (art.31+64 LF2025) — Arabic only | jibaya.tn/docs/cdpf-2025/ |
| NC 08/2025 | IS progressif pour certaines sociétés (art.37 LF2025) | https://jibaya.tn/wp-content/uploads/2025/02/Note-Commune-N08-2025.pdf |

### LF 2024 Notes (still partially in effect)

| Note | Topic | URL |
|---|---|---|
| NC 05/2024 | Avantage fiscal terrains résidentiels | See jibaya.tn/docs/cdpf-2025/ |
| NC 07/2024 | Taxe conjoncturelle 2024-2025 | See jibaya.tn/docs/cdpf-2025/ |
| NC 12/2024 | Révision TVA (art.33 LF2024) | https://jibaya.tn/wp-content/uploads/2024/03/Note-Commune-N%C2%B012.pdf |

All Notes Communes index: https://jibaya.tn/docs/cdpf-2025/

---

## TIER 3 — CNSS (Social Contributions)

| Resource | URL | Notes |
|---|---|---|
| Taux salariés 2025 | https://www.cnss.tn/fr/web/employeur/emp_asset_services/ | Official CNSS portal |
| Taux indépendants | https://www.cnss.tn/fr/web/non-salarie/ | Non-salary workers |
| Guide complet 2025 | https://www.tassaruf.com/blog/declarations-sociales-cnss-tunisie.html | Best structured summary |
| Synthèse cleiss.fr | https://www.cleiss.fr/docs/cotisations/tunisie.html | International reference |

### CNSS 2025 Rates (verified)
- Salarié — Part salariale: **9.68%**
- Salarié — Part patronale: **17.07%**
- Total indicatif: ~26.75% du salaire brut
- Indépendant: **14.71%** sur revenus déclarés
- SMIG (48h, jan 2025): **528.320 DT/mois**

---

## TIER 4 — SUPPLEMENTARY SOURCES

| Source | What It Covers | URL |
|---|---|---|
| finances.gov.tn | Official ministry overview, aperçu général | https://www.finances.gov.tn/fr/apercu-general-sur-la-fiscalite |
| jibaya.tn (portal) | All codes + Notes Communes aggregated | https://jibaya.tn |
| legislation.tn | Code d'Incitation aux Investissements | https://www.legislation.tn |
| paie-tunisie.com | CNSS detailed breakdowns, payroll | https://paie-tunisie.com |
| JORC (Journal Officiel) | Official gazette — all laws as published | https://www.iort.gov.tn |

---

## CRITICAL NUMERIC RULES (do NOT put these in RAG)

### IRPP Brackets 2025 (LF 2025, art.36)
```
0 – 5,000 DT        → 0%
5,000 – 10,000 DT   → 15%
10,000 – 20,000 DT  → 25%
20,000 – 30,000 DT  → 30%
30,000 – 50,000 DT  → 33%
> 50,000 DT         → 35%
```

### IS Rates 2025
```
Standard (PME, services): 15%
Progressif appliqué sur bénéfice net (LF2025 art.37): tranches à confirmer
Élevé (banques, assurances, télécoms, hydrocarbures): 35%
Minimum IS: 0.2% du CA brut
```

### TVA Taux 2025
```
Standard: 19%
Intermédiaire: 13%
Réduit: 7%
Super-réduit: 6%
Zéro / exonéré: 0%
Seuil assujettissement services: 50,000 DT CA
Seuil assujettissement commerce: 100,000 DT CA
```

---

## LANGUAGE HANDLING STRATEGY

### Problem
- Core codes (IRPP, IS, TVA, CDPF) are available in French ✅
- Many Notes Communes post-2024 are Arabic ONLY ⚠️
- CNSS portal is bilingual but Arabic-first

### Solution
1. **French texts** → pdfplumber extraction → multilingual-e5-large embedding
2. **Arabic-only texts** → Two options:
   a. Use `arabic-reshaper` + `python-bidi` for proper text extraction
   b. Use Tesseract OCR with `ara` language pack for scanned Arabic PDFs
   c. For MVP: manually translate key Arabic-only Notes Communes to French

### Arabic PDF Extraction
```python
# For Arabic PDFs, use this instead of standard pdfplumber
import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display

with pdfplumber.open("arabic_note.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped)
            # Now bidi_text is properly ordered Arabic
```

---

## ANNUAL MAINTENANCE CHECKLIST

Run this every January after the new Loi de Finances is published (typically December):

- [ ] Download new Code IRPP/IS PDF from jibaya.tn
- [ ] Download all new Notes Communes (NC 01/YEAR onwards)
- [ ] Update `tax_rates_YEAR.json` — especially IRPP brackets, IS rates, TVA taux
- [ ] Update SMIG value (changes annually)
- [ ] Re-run pipeline: `python tunisia_tax_pipeline.py --step all`
- [ ] Set `is_current: False` on superseded document versions
- [ ] Validate 5 test cases against known correct outcomes

---

## KNOWN DATA GAPS (manual work required)

| Gap | Status | Workaround |
|---|---|---|
| CNSS Indépendant coefficient table | Not in PDF | Scrape cnss.tn/non-salarie manually |
| Arabic-only NC 07/2025 (TVA changes) | No French version | Manual translation or AR embedding |
| Code d'Incitation aux Investissements | Partially outdated | legislation.tn + verify with expert |
| Sectoral TVA rate lists (Annex I/II) | Complex tables | Extract as CSV separately |
| Conventions fiscales bilatérales | ~70 treaties | Out of scope for MVP |
