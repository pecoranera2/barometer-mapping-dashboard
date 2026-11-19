import csv
import os
import re

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "inputs", "Barometers_codebook.xlsx")
OUT = os.path.join(HERE, "data", "latest_round.csv")

COLUMNS = {
    "Arab 2024": "Arab Barometer 2024",
    "Latino 2024": "Latinobarometer 2024",
    "Afro 2023": "Afro Barometer 2023",
    "Asian 2023": "Asian Barometer 2023",
    "Euro 2024": "Eurobarometer 2024 (Special)",
}
CLUSTERS = {"Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"}
NOT_AVAILABLE = {"", "-", "not available", "not created"}
MERGE = {"female": "Gender", "male": "Gender"}
# label typos
FIX = {
    "Arrival of inmigrants benefitial": "Arrival of immigrants beneficial",
    "Free to apart in protests": "Attended a demonstration or protest march",
    "Did you voted in the national election": "Did you vote in the national election",
    "Women has right to land": "Women have right to land",
    "Men decides how to spend money": "Men decide how to spend money",
    "A lot satisfaction with democracy": "A lot of satisfaction with democracy",
    "No fear crime in home": "No fear of crime in home",
}


OVERRIDE = {
    ("trust_pre", "Arab 2024"): "q201a_31b",
    ("trust_gov", "Arab 2024"): "q201a_5",
    ("voted", "Asian 2023"): "q33",
}


def code_of(cell):
    if cell is None:
        return ""
    first = str(cell).strip().split("\n")[0].strip()
    if first.lower() in NOT_AVAILABLE:
        return ""
    codes = []
    for tok in first.split(":")[0].split():
        if not re.fullmatch(r"[A-Za-z][\w.]*\d[\w.]*,?", tok):
            break
        codes.append(tok.rstrip(","))
    return ", ".join(codes) if codes else first.split(":")[0].strip()


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
        continue
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
        code = OVERRIDE.get((name, header[i])) or code_of(r[i])
        out.append({"variable": label, "barometer": bar, "code": code,
                    "available": "1" if code else "0", "chunk": cluster})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["variable", "barometer", "code", "available", "chunk"])
    w.writeheader()
    w.writerows(out)
print(f"{len(seen)} variables written to {OUT}")
