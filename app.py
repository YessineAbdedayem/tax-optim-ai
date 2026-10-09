"""
TaxOptimAI — Interface Streamlit
"""
import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(page_title="TaxOptimAI | Rapport Fiscal", layout="wide", initial_sidebar_state="expanded")

# Modern SaaS CSS & Enterprise colors
st.markdown("""
<style>
.step-done    {display:inline-block; padding:6px 16px; border-radius:25px; font-size:12px; font-weight:600; background:#F8FAFC; border: 1px solid #1B365D; color:#1B365D; margin:4px;}
.step-active  {display:inline-block; padding:6px 16px; border-radius:25px; font-size:12px; font-weight:600; background:#1B365D; color:#FFFFFF; margin:4px;}
.step-pending {display:inline-block; padding:6px 16px; border-radius:25px; font-size:12px; font-weight:500; background:#FFFFFF; color:#94A3B8; border:1px dashed #CBD5E1; margin:4px;}
.arrow-sep    {color:#CBD5E1; font-size:16px; margin:0 4px;}
</style>
""", unsafe_allow_html=True)

NAVY = "#1B365D"
TEAL = "#A7F3D0"
SLATE = "#64748B"

# Initialize Session State for Use Cases
if "uc_cat" not in st.session_state:
    st.session_state.update({"uc_cat": "Salarié", "uc_gross": 30000, "uc_fam": "Célibataire", "uc_child": 0, "uc_exp": 0})

with st.sidebar:
    st.markdown("## TaxOptimAI")
    st.caption("Optimisation fiscale tunisienne")
    st.markdown("---")

    user_type = st.radio(
        "Type de contribuable",
        ["Salarié", "Freelancer / Indépendant", "Entreprise (PME/TPE)"],
        horizontal=False,
    )

    st.markdown("---")

    if user_type in ("Salarié", "Freelancer / Indépendant"):
        income_type = "employee" if user_type == "Salarié" else "freelancer"
        gross_annual = st.number_input(
            "Revenu annuel brut (DT)",
            min_value=6000, max_value=500000, value=30000, step=1000
        )
        family_status = st.selectbox(
            "Situation familiale",
            ["Célibataire", "Marié sans enfants", "Marié avec enfants"]
        )
        children = 0
        if "enfants" in family_status:
            children = st.number_input(
                "Nombre d'enfants", min_value=0, max_value=8, value=2
            )
        expenses = st.number_input(
            "Dépenses professionnelles (DT)",
            min_value=0, max_value=50000, value=0, step=500
        )
        entreprise_data = None

    else:
        income_type     = "entreprise"
        gross_annual    = 0
        family_status   = "single"
        children        = 0
        expenses        = 0

        st.markdown("**Informations entreprise**")

        chiffre_affaires = st.number_input(
            "Chiffre d'affaires annuel HT (DT)",
            min_value=0, max_value=50000000, value=500000, step=10000
        )
        charges_exploit = st.number_input(
            "Charges d'exploitation (DT)",
            min_value=0, max_value=50000000, value=200000, step=5000
        )
        salaires_total  = st.number_input(
            "Masse salariale totale (DT)",
            min_value=0, max_value=10000000, value=100000, step=5000
        )
        entretien       = st.number_input(
            "Entretien & Réparations (DT)",
            min_value=0, max_value=1000000, value=5000, step=1000
        )
        autres_charges  = st.number_input(
            "Autres charges déductibles (DT)",
            min_value=0, max_value=5000000, value=15000, step=1000
        )
        charges_non_ded = st.number_input(
            "Charges NON déductibles (DT)",
            min_value=0, max_value=1000000, value=0, step=1000,
            help="Amendes, pénalités, dépenses non justifiées"
        )
        charges_interet = st.number_input(
            "Charges d'intérêts (DT)",
            min_value=0, max_value=500000, value=5000, step=1000
        )
        capital_social  = st.number_input(
            "Capital social (DT)",
            min_value=1000, max_value=10000000, value=50000, step=1000
        )
        secteur = st.selectbox(
            "Secteur d'activité",
            ["Services", "Commerce", "Industrie", "Agriculture", "Technologie",
             "Tourisme", "Santé", "Export"]
        )
        statut_juridique = st.selectbox(
            "Statut juridique",
            ["SARL", "SUARL", "SA", "Société de personnes", "Entreprise individuelle"],
            help=(
                "Utilisé pour :\n"
                "• SUARL/SARL → déduction 20% si centre gestion intégré\n"
                "• SA → retenue 10% sur dividendes distribués\n"
                "• Entreprise individuelle → soumise à l'IRPP, pas l'IS"
            )
        )
        regime_tva = st.selectbox(
            "Régime TVA",
            ["standard", "franchise", "export_exonere"]
        )
        tva_deductible = st.number_input(
            "TVA déductible (DT)",
            min_value=0, max_value=50000000, value=30000, step=1000,
            help="TVA récupérable sur achats et charges (ex: 19% des charges déductibles)"
        )
        oriente_export = st.checkbox("Orienté Export (>= 80% CA)")

        entreprise_data = {
            "chiffre_affaires":  chiffre_affaires,
            "charges_exploit":   charges_exploit,
            "salaires_total":    salaires_total,
            "entretien":         entretien,
            "autres_charges":    autres_charges,
            "charges_non_ded":   charges_non_ded,
            "charges_interet":   charges_interet,
            "capital_social":    capital_social,
            "secteur":           secteur,
            "statut_juridique":  statut_juridique,
            "regime_tva":        regime_tva,
            "oriente_export":    oriente_export,
            "tva_deductible":    tva_deductible,
        }

    st.markdown("---")
    run_btn = st.button(
        "Analyser",
        type="primary",
        use_container_width=True
    )
    st.markdown("---")
    st.caption("Basé sur LF n°2024-48 · 2025")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Dashboard Stratégique")
st.caption("Optimisation Fiscale Tunisie 2026")

if not run_btn:
    st.info("Veuillez sélectionner un Use Case ou remplir le profil, puis cliquer sur 'Générer le Rapport'.")
    st.stop()

# Mapping
family_map = {
    "Célibataire": "single",
    "Marié sans enfants": "married",
    "Marié avec enfants": "married_with_children",
}

if income_type == "entreprise" and entreprise_data:
    profile = {
        "income_type":      "entreprise",
        "gross_annual":     entreprise_data["chiffre_affaires"],
        "gross_monthly":    entreprise_data["chiffre_affaires"] / 12,
        "family_status":    "single",
        "children_count":   0,
        "deductions":       {},
        "expenses":         entreprise_data,
        # Context for LLM agents — forces IS references not IRPP
        "tax_regime":       "IS",
        "legal_form":       entreprise_data.get("statut_juridique", "SARL"),
        "secteur":          entreprise_data.get("secteur", "Services"),
        "taux_is":          0.35 if entreprise_data.get("secteur") in
                            ["Banques","Assurances","Télécoms","Hydrocarbures"]
                            else 0.15,
        "note_fiscal":      (
            "ENTREPRISE soumise à l'IS (Impôt sur les Sociétés). "
            "Ne pas citer le Code IRPP. "
            "Utiliser uniquement : Code IS, Code TVA, CDPF, Code CII. "
            "Articles pertinents : Art.37 LF2025 (taux IS), Art.49 (minimum IS), "
            "Art.7 CII (déduction investissement), Art.22 CII (R&D), "
            "Art.62 CDPF (conservation pièces)."
        ),
    }
else:
    income_map_local = {
        "Salarié": "employee",
        "Freelancer / Indépendant": "freelancer",
    }
    profile = {
        "income_type":    income_type,
        "gross_annual":   float(gross_annual),
        "gross_monthly":  float(gross_annual) / 12,
        "family_status":  family_map.get(family_status, "single"),
        "children_count": int(children),
        "deductions":     {},
        "expenses":       {"declared": float(expenses)} if expenses > 0 else {},
    }

# Pipeline Display
st.markdown("##### Progression de l'Analyse")
pipeline_placeholder = st.empty()
progress_bar = st.progress(0)
STEPS = ["Analyse Profil", "Cadre Légal", "Calculs", "Conformité", "Synthèse"]

def render_pipeline(current: int):
    html = ""
    for i, s in enumerate(STEPS):
        if i < current: html += f'<span class="step-done">{s}</span>'
        elif i == current: html += f'<span class="step-active">{s}</span>'
        else: html += f'<span class="step-pending">{s}</span>'
        if i < len(STEPS) - 1: html += '<span class="arrow-sep">→</span>'
    pipeline_placeholder.markdown(html, unsafe_allow_html=True)
    progress_bar.progress((current + 1) / len(STEPS))

# Agent Execution
try:
    from agents.langgraph_agents import (fiscal_strategy_agent, simulation_optimization_agent, risk_compliance_agent, explanation_reporting_agent)
    from agents.state_schema import TaxOptimizationState
    from agents.pdf_reporter import generate_pdf_report
    from agents.article_linker import linkify_articles

    state: TaxOptimizationState = {
        "user_input": "", "financial_profile": profile, "strategies": [], "selected_strategy": None,
        "simulation": None, "risks": [], "report": "", "current_agent": "", "messages": [],
        "current_question_index": 0, "questions": [], "answers": {}, "questioning_complete": True, "next_question": None,
    }

    render_pipeline(0)
    with st.spinner("Recherche des lois applicables..."):
        render_pipeline(1)
        state = fiscal_strategy_agent(state)
    with st.spinner("Simulation financière en cours..."):
        render_pipeline(2)
        state = simulation_optimization_agent(state)
    with st.spinner("Audit de conformité..."):
        render_pipeline(3)
        state = risk_compliance_agent(state)
    with st.spinner("Rédaction finale..."):
        render_pipeline(4)
        state = explanation_reporting_agent(state)

    progress_bar.empty()
    pipeline_placeholder.markdown("".join(f'<span class="step-done">{s}</span>' + ('<span class="arrow-sep">→</span>' if i < len(STEPS)-1 else "") for i, s in enumerate(STEPS)), unsafe_allow_html=True)

    sim = state.get("simulation", {}) or {}
    strats = state.get("strategies", []) or []
    risks = state.get("risks", []) or []
    report_t = state.get("report", "") or ""
    current_tax = sim.get("current_tax", 0)
    optimized = sim.get("optimized_tax", 0)
    savings = sim.get("savings", 0)
    cnss = sim.get("current_cnss_annual", 0)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs implementation ────────────────────────────────────────────────────
    tab_dash, tab_assist, tab_audit = st.tabs(["📊 Dashboard Fiscal", "📝 Assistant Déclaration", "🔍 Traçabilité IA (Audit)"])

    # TAB 1: DASHBOARD
    with tab_dash:
        st.markdown("### Résultats fiscaux")

        if income_type == "entreprise" and entreprise_data:
            # ── ENTREPRISE CALCULATIONS ───────────────────────────────────────────────
            # All formulas displayed inline for transparency

            CA        = entreprise_data["chiffre_affaires"]
            charges   = entreprise_data["charges_exploit"]
            salaires  = entreprise_data["salaires_total"]
            entretien_v = entreprise_data["entretien"]
            autres    = entreprise_data["autres_charges"]
            non_ded   = entreprise_data["charges_non_ded"]
            interets  = entreprise_data["charges_interet"]
            capital   = entreprise_data["capital_social"]
            secteur_v = entreprise_data["secteur"]
            statut_v  = entreprise_data["statut_juridique"]
            regime_v  = entreprise_data["regime_tva"]
            export_v  = entreprise_data["oriente_export"]

            # IS rate — LF 2025 Art. 37
            # Banques/Assurances/Télécoms/Hydrocarbures → 35%
            # Autres entreprises → 15%
            secteurs_35 = ["Banques", "Assurances", "Télécoms", "Hydrocarbures"]
            taux_is = 0.35 if secteur_v in secteurs_35 else 0.15
            taux_is_label = "35% (secteur réglementé)" if taux_is == 0.35 else "15% (taux standard LF 2025)"

            # Résultat comptable = CA - toutes charges
            total_charges_comptables = charges + salaires + entretien_v + autres + interets
            resultat_comptable = CA - total_charges_comptables

            # Résultat fiscal = résultat comptable + réintégration charges non déductibles
            # Formule : résultat fiscal = résultat comptable + charges_non_ded
            resultat_fiscal = resultat_comptable + non_ded
            # IS standard = résultat fiscal × taux_is (si résultat > 0)
            is_standard = max(0, resultat_fiscal) * taux_is

            # Minimum IS = 0.2% du CA brut (Art. IS minimum)
            minimum_is = CA * 0.002
            is_standard = max(is_standard, minimum_is)

            # ── IS Optimisé — real optimization levers (LF 2025 + CII) ──────────────
            optimisation_notes = []
            base_optimisee = resultat_fiscal

            # Levier 1 — Export total → exonération IS complète (Art. CII)
            if export_v:
                is_optimise = 0.0
                optimisation_notes.append("Exonération IS totale — Entreprise exportatrice (Art. CII)")

            else:
                # Levier 2 — Déduction investissement matériel (Art. 7 CII)
                # 30% du bénéfice réinvesti peut être déduit si achat équipement
                deduction_invest = min(base_optimisee * 0.30, base_optimisee)
                base_optimisee_levier2 = max(0, base_optimisee - deduction_invest)

                # Levier 3 — Déduction charges R&D pour secteur Technologie (Art. 22 CII)
                if secteur_v == "Technologie":
                    deduction_rd = min(charges * 0.50, 50000)
                    base_optimisee_levier2 = max(0, base_optimisee_levier2 - deduction_rd)
                    optimisation_notes.append(
                        f"Déduction R&D Technologie 50% charges : -{deduction_rd:,.0f} DT (Art. 22 CII)"
                    )

                # Levier 4 — Développement régional si applicable
                if secteur_v == "Agriculture":
                    base_optimisee_levier2 = max(0, base_optimisee_levier2 * 0.50)
                    optimisation_notes.append(
                        "Déduction développement agricole 50% (Art. CII développement régional)"
                    )

                # Levier 5 — Statut SUARL/SARL — déduction 20% si centre gestion intégré
                if statut_v in ("SUARL", "SARL"):
                    deduction_cgi = base_optimisee_levier2 * 0.20
                    base_optimisee_levier2 = max(0, base_optimisee_levier2 - deduction_cgi)
                    optimisation_notes.append(
                        f"Déduction 20% centre gestion intégré : -{deduction_cgi:,.0f} DT (Art. 2971 Code IS)"
                    )

                is_optimise = max(base_optimisee_levier2 * taux_is, minimum_is)
                optimisation_notes.append(
                    f"Déduction investissement 30% bénéfice : -{deduction_invest:,.0f} DT (Art. 7 CII)"
                )

            if not optimisation_notes:
                optimisation_notes.append("Aucun levier d'optimisation applicable détecté")

            is_note = " | ".join(optimisation_notes)
            economie_is = is_standard - is_optimise

            # TVA collectée = CA × taux TVA selon régime
            tva_rates = {"standard": 0.19, "franchise": 0.00, "export_exonere": 0.00}
            taux_tva  = tva_rates.get(regime_v, 0.19)
            tva_collectee  = CA * taux_tva
            tva_deductible = entreprise_data["tva_deductible"]
            tva_nette_standard = tva_collectee - tva_deductible
            tva_nette_optimisee = tva_nette_standard  # TVA net = same (no optimization on TVA base yet)

            # CNSS patronale = masse salariale × 17.07% (LF 2025)
            taux_cnss_patron = 0.1707
            cnss_patronale = salaires * taux_cnss_patron

            # Totaux — separate direct fiscal burden from taxes collected
            charge_fiscale_directe_standard = is_standard + cnss_patronale
            charge_fiscale_directe_optimise = is_optimise + cnss_patronale
            taxes_collectees_standard = tva_nette_standard
            taxes_collectees_optimise = tva_nette_optimisee
            economie_nette  = charge_fiscale_directe_standard - charge_fiscale_directe_optimise

            # ── Display metrics ────────────────────────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "IS Standard",
                f"{is_standard:,.0f} DT",
                help=(
                    f"Formule : max(Résultat fiscal × {taux_is:.0%}, Minimum IS)\n\n"
                    f"Résultat comptable = CA ({CA:,.0f}) − Charges ({total_charges_comptables:,.0f}) = {resultat_comptable:,.0f} DT\n"
                    f"Résultat fiscal = {resultat_comptable:,.0f} + Réintégrations ({non_ded:,.0f}) = {resultat_fiscal:,.0f} DT\n"
                    f"IS brut = {max(0,resultat_fiscal):,.0f} × {taux_is:.0%} = {max(0,resultat_fiscal)*taux_is:,.0f} DT\n"
                    f"Minimum IS (0.2% CA) = {minimum_is:,.0f} DT\n"
                    f"IS retenu = {is_standard:,.0f} DT ({taux_is_label})\n\n"
                    f"Source : Art. 37 LF 2025 — Code IS"
                )
            )
            m2.metric(
                "IS Optimisé",
                f"{is_optimise:,.0f} DT",
                delta=f"-{economie_is:,.0f} DT" if economie_is > 0 else "Aucune économie IS",
                help=(
                    f"Leviers d'optimisation appliqués :\n\n"
                    + "\n".join(f"• {n}" for n in optimisation_notes)
                    + f"\n\nIS standard    : {is_standard:,.0f} DT"
                    + f"\nIS optimisé    : {is_optimise:,.0f} DT"
                    + f"\nÉconomie IS    : {economie_is:,.0f} DT"
                )
            )
            m3.metric(
                "TVA Collectée",
                f"{tva_collectee:,.0f} DT",
                help=(
                    f"Formule : CA HT ({CA:,.0f} DT) × Taux TVA ({taux_tva:.0%})\n\n"
                    f"Régime TVA sélectionné : {regime_v}\n"
                    f"• standard → 19%\n"
                    f"• franchise → 0% (CA < seuil)\n"
                    f"• export_exonere → 0%\n\n"
                    f"TVA collectée = {CA:,.0f} × {taux_tva:.0%} = {tva_collectee:,.0f} DT\n\n"
                    f"Source : Code TVA 2024 — Art. 4 et 11"
                )
            )
            m4.metric(
                "TVA Nette Payable",
                f"{tva_nette_standard:,.0f} DT",
                delta=f"-0 DT",
                help=(
                    f"TVA nette = TVA collectée - TVA déductible\n\n"
                    f"TVA collectée : {tva_collectee:,.0f} DT\n"
                    f"TVA déductible : {tva_deductible:,.0f} DT\n"
                    f"TVA nette payable : {tva_nette_standard:,.0f} DT\n\n"
                    f"Note : TVA non optimisable sans audit approfondi."
                )
            )

            m5, m6, m7, m8 = st.columns(4)
            m5.metric(
                "CNSS Patronale",
                f"{cnss_patronale:,.0f} DT",
                help=(
                    f"Formule : Masse salariale ({salaires:,.0f} DT) × 17.07%\n\n"
                    f"CNSS patronale = {salaires:,.0f} × 17.07% = {cnss_patronale:,.0f} DT\n\n"
                    f"Source : LF 2025 — Taux CNSS employeur 2025"
                )
            )
            m6.metric(
                "Charge Fiscale Directe",
                f"{charge_fiscale_directe_standard:,.0f} DT",
                help=(
                    f"= IS ({is_standard:,.0f}) + CNSS ({cnss_patronale:,.0f})\n"
                    f"= {charge_fiscale_directe_standard:,.0f} DT\n\n"
                    f"Exclut TVA (taxe collectée pour l'État)"
                )
            )
            m7.metric(
                "Charge Fiscale Directe Optimisée",
                f"{charge_fiscale_directe_optimise:,.0f} DT",
                delta=f"-{economie_nette:,.0f} DT" if economie_nette > 0 else None,
                help=(
                    f"= IS optimisé ({is_optimise:,.0f}) + CNSS ({cnss_patronale:,.0f})\n"
                    f"= {charge_fiscale_directe_optimise:,.0f} DT"
                )
            )
            m8.metric(
                "Économie Nette",
                f"{economie_nette:,.0f} DT",
                delta=f"−{economie_nette/charge_fiscale_directe_standard*100:.1f}% de la charge fiscale directe" if charge_fiscale_directe_standard > 0 else None,
                help=(
                    f"= IS économisé ({economie_is:,.0f} DT)\n"
                    f"+ TVA économisée (0 DT — TVA non optimisable sans audit)\n"
                    f"+ CNSS économisée (0 DT — taux légal fixe)\n\n"
                    f"Charge directe standard : {charge_fiscale_directe_standard:,.0f} DT\n"
                    f"Charge directe optimisée : {charge_fiscale_directe_optimise:,.0f} DT\n"
                    f"Économie nette : {economie_nette:,.0f} DT"
                )
            )

            # ── Justification détaillée ────────────────────────────────────────────────
            with st.expander("Voir la justification complète des calculs"):
                st.markdown(f"""
**Résultat Comptable**
CA HT                        : {CA:>15,.0f} DT
− Charges d'exploitation     : {charges:>15,.0f} DT
− Masse salariale            : {salaires:>15,.0f} DT
− Entretien & Réparations    : {entretien_v:>15,.0f} DT
− Autres charges             : {autres:>15,.0f} DT
− Charges d'intérêts         : {interets:>15,.0f} DT
= Résultat comptable         : {resultat_comptable:>15,.0f} DT

**Résultat Fiscal**
Résultat comptable           : {resultat_comptable:,.0f} DT

Réintégrations (non ded.)  : {non_ded:>15,.0f} DT
= Résultat fiscal            : {resultat_fiscal:>15,.0f} DT


**Calcul IS (Art. 37 LF 2025)**
Résultat fiscal imposable    : {max(0,resultat_fiscal):>15,.0f} DT
× Taux IS                    : {taux_is:>15.0%}
= IS selon barème            : {max(0,resultat_fiscal)*taux_is:>15,.0f} DT
Minimum IS (0.2% CA)       : {minimum_is:>15,.0f} DT
IS retenu (max des deux)     : {is_standard:>15,.0f} DT

**Calcul TVA (Code TVA 2024)**
CA HT                        : {CA:>15,.0f} DT
× Taux TVA ({regime_v})      : {taux_tva:>15.0%}
= TVA collectée              : {tva_collectee:>15,.0f} DT
− TVA déductible             : {tva_deductible:>15,.0f} DT
= TVA nette payable          : {tva_nette_standard:>15,.0f} DT

**Calcul CNSS Patronale (LF 2025)**
Masse salariale              : {salaires:>15,.0f} DT
× Taux patronal (17.07%)     : {taux_cnss_patron:>15.2%}
= CNSS patronale             : {cnss_patronale:>15,.0f} DT

**Récapitulation**
IS                           : {is_standard:>15,.0f} DT
TVA nette                    : {tva_nette_standard:>15,.0f} DT
CNSS patronale               : {cnss_patronale:>15,.0f} DT
= CHARGE FISCALE DIRECTE     : {charge_fiscale_directe_standard:>15,.0f} DT
+ TVA collectée (pour État)  : {tva_collectee:>15,.0f} DT
                """)

            # Inject into simulation for agents
            sim = {
                "current_tax":          is_standard,
                "optimized_tax":        is_optimise,
                "savings":              economie_nette,
                "net_impact":           economie_nette,
                "current_cnss_annual":  cnss_patronale,
                "all_scenarios":        [],
                "note":                 is_note,
                "tva_collectee":        tva_collectee,
                "tva_deductible":       tva_deductible,
                "tva_nette":            tva_nette_standard,
                "charge_fiscale_directe_standard": charge_fiscale_directe_standard,
                "charge_fiscale_directe_optimise": charge_fiscale_directe_optimise,
                "resultat_fiscal":      resultat_fiscal,
                "taux_is":              taux_is,
                "optimisation_notes":   optimisation_notes,
            }

        else:
            # ── EMPLOYEE / FREELANCER — existing metrics (keep unchanged) ─────────────
            gross = profile.get("gross_annual", 0)
            cnss  = sim.get("current_cnss_annual", 0) if 'sim' in dir() else 0
            frais_pro = min(gross * 0.10, 2000)
            eff_rate  = (current_tax / gross * 100) if gross > 0 else 0
            savings_pct = (savings / current_tax * 100) if current_tax > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "IRPP actuel", f"{current_tax:,.0f} DT",
                help=(
                    f"Barème progressif LF 2025 sur base imposable\n\n"
                    f"Brut : {gross:,.0f} DT\n"
                    f"− CNSS ({9.68 if income_type=='employee' else 14.71}%) : {cnss:,.0f} DT\n"
                    f"− Frais pro (10%, max 2000) : {frais_pro:,.0f} DT\n"
                    f"= Base : {max(0,gross-cnss-frais_pro):,.0f} DT\n"
                    f"Taux effectif : {eff_rate:.1f}%"
                )
            )
            m2.metric(
                "IRPP optimisé", f"{optimized:,.0f} DT",
                delta=f"-{savings:,.0f} DT" if savings > 0 else None,
                help=f"Après déductions — économie {savings_pct:.1f}%"
            )
            m3.metric("Économies annuelles", f"{savings:,.0f} DT")
            m4.metric(
                "CNSS annuelle", f"{cnss:,.0f} DT",
                help=f"{'9.68%' if income_type=='employee' else '14.71%'} × {gross:,.0f} DT"
            )

    col_chart, col_strat = st.columns(2)
    with col_chart:
            with st.container(border=True):
                st.markdown("#### Comparatif Fiscal")
                fig = go.Figure(data=[
                    go.Bar(name='Standard', x=['IRPP'], y=[current_tax], marker_color=NAVY),
                    go.Bar(name='Optimisé', x=['IRPP'], y=[optimized], marker_color=TEAL)
                ])
                fig.update_layout(height=250, margin=dict(t=10, b=10, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
    with col_strat:
            with st.container(border=True):
                st.markdown("#### Répartition (Optimisée)")
                net = max(0, float(gross_annual) - optimized - cnss)
                fig2 = go.Figure(go.Pie(labels=["IRPP", "CNSS", "Revenu Net"], values=[optimized, cnss, net], marker_colors=[NAVY, SLATE, TEAL], hole=0.6))
                fig2.update_layout(height=250, margin=dict(t=10, b=10, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Rapport d'Analyse Détaillé")
    with st.container(border=True):
        if report_t:
            st.markdown(linkify_articles(report_t), unsafe_allow_html=True)
        else:
            st.info("Le rapport n'a pas pu être généré.")
    st.markdown("---")
    with st.spinner("Préparation du document PDF..."):
        pdf_bytes = generate_pdf_report(profile=profile, strategies=strats, simulation=sim, risks=risks, report_text=report_t)
    st.download_button(label="📄 Télécharger le Rapport Officiel (PDF)", data=pdf_bytes, file_name="Rapport_Fiscal_2026.pdf", mime="application/pdf", use_container_width=True, type="primary")
    # TAB 2: ASSISTANT DECLARATION
    with tab_assist:
        st.markdown("### 📝 Guide de Remplissage - Déclaration de l'IRPP")
        st.info("💡 **Explicabilité Métier :** Cet outil agit comme un assistant. Il vous indique exactement quelles valeurs reporter sur votre déclaration d'impôt (La feuille bleue) pour éviter les erreurs lors du passage à la recette des finances.")
        
        with st.container(border=True):
            st.markdown("#### Valeurs à reporter sur votre déclaration :")
            st.markdown(f"**Rubrique Revenus :**")
            st.markdown(f"- Revenu Annuel Brut déclaré : `{gross_annual:,.0f} DT`")
            if income_type == "Freelancer / Indépendant" and expenses > 0:
                st.markdown(f"- Déduction au titre des charges professionnelles : `{expenses:,.0f} DT`")
            
            st.markdown(f"**Rubrique Déductions Communes :**")
            deduc_fam = 300 if "Marié" in family_status else 0
            deduc_enf = int(children) * 100
            st.markdown(f"- Chef de famille (si applicable) : `{deduc_fam} DT`")
            st.markdown(f"- Enfants à charge : `{deduc_enf} DT`")
            st.markdown(f"- Montant de l'IRPP dû (à payer) : **`{optimized:,.0f} DT`**")

    # TAB 3: AUDIT & TRACEABILITY
    with tab_audit:
        st.markdown("### 🔍 Transparence des Agents IA (Mode Audit)")
        st.info("💡 **Explicabilité IA :** Cette section montre les résultats intermédiaires générés par chaque agent de notre pipeline LangGraph. Elle prouve que le résultat final n'est pas une 'boîte noire'.")
        
        with st.expander("🤖 Agent 1 : Stratégie & Cadre Légal (Données Brutes)"):
            st.write(strats if strats else "Aucune stratégie spécifique générée.")
            
        with st.expander("🧮 Agent 2 : Simulation (Moteur de Calcul JSON)"):
            st.json(sim)
            
        with st.expander("⚖️ Agent 3 : Audit & Conformité (Vérification des Risques)"):
            if risks:
                for r in risks:
                    st.write(f"**Niveau de Risque :** {r.get('risk_level', 'Non défini')}")
                    st.write("**Recommandations :**", r.get('recommendations', []))
                    st.write("**Problèmes :**", r.get('issues', []))
            else:
                st.write("Aucun risque identifié.")

except Exception as e:
    st.error(f"Erreur de traitement : {e}")
