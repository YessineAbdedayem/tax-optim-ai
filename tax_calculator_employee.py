"""
Tax Calculator for Tunisian Employee (2025)
===========================================

Calculates IRPP (income tax) and CNSS (social security) for a salaried employee
based on the 2025 tax regulations.

Example employee data:
- Ahmed Ben Ali
- Monthly gross salary: 2500 DT
- Marital status: Married with 2 children
- Sector: Private company (40h/week)
- No additional deductions

Usage:
    python tax_calculator_employee.py
"""

import json
from pathlib import Path
from typing import Dict, Any

# Load tax rates
RATES_FILE = Path("./tunisia_tax_data/rates_config/tax_rates_2025.json")

def load_tax_rates() -> Dict[str, Any]:
    """Load tax rates from JSON file."""
    with open(RATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Correct IRPP brackets LF 2025 — source: secu.tn verified
# 8 tranches (not 6 as previously coded)
IRPP_BRACKETS_2025 = [
    {"min": 0,     "max": 5000,  "rate": 0.00},
    {"min": 5000,  "max": 10000, "rate": 0.15},
    {"min": 10000, "max": 20000, "rate": 0.25},
    {"min": 20000, "max": 30000, "rate": 0.30},
    {"min": 30000, "max": 40000, "rate": 0.33},
    {"min": 40000, "max": 50000, "rate": 0.36},
    {"min": 50000, "max": 70000, "rate": 0.38},
    {"min": 70000, "max": None,  "rate": 0.40},
]

# CSS rate — 0.5% for 2023-2024-2025, 0% from 2026
# Source: secu.tn + LF 2026
CSS_RATE_BY_YEAR = {
    2023: 0.005,
    2024: 0.005,
    2025: 0.005,
    2026: 0.000,  # supprimée LF 2026
}


def calculate_irpp_annual(
    gross_annual: float,
    deductions: float,
    rates: Dict,
    year: int = 2025,
) -> dict:
    """
    Calculate annual IRPP using correct LF 2025 brackets (secu.tn verified).
    Also calculates CSS (Contribution Sociale Solidarité).

    Returns dict with:
      - irpp: IRPP amount
      - css: CSS amount
      - total: irpp + css
      - taxable_income: base imposable
      - bracket_detail: breakdown per tranche
      - effective_rate: total / gross_annual
    """
    taxable_income = max(0, gross_annual - deductions)

    irpp = 0.0
    bracket_detail = []

    for bracket in IRPP_BRACKETS_2025:
        bmin = bracket["min"]
        bmax = bracket["max"]
        rate = bracket["rate"]

        if taxable_income <= bmin:
            break

        if bmax is None:
            amount = (taxable_income - bmin) * rate
            irpp += amount
            bracket_detail.append({
                "label":  f"> {bmin:,} DT à {rate:.0%}",
                "base":   round(taxable_income - bmin, 2),
                "rate":   rate,
                "amount": round(amount, 2),
            })
            break
        else:
            portion = min(taxable_income, bmax) - bmin
            amount  = portion * rate
            irpp   += amount
            bracket_detail.append({
                "label":  f"{bmin:,}–{bmax:,} DT à {rate:.0%}",
                "base":   round(portion, 2),
                "rate":   rate,
                "amount": round(amount, 2),
            })

    # Apply minimum IRPP (100 DT)
    minimum_irpp = rates.get("IRPP", {}).get("minimum_irpp", 100)
    irpp = max(irpp, minimum_irpp)

    # CSS — 0.5% on taxable income if taxable > 5000 DT (2025)
    # Exonerated if taxable_income < 5000 DT
    css_rate = CSS_RATE_BY_YEAR.get(year, 0.005)
    css = taxable_income * css_rate if taxable_income >= 5000 else 0.0

    total = irpp + css
    effective_rate = total / gross_annual if gross_annual > 0 else 0

    return {
        "irpp":           round(irpp, 2),
        "css":            round(css, 2),
        "total":          round(total, 2),
        "taxable_income": round(taxable_income, 2),
        "bracket_detail": bracket_detail,
        "effective_rate": round(effective_rate, 4),
        "minimum_applied": irpp == minimum_irpp,
    }

def calculate_cnss_monthly(gross_monthly: float, rates: Dict) -> Dict[str, float]:
    """
    Calculate monthly CNSS contributions.

    Args:
        gross_monthly: Gross monthly salary
        rates: CNSS rates from config

    Returns:
        Dict with salarial, patronal, and total contributions
    """
    cnss = rates["CNSS"]["regime_general_salarie_2025"]

    # Apply ceiling
    assiette = min(gross_monthly, cnss["plafond_assiette"])

    salarial = assiette * cnss["part_salariale"]
    patronal = assiette * cnss["part_patronale"]

    return {
        "salarial": salarial,
        "patronal": patronal,
        "total": salarial + patronal
    }

def calculate_employee_taxes(employee_data: Dict[str, Any], rates: Dict) -> Dict[str, Any]:
    """
    Calculate all taxes for an employee.

    Args:
        employee_data: Employee information
        rates: Tax rates

    Returns:
        Dict with all calculations
    """
    # Monthly calculations
    gross_monthly = employee_data["gross_monthly"]
    cnss_monthly = calculate_cnss_monthly(gross_monthly, rates)

    # Annual calculations for IRPP
    gross_annual = gross_monthly * 12

    # CNSS annual deduction (deducted from gross before IRPP)
    cnss_annual = cnss_monthly["salarial"] * 12

    # Forfait frais professionnels for employees: 10% capped at 2000 DT
    frais_pro = min(
        gross_annual * rates["IRPP"]["forfait_frais_professionnels_rate"],
        rates["IRPP"]["forfait_frais_professionnels_max"]
    )

    # Family deductions — support both "marital_status" and "family_status" keys
    family_status = employee_data.get("family_status") or employee_data.get("marital_status", "single")
    deductions = cnss_annual + frais_pro

    if family_status in ("married", "married_with_children"):
        deductions += rates["IRPP"]["deduction_chef_famille"]

    children = employee_data.get("children_count") or employee_data.get("children", 0)
    deductions += min(children, rates["IRPP"]["deduction_max_enfants"]) * rates["IRPP"]["deduction_enfant"]

    irpp_result  = calculate_irpp_annual(gross_annual, deductions, rates)
    irpp_annual  = irpp_result["irpp"]
    css_annual   = irpp_result["css"]
    irpp_monthly = irpp_annual / 12
    css_monthly  = css_annual / 12

    # Withholding tax (retenue à la source)
    withholding_rate = rates["IRPP"]["taux_retenue_salaire"]
    withholding_monthly = gross_monthly * withholding_rate

    # Net calculations
    total_deductions_monthly = cnss_monthly["salarial"] + irpp_monthly
    net_monthly = gross_monthly - total_deductions_monthly

    # Employer cost
    employer_cost_monthly = gross_monthly + cnss_monthly["patronal"]

    return {
        "employee": employee_data,
        "gross_monthly": gross_monthly,
        "gross_annual": gross_annual,
        "deductions": {
            "cnss_annual": cnss_annual,
            "frais_professionnels": frais_pro,
            "family_deductions": deductions - cnss_annual - frais_pro,
            "total_deductions_annual": deductions,
            "cnss_salarial_monthly": cnss_monthly["salarial"],
            "irpp_monthly":  irpp_monthly,
            "css_monthly":   css_monthly,
            "withholding_monthly": withholding_monthly,
            "total_impots_monthly": irpp_monthly + css_monthly,
        },
        "net_monthly": net_monthly,
        "employer_cost_monthly": employer_cost_monthly,
        "cnss_patronal_monthly": cnss_monthly["patronal"],
        "tax_breakdown": {
            "cnss_total_monthly":  cnss_monthly["total"],
            "cnss_annual":         cnss_annual,
            "irpp_annual":         irpp_annual,
            "css_annual":          css_annual,
            "total_impots_annual": irpp_annual + css_annual,
            "effective_irpp_rate": irpp_annual / gross_annual if gross_annual > 0 else 0,
            "effective_total_rate": (irpp_annual + css_annual) / gross_annual if gross_annual > 0 else 0,
            "bracket_detail":      irpp_result["bracket_detail"],
            "taxable_income":      irpp_result["taxable_income"],
        }
    }

def calculate_freelancer_taxes(freelancer_data: Dict[str, Any], rates: Dict) -> Dict[str, Any]:
    """
    Calculate taxes for a freelancer/independent worker.

    Args:
        freelancer_data: Freelancer information
        rates: Tax rates

    Returns:
        Dict with all calculations
    """
    # Monthly revenue
    revenue_monthly = freelancer_data["revenue_monthly"]

    # CNSS independent (14.71% on declared revenue)
    cnss_independent = rates["CNSS"]["regime_independant_2025"]["taux"]
    cnss_monthly = revenue_monthly * cnss_independent

    # Annual calculations for IRPP
    revenue_annual = revenue_monthly * 12

    # Forfait frais professionnels (10% or 2000 DT max)
    frais_pro = min(revenue_annual * rates["IRPP"]["forfait_frais_professionnels_rate"],
                   rates["IRPP"]["forfait_frais_professionnels_max"])

    # CNSS annual — deducted from gross before IRPP (same as employees)
    cnss_annual = cnss_monthly * 12

    # Deductions: CNSS + frais pro + family
    deductions = cnss_annual + frais_pro
    family_status = freelancer_data.get("family_status") or freelancer_data.get("marital_status", "single")
    if family_status in ("married", "married_with_children"):
        deductions += rates["IRPP"]["deduction_chef_famille"]

    children = freelancer_data.get("children_count") or freelancer_data.get("children", 0)
    deductions += min(children, rates["IRPP"]["deduction_max_enfants"]) * rates["IRPP"]["deduction_enfant"]

    # Taxable income
    taxable_income = max(0, revenue_annual - deductions)

    # IRPP calculation — reuse the shared function for consistency
    irpp_result = calculate_irpp_annual(taxable_income, 0, rates)
    irpp_annual = irpp_result["irpp"]
    css_annual  = irpp_result["css"]
    irpp_monthly = irpp_annual / 12

    # Net income
    total_deductions_monthly = cnss_monthly + irpp_monthly
    net_monthly = revenue_monthly - total_deductions_monthly

    return {
        "freelancer": freelancer_data,
        "revenue_monthly": revenue_monthly,
        "revenue_annual": revenue_annual,
        "deductions": {
            "frais_professionnels": frais_pro,
            "family_deductions": deductions - frais_pro,
            "cnss_monthly": cnss_monthly,
            "irpp_monthly": irpp_monthly
        },
        "net_monthly": net_monthly,
        "tax_breakdown": {
            "cnss_rate":           cnss_independent,
            "cnss_annual":         round(cnss_annual, 2),
            "cnss_monthly":        round(cnss_monthly, 2),
            "irpp_annual":         irpp_annual,
            "css_annual":          css_annual,
            "total_impots_annual": irpp_annual + css_annual,
            "effective_irpp_rate": irpp_annual / revenue_annual if revenue_annual > 0 else 0,
            "effective_total_rate": (irpp_annual + css_annual) / revenue_annual if revenue_annual > 0 else 0,
            "taxable_income":      irpp_result["taxable_income"],
            "bracket_detail":      irpp_result["bracket_detail"],
        }
    }

# Example employee
EXAMPLE_EMPLOYEE = {
    "name": "Ahmed Ben Ali",
    "gross_monthly": 2500.0,  # DT
    "marital_status": "married",
    "children": 2,
    "sector": "private_company",
    "working_hours": 40,
    "position": "employee"
}

# Example freelancer
EXAMPLE_FREELANCER = {
    "name": "Fatma Trabelsi",
    "revenue_monthly": 3500.0,  # DT net mensuel (revenus déclarés)
    "marital_status": "single",
    "children": 0,
    "sector": "services",
    "activity": "freelance_consultant",
    "tva_regime": "franchise"  # Below threshold
}

def main():
    # Load rates
    rates = load_tax_rates()

    print("=== CALCULATEUR D'IMPÔTS TUNISIENS 2025 ===\n")

    # Calculate for employee example
    print("1️⃣ EMPLOYÉ SALARIÉ")
    print("-" * 40)
    employee_result = calculate_employee_taxes(EXAMPLE_EMPLOYEE, rates)

    print(f"Employé: {employee_result['employee']['name']}")
    print(f"Salaire brut mensuel: {employee_result['gross_monthly']:.2f} DT")
    print(f"Statut: {employee_result['employee']['marital_status']} avec {employee_result['employee']['children']} enfants")
    print()

    print("DÉDUCTIONS MENSUELLES:")
    ded = employee_result['deductions']
    print(f"  • CNSS salarié: {ded['cnss_salarial_monthly']:.2f} DT")
    print(f"  • IRPP: {ded['irpp_monthly']:.2f} DT")
    print(f"  • Retenue à la source: {ded['withholding_monthly']:.2f} DT")
    print()

    print("RÉSULTATS:")
    print(f"  • Salaire net mensuel: {employee_result['net_monthly']:.2f} DT")
    print(f"  • Coût employeur mensuel: {employee_result['employer_cost_monthly']:.2f} DT")
    print()

    # Calculate for freelancer example
    print("2️⃣ TRAVAILLEUR INDÉPENDANT (FREELANCE)")
    print("-" * 40)
    freelancer_result = calculate_freelancer_taxes(EXAMPLE_FREELANCER, rates)

    print(f"Freelancer: {freelancer_result['freelancer']['name']}")
    print(f"Revenus mensuels déclarés: {freelancer_result['revenue_monthly']:.2f} DT")
    print(f"Statut: {freelancer_result['freelancer']['marital_status']} avec {freelancer_result['freelancer']['children']} enfants")
    print(f"Activité: {freelancer_result['freelancer']['activity']}")
    print()

    print("DÉDUCTIONS MENSUELLES:")
    ded_f = freelancer_result['deductions']
    print(f"  • CNSS indépendant: {ded_f['cnss_monthly']:.2f} DT ({freelancer_result['tax_breakdown']['cnss_rate']:.1%})")
    print(f"  • IRPP: {ded_f['irpp_monthly']:.2f} DT")
    print(f"  • Frais professionnels (forfait): {ded_f['frais_professionnels']/12:.2f} DT/mois")
    print()

    print("RÉSULTATS:")
    print(f"  • Revenus nets mensuels: {freelancer_result['net_monthly']:.2f} DT")
    print()

    print("ANALYSE ANNUELLE:")
    tb_f = freelancer_result['tax_breakdown']
    print(f"  • IRPP annuel: {tb_f['irpp_annual']:.2f} DT")
    print(f"  • Taux effectif IRPP: {tb_f['effective_irpp_rate']:.1%}")
    print(f"  • Revenus imposables: {tb_f['taxable_income']:.2f} DT")

if __name__ == "__main__":
    main()
