import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "output" / "sample_output.json"

RAW_HOSPITALS = [
    {"name": "Riverside General", "capacity": 620, "demand": 520, "wait50": 118, "wait90": 210, "volume": 340},
    {"name": "Lakeshore Regional", "capacity": 540, "demand": 610, "wait50": 165, "wait90": 305, "volume": 290},
    {"name": "North Valley Health Ctr", "capacity": 410, "demand": 590, "wait50": 205, "wait90": 410, "volume": 180},
    {"name": "Cedar Grove Hospital", "capacity": 700, "demand": 460, "wait50": 95, "wait90": 160, "volume": 400},
    {"name": "Fraser Point Medical", "capacity": 480, "demand": 470, "wait50": 140, "wait90": 235, "volume": 250},
    {"name": "Union Bay Regional", "capacity": 350, "demand": 520, "wait50": 240, "wait90": 470, "volume": 150},
    {"name": "St. Alban's Surgical Ctr", "capacity": 600, "demand": 600, "wait50": 130, "wait90": 225, "volume": 330},
    {"name": "Harborview Clinic", "capacity": 460, "demand": 340, "wait50": 88, "wait90": 145, "volume": 210},
    {"name": "Pinehollow District", "capacity": 330, "demand": 400, "wait50": 205, "wait90": 320, "volume": 130},
    {"name": "Kettleford Hospital", "capacity": 560, "demand": 530, "wait50": 205, "wait90": 460, "volume": 300},
    {"name": "Marlbank General", "capacity": 500, "demand": 380, "wait50": 100, "wait90": 175, "volume": 260},
    {"name": "Silver Creek Regional", "capacity": 640, "demand": 560, "wait50": 108, "wait90": 190, "volume": 360},
    {"name": "Dunmore Community", "capacity": 380, "demand": 300, "wait50": 118, "wait90": 200, "volume": 160},
    {"name": "Elmsworth Medical Ctr", "capacity": 450, "demand": 610, "wait50": 260, "wait90": 380, "volume": 220},
    {"name": "Thornbury General", "capacity": 300, "demand": 340, "wait50": 175, "wait90": 300, "volume": 110},
    {"name": "Oakhaven Surgical Inst.", "capacity": 690, "demand": 640, "wait50": 150, "wait90": 250, "volume": 410},
]


def fit_linear(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    b = num / den
    a = my - b * mx
    return {"a": a, "b": b}


def median(values):
    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2


def build_payload():
    hospitals = []
    for raw in RAW_HOSPITALS:
        hospitals.append({
            "name": raw["name"],
            "capacity": raw["capacity"],
            "demand": raw["demand"],
            "wait50": raw["wait50"],
            "wait90": raw["wait90"],
            "volume": raw["volume"],
        })

    for hospital in hospitals:
        hospital["utilization"] = hospital["demand"] / hospital["capacity"]

    util = [hospital["utilization"] for hospital in hospitals]
    fit50 = fit_linear(util, [hospital["wait50"] for hospital in hospitals])
    fit90 = fit_linear(util, [hospital["wait90"] for hospital in hospitals])

    for hospital in hospitals:
        hospital["expected50"] = fit50["a"] + fit50["b"] * hospital["utilization"]
        hospital["expected90"] = fit90["a"] + fit90["b"] * hospital["utilization"]
        hospital["resid50"] = hospital["wait50"] - hospital["expected50"]
        hospital["resid90"] = hospital["wait90"] - hospital["expected90"]

    med_capacity = median([hospital["capacity"] for hospital in hospitals])
    med_demand = median([hospital["demand"] for hospital in hospitals])

    sorted_resid90 = sorted([hospital["resid90"] for hospital in hospitals])
    q3_idx = math.floor(len(sorted_resid90) * 0.75)
    q3_90 = sorted_resid90[q3_idx]
    max_90 = max(sorted_resid90)

    max_abs_resid = max(abs(hospital["resid50"]) for hospital in hospitals)
    for hospital in hospitals:
        flagged = hospital["resid90"] >= q3_90
        hospital["flagged"] = flagged
        if flagged:
            span = max(1, max_90 - q3_90)
            hospital["flagIntensity"] = max(0.15, min(1, (hospital["resid90"] - q3_90) / span))
        else:
            hospital["flagIntensity"] = 0

        t = max(-1, min(1, hospital["resid50"] / max_abs_resid))
        if t <= 0:
            hospital["color"] = "#2F8F76"
        else:
            hospital["color"] = "#C1443C"

    chart = {
        "width": 780,
        "height": 620,
        "margin": {"top": 30, "right": 30, "bottom": 55, "left": 65},
        "capExtent": [280, 730],
        "demExtent": [270, 660],
        "volExtent": [min(h["volume"] for h in hospitals), max(h["volume"] for h in hospitals)],
    }
    chart["plotWidth"] = chart["width"] - chart["margin"]["left"] - chart["margin"]["right"]
    chart["plotHeight"] = chart["height"] - chart["margin"]["top"] - chart["margin"]["bottom"]

    def sx(value):
        return chart["margin"]["left"] + (value - chart["capExtent"][0]) / (chart["capExtent"][1] - chart["capExtent"][0]) * chart["plotWidth"]

    def sy(value):
        return chart["margin"]["top"] + chart["plotHeight"] - (value - chart["demExtent"][0]) / (chart["demExtent"][1] - chart["demExtent"][0]) * chart["plotHeight"]

    def r_scale(value):
        t = (value - chart["volExtent"][0]) / (chart["volExtent"][1] - chart["volExtent"][0])
        return 7 + t * 13

    for hospital in hospitals:
        hospital["cx"] = sx(hospital["capacity"])
        hospital["cy"] = sy(hospital["demand"])
        hospital["radius"] = r_scale(hospital["volume"])
        hospital["zone"] = "z4"
        if hospital["capacity"] > med_capacity and hospital["demand"] < med_demand:
            hospital["zone"] = "z1"
        elif hospital["capacity"] > med_capacity and hospital["demand"] > med_demand:
            hospital["zone"] = "z2"
        elif hospital["capacity"] < med_capacity and hospital["demand"] < med_demand:
            hospital["zone"] = "z3"
        hospital["zoneLabel"] = {
            "z1": "Has slack",
            "z2": "Pressure cooker",
            "z3": "Low-capacity equilibrium",
            "z4": "Structural bottleneck",
        }[hospital["zone"]]

    return {
        "meta": {
            "title": "CanRoute — Capacity/Demand Diagnostic v3",
            "chart": chart,
        },
        "summary": {
            "hospitalsShown": len(hospitals),
            "medianCapacity": med_capacity,
            "medianDemand": med_demand,
            "flaggedCount": sum(1 for hospital in hospitals if hospital["flagged"]),
            "bottleneckCount": sum(1 for hospital in hospitals if hospital["capacity"] < med_capacity and hospital["demand"] > med_demand),
        },
        "hospitals": hospitals,
    }


def main():
    payload = build_payload()
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
