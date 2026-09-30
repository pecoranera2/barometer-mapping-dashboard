"""Builds data/countries.csv: which countries each barometer covered in each round.
Arab/Latino/Afro lists come from the barometers' published documentation (hardcoded below);
Asian Barometer and Eurobarometer are read from the raw .dta files on Natalia's OneDrive."""
import csv, glob, os
import pandas as pd
import pyreadstat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "countries.csv")
WB = r"C:\Users\pecor\OneDrive\WB 2026"

ISO3 = {
 "Algeria":"DZA","Angola":"AGO","Bahrain":"BHR","Benin":"BEN","Botswana":"BWA","Burkina Faso":"BFA","Burundi":"BDI",
 "Cameroon":"CMR","Cabo Verde":"CPV","Congo-Brazzaville":"COG","Côte d'Ivoire":"CIV","Egypt":"EGY","eSwatini":"SWZ",
 "Ethiopia":"ETH","Gabon":"GAB","Gambia":"GMB","Ghana":"GHA","Guinea":"GIN","Iraq":"IRQ","Jordan":"JOR","Kenya":"KEN",
 "Kuwait":"KWT","Lebanon":"LBN","Lesotho":"LSO","Liberia":"LBR","Libya":"LBY","Madagascar":"MDG","Malawi":"MWI",
 "Mali":"MLI","Mauritania":"MRT","Mauritius":"MUS","Morocco":"MAR","Mozambique":"MOZ","Namibia":"NAM","Niger":"NER",
 "Nigeria":"NGA","Palestine":"PSE","Qatar":"QAT","Saudi Arabia":"SAU","São Tomé and Príncipe":"STP","Senegal":"SEN",
 "Seychelles":"SYC","Sierra Leone":"SLE","South Africa":"ZAF","Sudan":"SDN","Syria":"SYR","Tanzania":"TZA","Togo":"TGO",
 "Tunisia":"TUN","Uganda":"UGA","Yemen":"YEM","Zambia":"ZMB","Zimbabwe":"ZWE",
 "Argentina":"ARG","Bolivia":"BOL","Brazil":"BRA","Chile":"CHL","Colombia":"COL","Costa Rica":"CRI","Dominican Republic":"DOM",
 "Ecuador":"ECU","El Salvador":"SLV","Guatemala":"GTM","Honduras":"HND","Mexico":"MEX","Nicaragua":"NIC","Panama":"PAN",
 "Paraguay":"PRY","Peru":"PER","Uruguay":"URY","Venezuela":"VEN",
 "Australia":"AUS","Cambodia":"KHM","China":"CHN","Hong Kong":"HKG","India":"IND","Indonesia":"IDN","Japan":"JPN",
 "South Korea":"KOR","Malaysia":"MYS","Mongolia":"MNG","Myanmar":"MMR","Philippines":"PHL","Singapore":"SGP","Taiwan":"TWN",
 "Thailand":"THA","Vietnam":"VNM",
}
EB_ISO2 = {"AL":("Albania","ALB"),"AT":("Austria","AUT"),"BA":("Bosnia and Herzegovina","BIH"),"BE":("Belgium","BEL"),
 "BG":("Bulgaria","BGR"),"CY":("Cyprus","CYP"),"CY-TCC":("Cyprus","CYP"),"CZ":("Czechia","CZE"),"DE-E":("Germany","DEU"),
 "DE-W":("Germany","DEU"),"DK":("Denmark","DNK"),"EE":("Estonia","EST"),"ES":("Spain","ESP"),"FI":("Finland","FIN"),
 "FR":("France","FRA"),"GB":("United Kingdom","GBR"),"GB-GBN":("United Kingdom","GBR"),"GB-NIR":("United Kingdom","GBR"),
 "GE":("Georgia","GEO"),"GR":("Greece","GRC"),"HR":("Croatia","HRV"),"HU":("Hungary","HUN"),"IE":("Ireland","IRL"),
 "IT":("Italy","ITA"),"LT":("Lithuania","LTU"),"LU":("Luxembourg","LUX"),"LV":("Latvia","LVA"),"MD":("Moldova","MDA"),
 "ME":("Montenegro","MNE"),"MK":("North Macedonia","MKD"),"MT":("Malta","MLT"),"NL":("Netherlands","NLD"),"PL":("Poland","POL"),
 "PT":("Portugal","PRT"),"RO":("Romania","ROU"),"RS":("Serbia","SRB"),"RS-KM":("Serbia","SRB"),"SE":("Sweden","SWE"),
 "SI":("Slovenia","SVN"),"SK":("Slovakia","SVK"),"TR":("Turkey","TUR")}

rows = []  # barometer, round, year, period, country, iso3, latest


def add(bar, rnd, year, period, names, latest=False):
    for n in sorted(set(names)):
        rows.append((bar, rnd, year, period, n, ISO3[n], int(latest)))


# ---- Arab Barometer (arabbarometer.org/survey-data/data-downloads) ----
AR = {
 "III": ("2012-2014", "2012-2016", ["Algeria","Egypt","Iraq","Jordan","Kuwait","Lebanon","Libya","Morocco","Palestine","Sudan","Tunisia","Yemen"]),
 "IV":  ("2016-2017", "2016-2019", ["Algeria","Egypt","Jordan","Lebanon","Morocco","Palestine","Tunisia","Qatar"]),
 "V":   ("2018-2019", "2016-2019", ["Algeria","Egypt","Iraq","Jordan","Kuwait","Lebanon","Libya","Morocco","Palestine","Sudan","Tunisia","Yemen"]),
 "VI":  ("2020-2021", "2020-2022", ["Algeria","Jordan","Lebanon","Libya","Morocco","Tunisia","Iraq"]),
 "VII": ("2021-2022", "2020-2022", ["Algeria","Egypt","Iraq","Jordan","Kuwait","Lebanon","Libya","Mauritania","Morocco","Palestine","Sudan","Tunisia"]),
 "VIII": ("2023-2024", "2023-2025", ["Iraq","Jordan","Kuwait","Lebanon","Mauritania","Morocco","Palestine","Tunisia"]),
 # Wave IX: only the countries already fielded (Mauritania planned, not yet surveyed)
 "IX":  ("2025-2026", "2023-2025", ["Egypt","Iraq","Jordan","Lebanon","Morocco","Palestine","Syria","Tunisia"]),
}
for r, (y, p, c) in AR.items():
    add("Arab Barometer", f"Wave {r}", y, p, c, latest=(r == "VIII"))

# ---- Latinobarometro (latinobarometro.org/latinobarometro-YYYY) ----
L18 = ["Argentina","Bolivia","Brazil","Chile","Colombia","Costa Rica","Dominican Republic","Ecuador","El Salvador","Guatemala",
       "Honduras","Mexico","Nicaragua","Panama","Paraguay","Peru","Uruguay","Venezuela"]
L17 = [c for c in L18 if c != "Nicaragua"]   # 2023 report: Nicaragua not surveyed
LAT = [("2013","2012-2016",L18),("2015","2012-2016",L18),("2016","2012-2016",L18),("2017","2016-2019",L18),
       ("2018","2016-2019",L18),("2020","2020-2022",L18),("2023","2023-2025",L17),("2024","2023-2025",L17)]
for y, p, c in LAT:
    add("Latinobarometro", y, y, p, c, latest=(y == "2024"))

# ---- Afrobarometer (World Bank Microdata Library / DataFirst merged-round catalog) ----
R5 = ["Algeria","Benin","Botswana","Burkina Faso","Burundi","Cameroon","Cabo Verde","Côte d'Ivoire","Egypt","Ghana","Guinea","Kenya",
      "Lesotho","Liberia","Madagascar","Malawi","Mali","Mauritius","Morocco","Mozambique","Namibia","Niger","Nigeria","Senegal",
      "Sierra Leone","South Africa","Sudan","eSwatini","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"]
R6 = ["Algeria","Benin","Botswana","Burkina Faso","Burundi","Cameroon","Cabo Verde","Côte d'Ivoire","Egypt","Gabon","Ghana","Guinea",
      "Kenya","Lesotho","Liberia","Madagascar","Malawi","Mali","Mauritius","Morocco","Mozambique","Namibia","Niger","Nigeria",
      "São Tomé and Príncipe","Senegal","Sierra Leone","South Africa","Sudan","eSwatini","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"]
R7 = ["Benin","Botswana","Burkina Faso","Cabo Verde","Cameroon","Côte d'Ivoire","eSwatini","Gabon","Gambia","Ghana","Guinea","Kenya",
      "Lesotho","Liberia","Madagascar","Malawi","Mali","Mauritius","Morocco","Mozambique","Namibia","Niger","Nigeria",
      "São Tomé and Príncipe","Senegal","Sierra Leone","South Africa","Sudan","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"]
R8 = ["Angola","Benin","Botswana","Burkina Faso","Cabo Verde","Cameroon","Côte d'Ivoire","eSwatini","Ethiopia","Gabon","Gambia","Ghana",
      "Guinea","Kenya","Lesotho","Liberia","Malawi","Mali","Mauritius","Morocco","Mozambique","Namibia","Niger","Nigeria","Senegal",
      "Sierra Leone","South Africa","Sudan","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"]
R9 = ["Angola","Benin","Botswana","Burkina Faso","Cabo Verde","Cameroon","Congo-Brazzaville","Côte d'Ivoire","eSwatini","Ethiopia",
      "Gabon","Gambia","Ghana","Guinea","Kenya","Lesotho","Liberia","Madagascar","Malawi","Mali","Mauritania","Mauritius","Morocco",
      "Mozambique","Namibia","Niger","Nigeria","São Tomé and Príncipe","Senegal","Seychelles","Sierra Leone","South Africa","Sudan",
      "Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"]
assert [len(x) for x in (R5, R6, R7, R8, R9)] == [34, 36, 34, 34, 39], [len(x) for x in (R5, R6, R7, R8, R9)]
for r, y, p, c in [("Round 5","2011-2013","2012-2016",R5), ("Round 6","2014-2015","2012-2016",R6),
                   ("Round 7","2016-2018","2016-2019",R7), ("Round 8","2019-2021","2020-2022",R8),
                   ("Round 9","2021-2023","2023-2025",R9)]:
    add("Afrobarometer", r, y, p, c, latest=(r == "Round 9"))

# ---- Asian Barometer (raw .dta) ----
AB_NAME = {"Korea": "South Korea", "Mainland China": "China"}


def ab_countries(path):
    df = pyreadstat.read_dta(path, usecols=["country"], apply_value_formats=True, formats_as_category=True)[0]
    return [AB_NAME.get(x, x) for x in df["country"].astype(str).unique()]


for w, y, p, f in [("Wave 3","2010-2012","2012","W3 data/ABS3 merge20250609.dta"),
                   ("Wave 4","2014-2016","2016","W4 data/W4_v15_merged20250609_release.dta"),
                   ("Wave 5","2018-2021","2021","W5 data/20230504_W5_merge_15.dta")]:
    add("Asian Barometer", w, y, p, ab_countries(os.path.join(WB, "Asian Barometer", f)))
W6 = {"Japan","Singapore","Vietnam","Malaysia","Australia","Thailand","Cambodia","Indonesia","South Korea","Mongolia","Philippines","Taiwan"}
assert len(glob.glob(os.path.join(WB, "Asian Barometer", "W6 data", "*.dta"))) == len(W6)
add("Asian Barometer", "Wave 6", "2021-2023", "2023", W6, latest=True)


# ---- Eurobarometer (raw .dta: isocntry) ----
def add_eb(rnd, year, period, path, latest=False):
    df = pyreadstat.read_dta(path, usecols=["isocntry"])[0]
    for n, i in sorted({EB_ISO2[c] for c in df["isocntry"].astype(str).unique()}):
        rows.append(("Eurobarometer", rnd, year, period, n, i, int(latest)))


EB = os.path.join(WB, "Eurobarometer")
for rnd, y, f in [("Special EB 83.4","2015","Special EB modules/ZA6595_v3-0-0.dta"),
                  ("Special EB 87.4","2017","Special EB modules/ZA6924_v2-0-0.dta"),
                  ("Special EB 91.4","2019","Special EB modules/ZA7575_v2-0-0.dta"),
                  ("Special EB 99.2","2023","Special EB modules/ZA7955_v1-0-0.dta"),
                  ("Special EB 100.3","2024","Special EB modules/ZA8840_v1-0-0.dta")]:
    add_eb(rnd, y, y, os.path.join(EB, f))
add_eb("Standard EB 104.1", "2025", "2025", os.path.join(EB, "Raw data/ZA9130_v1-0-0.dta"), latest=True)

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["barometer", "round", "year", "period", "country", "iso3", "latest"])
    w.writerows(rows)
d = pd.read_csv(OUT)
print(d.groupby(["barometer", "round"]).size().to_string())
print(d[d.latest == 1].groupby("barometer").size())
