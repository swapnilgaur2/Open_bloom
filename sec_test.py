import pandas as pd
from src.openbloom.sec_client import get_company_facts

facts = get_company_facts("0000320193")["facts"]["us-gaap"]


def annual_values(concept):
    rows = facts[concept]["units"]["USD"]
    df = pd.DataFrame(rows)
    df = df[df["form"] == "10-K"].copy()
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df = df[(df["end"] - df["start"]).dt.days.between(350, 380)]
    df = df.sort_values(["end", "filed"]).drop_duplicates("end", keep="last")
    return df[["end", "val", "accn", "filed"]].rename(columns={"val": concept})


revenue = annual_values("RevenueFromContractWithCustomerExcludingAssessedTax")
operating_income = annual_values("OperatingIncomeLoss")

print("\n--- REVENUE ---")
print(revenue.tail(6).to_string(index=False))
print("\n--- OPERATING INCOME ---")
print(operating_income.tail(6).to_string(index=False))