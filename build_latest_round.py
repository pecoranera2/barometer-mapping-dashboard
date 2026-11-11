# Builds data/latest_round.csv (Latest round page) from inputs/Barometers_codebook.xlsx.
import csv
import os

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "inputs", "Barometers_codebook.xlsx")
OUT = os.path.join(HERE, "data", "latest_round.csv")

# codebook column -> barometer name used by the app
COLUMNS = {
    "Arab 2024": "Arab Barometer 2024",
    "Latino 2024": "Latinobarometer 2024",
    "Afro 2023": "Afro Barometer 2023",
    "Asian 2023": "Asian Barometer 2023",
    "Euro 2024": "Eurobarometer 2024 (Special)",
}
CLUSTERS = {"Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"}
NOT_AVAILABLE = {"", "-", "not available", "not created"}
# female and male come from the same question, shown as one row
MERGE = {"female": "Gender", "male": "Gender"}
# typos in the codebook labels, corrected for display
FIX = {
    "Arrival of inmigrants benefitial": "Arrival of immigrants beneficial",
    "Free to apart in protests": "Free to take part in protests",
    "Did you voted in the national election": "Did you vote in the national election",
    "Women has right to land": "Women have right to land",
    "Men decides how to spend money": "Men decide how to spend money",
    "A lot satisfaction with democracy": "A lot of satisfaction with democracy",
    "No fear crime in home": "No fear of crime in home",
}


def code_of(cell):
    """First line of the cell is the code; text after a colon is the question."""
    if cell is None:
        return ""
    first = str(cell).strip().split("\n")[0].strip()
    if first.lower() in NOT_AVAILABLE:
        return ""
    return first.split(":")[0].strip()


ws = openpyxl.load_workbook(SRC, data_only=True)["Codebook"]
rows = list(ws.iter_rows(values_only=True))
header = [str(h).strip() if h else "" for h in rows[0]]
col_idx = {header.index(k): v for k, v in COLUMNS.items()}

out, seen, cluster = [], set(), None
for r in rows[1:]:
    name = str(r[0]).strip() if r[0] else ""
    if name in CLUSTERS and all(v is None for v in r[1:]):
        cluster = name
        continue
    if not name or cluster is None:
        continue  # blank rows; the Weights block has no cluster
    if name == "Weights":
        cluster = None
        continue
    label = MERGE.get(name) or str(r[1] or name).strip()
    label = label[0].upper() + label[1:]
    label = FIX.get(label, label)
    if label in seen:
        continue
    seen.add(label)
    for i, bar in col_idx.items():
        code = code_of(r[i])
        out.append({"variable": label, "barometer": bar, "code": code,
                    "available": "1" if code else "0", "chunk": cluster})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["variable", "barometer", "code", "available", "chunk"])
    w.writeheader()
    w.writerows(out)
print(f"{len(seen)} variables written to {OUT}")
