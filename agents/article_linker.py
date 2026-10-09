"""
Article Linker — transforms article references into clickable links
"""
import re

SOURCES = {
    "CDPF":     "https://jibaya.tn/wp-content/uploads/2025/02/cdpf-2025.pdf",
    "IRPP_IS":  "https://jibaya.tn/wp-content/uploads/2025/07/code-IS-et-IRPP-francais-1.pdf",
    "TVA":      "https://alliance-tunisie.com/wp-content/uploads/2024/06/CODE-DE-LA-TVA-2024.pdf",
    "FINANCES": "https://www.finances.gov.tn/fr/apercu-general-sur-la-fiscalite",
}

ARTICLE_PATTERNS = [
    (r'[Aa]rticle\s+(\d+[\w\s]*?(?:du\s+)?(?:code\s+des\s+)?(?:droits\s+et\s+)?(?:proc[eé]dures\s+)?fiscaux|CDPF)', "CDPF", "CDPF"),
    (r'[Aa]rticle\s+(\d+[\w\s]*?(?:bis|ter|quater)?)\s+(?:du\s+)?(?:code\s+)?(?:de\s+l[\'\'])?(?:imp[oô]t|imp[oô]t|IRPP|IRPP\s+et\s+IS)', "IRPP_IS", "Code IRPP & IS"),
    (r'[Aa]rticle\s+(\d+)\s+(?:bis|ter|quater)?\s*(?:du\s+code\s+des\s+imp[oô]ts)', "IRPP_IS", "Code des impôts"),
]

def linkify_articles(text: str, mode: str = "markdown") -> str:
    if not text: return text
    result = text
    for pattern, source_key, label in ARTICLE_PATTERNS:
        url = SOURCES.get(source_key, SOURCES["FINANCES"])
        def make_replacement(match, url=url, label=label):
            original = match.group(0)
            if mode == "html":
                return f'<a href="{url}" target="_blank" style="color:#1D9E75;text-decoration:underline;font-weight:500;">{original}</a>'
            return f"[{original}]({url})"
        result = re.sub(pattern, make_replacement, result, flags=re.IGNORECASE)
    return result
