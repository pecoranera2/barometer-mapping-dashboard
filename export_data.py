import openpyxl, csv, re

SRC = r"C:\Users\pecor\OneDrive\WB 2026\Mapping\Map of Variables 09 04 2026.xlsx"
OUT = r"C:\Users\pecor\OneDrive\WB 2026\Mapping\Visuals\data"

CLUSTER_HEADERS = {"Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"}
CLUSTER_ORDER = ["Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"]

# Best-effort classification of the 51 "Latest round" concepts into the 5 mapping
# clusters, for visual grouping only (not an authoritative recoding of the clusters
# themselves - several of these variables aren't in any cluster tab at all).
LATEST_ROUND_CLUSTER = {
    "Gender": "Socioeconomic",
    "Age": "Socioeconomic",
    "Highest education achieved: Secondary": "Socioeconomic",
    "Married": "Socioeconomic",
    "Household size": "Socioeconomic",
    "Religion": "Socioeconomic",
    "Religious": "Socioeconomic",
    "Ethnicity": "Socioeconomic",
    "Household head": "Socioeconomic",
    "Parents education": "Socioeconomic",
    "Do you have children": "Socioeconomic",
    "Children in household": "Socioeconomic",
    "Employed": "Employment",
    "Self-employed/Salaried": "Employment",
    "Full time or part time": "Employment",
    "Job sector (priv and public)": "Employment",
    "Position at work (occupation)": "Employment",
    "Bank Account": "Access",
    "Savings": "Access",
    "Internet user": "Access",
    "Electricity": "Access",
    "Water": "Access",
    "Food insecure": "Access",
    "Urban": "Access",
    "Poor neighborhood": "Access",
    "Owns a house": "Access",
    "Victim of a crime": "Access",
    "Mobile phone": "Access",
    "Internet connection at home": "Access",
    "Safety of neighborhood": "Access",
    "Men make better political leaders": "Gender and social norms",
    "University more important for men": "Gender and social norms",
    "Female head responsible for child studies": "Gender and social norms",
    "Felt discriminated against": "Gender and social norms",
    "How often: adults use physical discipline with children": "Gender and social norms",
    "Children belong more to mother’s or father’s side": "Gender and social norms",
    "Who decides how money is used": "Gender and social norms",
    "Men and women should have equal work opportunities.": "Gender and social norms",
    "Neighbors": "Gender and social norms",
    "It is preferable woman in the house and man in his work": "Gender and social norms",
    "If one could have only one child, it is more preferable to have a boy than a girl": "Gender and social norms",
    "\"Gender issues / women's rights\" as a volunteered answer to the open-ended \"most important problems facing this country\" question (response code 28)": "Gender and social norms",
    "Interested in Politics": "Institutional",
    "Freedom of speech": "Institutional",
    "Freedom to participate in protests": "Institutional",
    "Freedom of religion": "Institutional",
    "Inequality is a problem": "Institutional",
    "Democracy always preferable": "Institutional",
    "Life satisfaction": "Institutional",
    "Support for democracy": "Institutional",
    "Freedom of political participation": "Institutional",
}

# Shorter display labels for the charts, keyed by the exact original cell text -
# classification (LATEST_ROUND_CLUSTER etc.) still keys off the ORIGINAL label,
# this is applied only at the point of writing to CSV for display.
RELABEL = {
    "Job sector (priv and public)": "Job sector (private and public)",
    "\"Gender issues / women's rights\" as a volunteered answer to the open-ended \"most important problems facing this country\" question (response code 28)":
        "Most important problems facing the country: Gender issues/women's rights",
    # source cell itself ends mid-sentence ("...campaign that…"); replaced with the
    # accurate short label taken straight from the raw .dta variable label (qb5_3/qc5_3)
    "You have joined an association or campaign that…":
        "Actions against discrimination: joined association/campaign",
    # source cell contains a literal replacement character (U+FFFD) where a dash was
    # presumably meant - garbled in the source workbook itself, not by this export
    "Most important problems � 1 st response: gender issues":
        "Most important problems (1st response): gender issues",
}

def clean_label(label):
    # colleague's asterisks on some ARAB/LATINO/AFRO cluster rows aren't needed in the visuals
    return str(label).replace("*", "").strip()

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)

# ---- 1. Latest round ----
ws = wb["Latest round"]
rows = list(ws.iter_rows(values_only=True))
header = rows[0]
barometers = [h for h in header[1:] if h]  # drop trailing None
unmatched = set()
dropped = []
with open(f"{OUT}/latest_round.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["variable", "barometer", "code", "available", "chunk"])
    for row in rows[1:]:
        label = row[0]
        if label is None:
            continue
        label = clean_label(label)
        if label.lower().startswith("numero de paises"):
            continue
        chunk = LATEST_ROUND_CLUSTER.get(label)
        if chunk is None:
            unmatched.add(label)
            chunk = "Other"
        label = RELABEL.get(label, label)
        # drop concepts not available in any barometer's latest round
        if all(row[i + 1] in (None, "") for i in range(len(barometers))):
            dropped.append(("Latest round", label))
            continue
        for i, bar in enumerate(barometers):
            code = row[i + 1]
            w.writerow([label, bar, code if code is not None else "", "1" if code not in (None, "") else "0", chunk])
if unmatched:
    print("UNMATCHED (classified as 'Other'):", unmatched)

# country counts row, for subtitle annotation
n_row = [r for r in rows[1:] if r[0] and str(r[0]).strip().lower().startswith("numero de paises")]
with open(f"{OUT}/latest_round_counts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["barometer", "n_countries"])
    if n_row:
        r = n_row[0]
        for i, bar in enumerate(barometers):
            w.writerow([bar, r[i + 1]])

# column labels for Arab/Latino/Afro (newest first, as in the workbook): year + wave/round
PERIOD_LABELS = {
    "Clusters ARAB": ["2024 (Wave 8)", "2021 (Wave 6)", "2017 (Wave 4)", "2014 (Wave 3)"],
    "Clusters LATINO": ["Round 2024", "Round 2020", "Round 2017", "Round 2015"],
    "Clusters AFRO": ["2023 (Wave 9)", "2022 (Wave 8)", "2019/20 (Wave 7)", "2016 (Wave 6)", "2013 (Wave 5)"],
}


def export_cluster_tab(sheet_name, out_name):
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    cols = PERIOD_LABELS.get(sheet_name) or [str(h).strip() for h in header[1:] if h is not None]
    seen_labels = set()
    with open(f"{OUT}/{out_name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "variable", "period", "code", "available"])
        current_cluster = None
        for row in rows[1:]:
            label = row[0]
            if label is None:
                continue
            label = clean_label(label)
            if label in CLUSTER_HEADERS:
                current_cluster = label
                continue
            label = RELABEL.get(label, label)
            # a few source tabs (e.g. Clusters AFRO) repeat the same label twice with
            # different codes - a source data-entry issue flagged to the mapping owner;
            # keep only the first occurrence for the visual
            if label in seen_labels:
                continue
            seen_labels.add(label)
            # drop concepts with no variable in any period of this barometer
            if all((row[i + 1] if i + 1 < len(row) else None) in (None, "") for i in range(len(cols))):
                dropped.append((sheet_name, label))
                continue
            for i, col in enumerate(cols):
                code = row[i + 1] if i + 1 < len(row) else None
                w.writerow([current_cluster, label, col, code if code is not None else "", "1" if code not in (None, "") else "0"])
    return out_name

# ---- 2. EURO CLUSTERS ----
export_cluster_tab("Clusters Euro", "euro_clusters")

# ---- 3. AB CLUSTERS (Asian Barometer) ----
export_cluster_tab("Clusters AB", "ab_clusters")

# ---- 4. Clusters ARAB / LATINO / AFRO ----
export_cluster_tab("Clusters ARAB", "arab_clusters")
export_cluster_tab("Clusters LATINO", "latino_clusters")
export_cluster_tab("Clusters AFRO", "afro_clusters")

print("dropped:", dropped)
print("done")

# ---- override workbook country counts with the published latest-round counts (data/countries.csv) ----
import pandas as pd
_c = pd.read_csv(f"{OUT}/countries.csv")
_pub = _c[_c["latest"] == 1].groupby("barometer")["country"].nunique()
_short = {"Arab Barometer 2024": "Arab Barometer", "Latinobarometer 2024": "Latinobarometro",
          "Afro Barometer 2023": "Afrobarometer", "Asian Barometer 2023": "Asian Barometer",
          "Eurobarometer 2025 (Standard)": "Eurobarometer"}
_cnt = pd.read_csv(f"{OUT}/latest_round_counts.csv")
_cnt["n_countries"] = _cnt["barometer"].map(lambda b: int(_pub[_short[b]]))
_cnt.to_csv(f"{OUT}/latest_round_counts.csv", index=False)
print("counts set to published:", dict(zip(_cnt.barometer, _cnt.n_countries)))
