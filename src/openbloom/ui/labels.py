LABELS = {
    "revenue": "Revenue",
    "gross_profit": "Gross profit",
    "operating_income": "Operating income",
    "net_income": "Net income",
    "operating_cash_flow": "Operating cash flow",
    "capex": "Capex",
    "free_cash_flow": "Free cash flow",
    "gross_margin_pct": "Gross margin",
    "operating_margin_pct": "Operating margin",
    "net_margin_pct": "Net margin",
    "fcf_margin_pct": "FCF margin",
}

METRIC_LABELS = {
    "revenue_growth_pct": "Revenue growth (%)",
    "gross_margin_pct": "Gross margin (%)",
    "operating_margin_pct": "Operating margin (%)",
    "net_margin_pct": "Net margin (%)",
    "fcf_margin_pct": "FCF margin (%)",
    "roe_pct": "ROE (%)",
    "liabilities_to_equity": "Liabilities / equity (x)",
}

FORMULAS = {
    "revenue_growth_pct": "(revenue - previous year revenue) / previous year revenue x 100. Only if the previous row is about 1 year earlier and positive.",
    "gross_margin_pct": "gross_profit / revenue x 100",
    "operating_margin_pct": "operating_income / revenue x 100",
    "net_margin_pct": "net_income / revenue x 100",
    "free_cash_flow": "operating_cash_flow - capex",
    "fcf_margin_pct": "free_cash_flow / revenue x 100",
    "roe_pct": "net_income / equity x 100 (distorted when equity is small, e.g. after buybacks)",
    "liabilities_to_equity": "total_liabilities / equity",
}