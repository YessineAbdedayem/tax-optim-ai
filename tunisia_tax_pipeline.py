"""
tunisia_tax_pipeline.py
=======================
Complete pipeline: Download → Extract → Clean → Chunk → Index
For Tunisian tax law RAG system (IRPP, IS, TVA, CNSS, CDPF)

Requirements:
    pip install requests pdfplumber langdetect chromadb sentence-transformers tqdm

Usage:
    python tunisia_tax_pipeline.py --step all
    python tunisia_tax_pipeline.py --step download
    python tunisia_tax_pipeline.py --step extract
    python tunisia_tax_pipeline.py --step index
"""

import os
import re
import json
import time
import argparse
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests
import pdfplumber
from tqdm import tqdm

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR = Path("./tunisia_tax_data")
RAW_DIR = BASE_DIR / "raw_pdfs"
TEXT_DIR = BASE_DIR / "extracted_text"
CHUNKS_DIR = BASE_DIR / "chunks"
INDEX_DIR = BASE_DIR / "chroma_index"
RATES_DIR = BASE_DIR / "rates_config"

for d in [RAW_DIR, TEXT_DIR, CHUNKS_DIR, INDEX_DIR, RATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── DOCUMENT REGISTRY ─────────────────────────────────────────────────────────
# Every official source with metadata. Add new Lois de Finances here each year.

DOCUMENTS = [
    # ── IRPP & IS ──────────────────────────────────────────────────────────────
    {
        "id": "irpp_is_2024",
        "domain": "IRPP_IS",
        "year": 2024,
        "language": "fr",
        "title": "Code de l'IRPP et de l'IS 2024",
        "url": "https://alliance-tunisie.com/wp-content/uploads/2024/06/CODE-IRPP-IS-2024.pdf",
        "source": "alliance-tunisie.com",
        "priority": 1,
        "is_current": False,  # superseded by 2025 LF changes
    },
    {
        "id": "irpp_is_2025",
        "domain": "IRPP_IS",
        "year": 2025,
        "language": "fr",
        "title": "Code de l'IRPP et de l'IS 2025 (mis à jour LF 2025)",
        "url": "https://jibaya.tn/wp-content/uploads/2025/07/code-IS-et-IRPP-francais-1.pdf",
        "source": "jibaya.tn",
        "priority": 1,
        "is_current": True,
    },
    # ── TVA ────────────────────────────────────────────────────────────────────
    {
        "id": "tva_2024",
        "domain": "TVA",
        "year": 2024,
        "language": "fr",
        "title": "Code de la TVA 2024",
        "url": "https://alliance-tunisie.com/wp-content/uploads/2024/06/CODE-DE-LA-TVA-2024.pdf",
        "source": "alliance-tunisie.com",
        "priority": 1,
        "is_current": True,
    },
    # ── CDPF ───────────────────────────────────────────────────────────────────
    {
        "id": "cdpf_2025",
        "domain": "CDPF",
        "year": 2025,
        "language": "fr",
        "title": "Code des Droits et Procédures Fiscaux 2025",
        "url": "https://jibaya.tn/wp-content/uploads/2025/02/cdpf-2025.pdf",
        "source": "jibaya.tn",
        "priority": 1,
        "is_current": True,
    },
    {
        "id": "cdpf_2023",
        "domain": "CDPF",
        "year": 2023,
        "language": "fr",
        "title": "Code des Droits et Procédures Fiscaux 2023",
        "url": "https://jibaya.tn/wp-content/uploads/2024/02/CODE-DES-DROITS-ET-PROCEDURES-FISCAUX-2023.pdf",
        "source": "jibaya.tn",
        "priority": 2,
        "is_current": False,
    },
    # ── Notes Communes LF 2025 (most important annual updates) ─────────────────
    {
        "id": "nc_03_2025",
        "domain": "IRPP_IS",
        "year": 2025,
        "language": "fr",
        "title": "Note Commune 03/2025 — Allègement charge fiscale individus (LF 2025 art.36)",
        "url": "https://jibaya.tn/wp-content/uploads/2025/01/Note-Commune-03-1.pdf",
        "source": "jibaya.tn",
        "priority": 1,
        "is_current": True,
    },
    {
        "id": "nc_08_2025",
        "domain": "IS",
        "year": 2025,
        "language": "fr",
        "title": "Note Commune 08/2025 — Taux progressifs IS (LF 2025 art.37)",
        "url": "https://jibaya.tn/wp-content/uploads/2025/02/Note-Commune-N08-2025.pdf",
        "source": "jibaya.tn",
        "priority": 1,
        "is_current": True,
    },
    {
        "id": "nc_12_2024",
        "domain": "TVA",
        "year": 2024,
        "language": "fr",
        "title": "Note Commune 12/2024 — Révision TVA (LF 2024 art.33)",
        "url": "https://jibaya.tn/wp-content/uploads/2024/03/Note-Commune-N%C2%B012.pdf",
        "source": "jibaya.tn",
        "priority": 1,
        "is_current": True,
    },
]

# ─── STEP 1: DOWNLOAD ──────────────────────────────────────────────────────────

def download_documents(retry: int = 3) -> dict:
    """Download all PDFs with retry logic. Returns {doc_id: local_path}."""
    results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (research project, contact: your@email.com)"
    }

    for doc in tqdm(DOCUMENTS, desc="Downloading PDFs"):
        out_path = RAW_DIR / f"{doc['id']}.pdf"

        if out_path.exists():
            log.info(f"[SKIP] {doc['id']} already downloaded")
            results[doc["id"]] = str(out_path)
            continue

        for attempt in range(retry):
            try:
                response = requests.get(doc["url"], headers=headers, timeout=30)
                response.raise_for_status()

                with open(out_path, "wb") as f:
                    f.write(response.content)

                # Verify it's actually a PDF
                if response.content[:4] != b"%PDF":
                    raise ValueError("Downloaded file is not a valid PDF")

                log.info(f"[OK] {doc['id']} ({len(response.content)//1024}KB)")
                results[doc["id"]] = str(out_path)
                break

            except Exception as e:
                log.warning(f"[RETRY {attempt+1}] {doc['id']}: {e}")
                if attempt == retry - 1:
                    log.error(f"[FAILED] {doc['id']} — manual download required")
                    log.error(f"  URL: {doc['url']}")
                time.sleep(2 ** attempt)

    # Save download manifest
    manifest = {
        "downloaded_at": datetime.now().isoformat(),
        "results": results,
        "failed": [d["id"] for d in DOCUMENTS if d["id"] not in results]
    }
    with open(BASE_DIR / "download_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    log.info(f"Download complete: {len(results)}/{len(DOCUMENTS)} successful")
    return results

# ─── STEP 2: EXTRACT TEXT ──────────────────────────────────────────────────────

def clean_pdf_text(raw: str) -> str:
    """Remove headers, footers, page numbers, and normalize whitespace."""
    lines = raw.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()

        # Skip blank lines
        if not line:
            continue

        # Skip standalone page numbers
        if re.match(r"^\d+$", line):
            continue

        # Skip common header/footer patterns
        if re.match(r"^(Imprimerie Officielle|REPUBLIQUE TUNISIENNE|Ministère des Finances)", line, re.I):
            continue

        # Skip dotted table-of-contents lines
        if re.match(r"^.+\.{5,}\s*\d+$", line):
            continue

        cleaned.append(line)

    text = "\n".join(cleaned)

    # Collapse excessive whitespace while preserving paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def extract_text(doc_id: str, pdf_path: str) -> Optional[str]:
    """Extract and clean text from a PDF file."""
    out_path = TEXT_DIR / f"{doc_id}.txt"

    if out_path.exists():
        log.info(f"[SKIP] {doc_id} already extracted")
        with open(out_path, encoding="utf-8") as f:
            return f.read()

    try:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if text:
                    full_text.append(text)

        raw = "\n".join(full_text)
        cleaned = clean_pdf_text(raw)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        char_count = len(cleaned)
        log.info(f"[OK] {doc_id}: {char_count:,} chars extracted")
        return cleaned

    except Exception as e:
        log.error(f"[FAIL] {doc_id}: {e}")
        return None


def extract_all():
    """Extract text from all downloaded PDFs."""
    for doc in DOCUMENTS:
        pdf_path = RAW_DIR / f"{doc['id']}.pdf"
        if pdf_path.exists():
            extract_text(doc["id"], str(pdf_path))
        else:
            log.warning(f"[MISSING PDF] {doc['id']} — skipping extraction")

# ─── STEP 3: CHUNK BY ARTICLE ─────────────────────────────────────────────────

# Article detection patterns for Tunisian legal texts (French + Arabic)
ARTICLE_PATTERNS = [
    re.compile(r"^(Article\s+\d+[\w\-]*\.?)", re.MULTILINE | re.IGNORECASE),  # French
    re.compile(r"^(الفصل\s+\d+)", re.MULTILINE),                               # Arabic
    re.compile(r"^(Art\.?\s+\d+)", re.MULTILINE | re.IGNORECASE),              # Abbreviated
]


def split_by_article(text: str, doc_meta: dict) -> list[dict]:
    """
    Split document text into chunks by Article number.
    Falls back to paragraph chunking if no article structure detected.
    Returns list of chunk dicts with metadata.
    """
    chunks = []

    # Try to find article boundaries
    all_matches = []
    for pattern in ARTICLE_PATTERNS:
        matches = [(m.start(), m.group()) for m in pattern.finditer(text)]
        all_matches.extend(matches)

    all_matches.sort(key=lambda x: x[0])

    if len(all_matches) < 3:
        # Fallback: split by paragraphs into ~500 char chunks
        log.warning(f"No article structure in {doc_meta['id']}, using paragraph chunking")
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]

        current = ""
        chunk_idx = 0
        for para in paragraphs:
            if len(current) + len(para) > 800:
                if current:
                    chunks.append(_make_chunk(
                        doc_meta, chunk_idx, current,
                        article_ref=f"chunk_{chunk_idx}"
                    ))
                    chunk_idx += 1
                    current = para
            else:
                current += "\n\n" + para

        if current:
            chunks.append(_make_chunk(doc_meta, chunk_idx, current, f"chunk_{chunk_idx}"))

    else:
        # Article-based chunking
        for i, (start, article_ref) in enumerate(all_matches):
            end = all_matches[i + 1][0] if i + 1 < len(all_matches) else len(text)
            content = text[start:end].strip()

            if len(content) < 30:  # Skip empty articles
                continue

            # Long articles: sub-chunk by paragraph
            if len(content) > 1500:
                sub_chunks = _sub_chunk(content, article_ref)
                for j, sub in enumerate(sub_chunks):
                    chunks.append(_make_chunk(
                        doc_meta, f"{i}_{j}", sub,
                        article_ref=article_ref,
                        sub_chunk=True
                    ))
            else:
                chunks.append(_make_chunk(doc_meta, i, content, article_ref))

    return chunks


def _make_chunk(doc_meta: dict, idx, content: str, article_ref: str, sub_chunk: bool = False) -> dict:
    chunk_id = hashlib.md5(
        f"{doc_meta['id']}_{idx}_{content[:50]}".encode()
    ).hexdigest()[:12]

    return {
        "chunk_id": chunk_id,
        "doc_id": doc_meta["id"],
        "domain": doc_meta["domain"],
        "year": doc_meta["year"],
        "language": doc_meta["language"],
        "title": doc_meta["title"],
        "source": doc_meta["source"],
        "is_current": doc_meta["is_current"],
        "article_ref": article_ref,
        "is_sub_chunk": sub_chunk,
        "content": content,
        "char_count": len(content),
        "indexed_at": datetime.now().isoformat(),
    }


def _sub_chunk(text: str, article_ref: str, max_len: int = 800) -> list[str]:
    """Split a long article into sub-paragraphs."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    subs = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > max_len and current:
            subs.append(current.strip())
            current = para
        else:
            current += "\n\n" + para
    if current:
        subs.append(current.strip())
    return subs


def chunk_all():
    """Chunk all extracted texts and save to JSON."""
    all_chunks = []
    doc_meta_map = {d["id"]: d for d in DOCUMENTS}

    for txt_file in TEXT_DIR.glob("*.txt"):
        doc_id = txt_file.stem
        if doc_id not in doc_meta_map:
            continue

        with open(txt_file, encoding="utf-8") as f:
            text = f.read()

        doc_meta = doc_meta_map[doc_id]
        chunks = split_by_article(text, doc_meta)
        all_chunks.extend(chunks)

        out_path = CHUNKS_DIR / f"{doc_id}_chunks.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        log.info(f"[CHUNKED] {doc_id}: {len(chunks)} chunks")

    # Save master chunk file
    with open(BASE_DIR / "all_chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    log.info(f"Total chunks: {len(all_chunks)}")
    return all_chunks

# ─── STEP 4: INDEX INTO CHROMADB ──────────────────────────────────────────────

def build_index():
    """Embed all chunks and load into ChromaDB using multilingual embeddings."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        log.error("Install: pip install chromadb sentence-transformers")
        return

    chunks_path = BASE_DIR / "all_chunks.json"
    if not chunks_path.exists():
        log.error("Run chunking step first")
        return

    with open(chunks_path, encoding="utf-8") as f:
        all_chunks = json.load(f)

    log.info(f"Indexing {len(all_chunks)} chunks...")

    # Use cached sentence-transformers model for faster loading
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    )

    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    # Create collection per domain for faster filtered retrieval
    domains = set(c["domain"] for c in all_chunks)
    collections = {}
    for domain in domains:
        collections[domain] = client.get_or_create_collection(
            name=f"tunisia_tax_{domain.lower()}",
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    # Also create a master collection
    master_col = client.get_or_create_collection(
        name="tunisia_tax_all",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Batch insert (ChromaDB handles batching internally)
    batch_size = 50
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Indexing"):
        batch = all_chunks[i:i+batch_size]

        ids = [c["chunk_id"] for c in batch]
        documents = [c["content"] for c in batch]
        metadatas = [{
            k: v for k, v in c.items() if k != "content"
        } for c in batch]

        # Add to domain collection
        for chunk in batch:
            domain_col = collections.get(chunk["domain"])
            if domain_col:
                domain_col.upsert(
                    ids=[chunk["chunk_id"]],
                    documents=[chunk["content"]],
                    metadatas=[{k: v for k, v in chunk.items() if k != "content"}]
                )

        # Add to master collection
        master_col.upsert(ids=ids, documents=documents, metadatas=metadatas)

    log.info(f"Index built. Collections: {list(collections.keys()) + ['all']}")

# ─── STEP 5: RATES CONFIG (JSON, not RAG) ────────────────────────────────────

def generate_rates_config():
    """
    Generate structured JSON for all numeric tax rules.
    These go in code, NOT in the vector database.
    Update this every January after reviewing the new Loi de Finances.
    """

    config = {
        "_meta": {
            "last_updated": "2025-01-01",
            "source_law": "Loi n°2024-48 du 9 décembre 2024 (LF 2025)",
            "warning": "Verify against official texts before production use"
        },

        # ── IRPP — Impôt sur le Revenu des Personnes Physiques ───────────────
        # Source: LF 2025 art.36, Note Commune 03/2025
        "IRPP": {
            "brackets_2025": [
                {"min": 0,      "max": 5000,   "rate": 0.00, "label": "Exonéré"},
                {"min": 5000,   "max": 10000,  "rate": 0.15, "label": "Tranche 15%"},
                {"min": 10000,  "max": 20000,  "rate": 0.25, "label": "Tranche 25%"},
                {"min": 20000,  "max": 30000,  "rate": 0.30, "label": "Tranche 30%"},
                {"min": 30000,  "max": 50000,  "rate": 0.33, "label": "Tranche 33%"},
                {"min": 50000,  "max": None,   "rate": 0.35, "label": "Tranche max 35%"},
            ],
            "minimum_irpp": 100,  # DT minimum pour salariés
            "taux_retenue_salaire": 0.15,  # Retenue à la source salaires
            "deduction_chef_famille": 300,
            "deduction_enfant": 100,  # Par enfant (max 4)
            "deduction_max_enfants": 4,
            "deduction_epargne_retraite_max": 10000,  # SMART, épargne LT
            "forfait_frais_professionnels_rate": 0.10,  # 10% du revenu brut
            "forfait_frais_professionnels_max": 2000,

            "regime_forfaitaire": {
                "seuil_ca_services": 100000,   # CA annuel max services
                "seuil_ca_commerce": 150000,   # CA annuel max commerce
                "taux": 0.03,                  # 3% du CA brut (simplifié)
                "note": "Régime forfaitaire pour petits contribuables"
            },
        },

        # ── IS — Impôt sur les Sociétés ───────────────────────────────────────
        # Source: LF 2025 art.37 — progressif pour certaines sociétés, Note Commune 08/2025
        "IS": {
            "taux_standard": 0.15,   # PME, sociétés de services
            "taux_eleve": 0.35,      # Banques, assurances, télécoms, hydrocarbures
            "taux_intermediaire": 0.20,

            "brackets_progressifs_2025": {
                "applicable_a": "Sociétés soumises au taux standard (hors secteurs exclus)",
                "tranches": [
                    {"min": 0,      "max": 100000, "rate": 0.10},
                    {"min": 100000, "max": 400000, "rate": 0.15},
                    {"min": 400000, "max": None,   "rate": 0.15},  # à confirmer LF
                ]
            },

            "secteurs_taux_35": [
                "Banques",
                "Établissements financiers",
                "Compagnies d'assurance",
                "Opérateurs téléphoniques",
                "Hydrocarbures"
            ],

            "taux_minimum_is": {
                "rate": 0.002,    # 0.2% du CA brut minimum
                "note": "Si IS calculé < minimum, payer le minimum IS"
            },

            "SUARL_SARL": {
                "capital_minimum_SUARL": 1000,   # DT
                "capital_minimum_SARL": 1000,    # DT (réformé)
                "note": "Soumises à IS standard, bénéfices retirés soumis à retenue 10%"
            },
        },

        # ── TVA — Taxe sur la Valeur Ajoutée ──────────────────────────────────
        # Source: Code TVA 2024, LF 2025 art.31+64, Note Commune 07/2025
        "TVA": {
            "taux": {
                "standard": 0.19,
                "intermediaire": 0.13,
                "reduit": 0.07,
                "super_reduit": 0.06,
                "zero": 0.00,
            },

            "seuil_assujettissement": {
                "commerce_industrie": 100000,   # DT CA annuel
                "services": 50000,              # DT CA annuel
                "note": "En dessous: régime franchise (non soumis TVA)"
            },

            "franchise_tva": {
                "applicable": True,
                "conditions": "CA < seuils ci-dessus ET option non-TVA",
                "avantages": "Pas de collecte TVA, pas de déclaration mensuelle"
            },

            "exemptions_principales": [
                "Produits alimentaires de base (pain, lait, huile, etc.)",
                "Médicaments et produits pharmaceutiques",
                "Services d'enseignement",
                "Services médicaux",
                "Exportations (taux 0%)",
                "Agriculture (première transformation)",
            ],

            "periodicite_declaration": {
                "mensuelle": "CA > 100,000 DT",
                "trimestrielle": "CA ≤ 100,000 DT (option)",
            },
        },

        # ── CNSS — Caisse Nationale de Sécurité Sociale ───────────────────────
        # Source: cnss.tn, cleiss.fr, LF 2025
        "CNSS": {
            "regime_general_salarie_2025": {
                "part_salariale": 0.0968,    # 9.68%
                "part_patronale": 0.1707,    # 17.07%
                "total": 0.2675,
                "plafond_assiette": 6000,    # DT/mois (certaines composantes)
                "smig_48h_mensuel": 528.32,  # DT (depuis 01/01/2025)
                "smig_40h_mensuel": 448.24,
                "AT_MT_range": [0.004, 0.04],  # Accidents travail: 0.4% à 4% selon secteur
            },

            "regime_independant_2025": {
                "taux": 0.1471,             # 14.71% sur revenus déclarés
                "note": "Couvre maladie-maternité + vieillesse",
                "base_calcul": "Revenu forfaitaire basé coefficient × SMIG",
                "source": "cnss.tn/non-salarie"
            },

            "echeances": {
                "DMS": "Avant le 15 de chaque mois (mois précédent)",
                "DAS": "Annuelle — récapitulatif cohérent avec DMS",
                "penalite_retard": "100 DT/mois de retard par tranche"
            },
        },

        # ── Retenues à la source ──────────────────────────────────────────────
        "RETENUES_SOURCE": {
            "honoraires_personnes_physiques": 0.15,   # 15%
            "honoraires_personnes_morales": 0.25,     # 25%
            "loyers": 0.15,
            "dividendes_residents": 0.10,
            "dividendes_non_residents": 0.05,         # Avec convention fiscale
            "interets_bancaires": 0.20,
        },

        # ── Droits de Timbre ──────────────────────────────────────────────────
        "DROIT_TIMBRE": {
            "facture_standard": 1.0,   # DT par facture > 1000 DT
        },
    }

    out_path = RATES_DIR / "tax_rates_2025.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    log.info(f"Rates config saved: {out_path}")
    return config

# ─── RETRIEVAL HELPER (for your Agents) ───────────────────────────────────────

class TunisiataxRetriever:
    """
    Drop-in retriever for your LangGraph agents.

    Usage:
        retriever = TunisiaTaskRetriever()
        # In Fiscal Strategy Agent:
        results = retriever.query(
            "quelles dépenses sont déductibles pour un freelance",
            domain="IRPP_IS",
            n=5
        )
    """

    def __init__(self, index_path: str = str(INDEX_DIR)):
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
            )
            self.client = chromadb.PersistentClient(path=index_path)
            self.master = self.client.get_collection("tunisia_tax_all", embedding_function=emb_fn)
            self._emb_fn = emb_fn
            log.info("Retriever initialized")
        except Exception as e:
            log.error(f"Retriever init failed: {e}")
            self.master = None

    def query(self, question: str, domain: str = None, n: int = 5,
              current_only: bool = True) -> list[dict]:
        """
        Query the knowledge base.

        Args:
            question: Natural language question (FR or AR)
            domain: Filter by domain (IRPP_IS, TVA, IS, CDPF, CNSS)
            n: Number of results
            current_only: Only return chunks from current law versions

        Returns:
            List of {content, article_ref, domain, year, title, distance}
        """
        if not self.master:
            return []

        where = {}
        conditions = []
        if domain:
            conditions.append({"domain": {"$eq": domain}})
        if current_only:
            conditions.append({"is_current": {"$eq": True}})

        if len(conditions) == 1:
            where = conditions[0]
        elif len(conditions) > 1:
            where = {"$and": conditions}

        results = self.master.query(
            query_texts=[question],
            n_results=n,
            where=where if where else None,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            output.append({
                "content": doc,
                "article_ref": meta.get("article_ref"),
                "domain": meta.get("domain"),
                "year": meta.get("year"),
                "title": meta.get("title"),
                "relevance_score": round(1 - dist, 3),
            })

        return output

    def get_rates(self) -> dict:
        """Load the structured rates config (use this for numeric calculations)."""
        rates_path = RATES_DIR / "tax_rates_2025.json"
        if rates_path.exists():
            with open(rates_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tunisia Tax Data Pipeline")
    parser.add_argument("--step", choices=["download", "extract", "chunk", "index", "rates", "all"],
                        default="all")
    args = parser.parse_args()

    if args.step in ("download", "all"):
        log.info("=== STEP 1: DOWNLOADING PDFs ===")
        download_documents()

    if args.step in ("extract", "all"):
        log.info("=== STEP 2: EXTRACTING TEXT ===")
        extract_all()

    if args.step in ("chunk", "all"):
        log.info("=== STEP 3: CHUNKING BY ARTICLE ===")
        chunk_all()

    if args.step in ("rates", "all"):
        log.info("=== STEP 4: GENERATING RATES CONFIG ===")
        generate_rates_config()

    if args.step in ("index", "all"):
        log.info("=== STEP 5: BUILDING VECTOR INDEX ===")
        build_index()

    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
