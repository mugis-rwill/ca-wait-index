"""
compute.py — turns a cleaned (name, capacity, demand, wait50, wait90, volume)
table into the fully computed, frontend-ready structure: regression-based
expected wait, residuals, tail flags, quadrant zone, color, and precomputed
chart pixel geometry. The frontend should only render this — it should never
recompute statistics itself, so the math lives in exactly one place.
"""

import statistics as stats


def fit_linear(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    b = num / den if den else 0.0
    a = my - b * mx
    return a, b


def lerp_color(c1, c2, t):
    p1 = [int(c1[i:i+2], 16) for i in (0, 2, 4)]
    p2 = [int(c2[i:i+2], 16) for i in (0, 2, 4)]
    rgb = [round(v + (p2[i] - v) * t) for i, v in enumerate(p1)]
    return "#%02X%02X%02X" % tuple(rgb)


def resid_color(r, max_abs_resid):
    if max_abs_resid == 0:
        return "#E4E0CE"
    t = max(-1.0, min(1.0, r / max_abs_resid))
    if t <= 0:
        return lerp_color("2F8F76", "E4E0CE", t + 1)
    return lerp_color("E4E0CE", "C1443C", t)


CHART_DEFAULTS = {
    "width": 780, "height": 620,
    "margin": {"top": 30, "right": 30, "bottom": 55, "left": 65},
}


def compute_year(records: list[dict], title: str) -> dict:
    """
    records: list of dicts with name, capacity, demand, wait50, wait90, volume
    (already cleaned — no NaNs). Returns the full frontend-ready payload for
    one year.
    """
    records = [r for r in records if r["capacity"] and r["demand"] is not None
               and r["wait50"] is not None and r["wait90"] is not None]
    if not records:
        return None

    for r in records:
        r["utilization"] = r["demand"] / r["capacity"]

    util = [r["utilization"] for r in records]
    a50, b50 = fit_linear(util, [r["wait50"] for r in records])
    a90, b90 = fit_linear(util, [r["wait90"] for r in records])

    for r in records:
        r["expected50"] = a50 + b50 * r["utilization"]
        r["expected90"] = a90 + b90 * r["utilization"]
        r["resid50"] = r["wait50"] - r["expected50"]
        r["resid90"] = r["wait90"] - r["expected90"]

    resid90_sorted = sorted(r["resid90"] for r in records)
    q3_idx = int(len(resid90_sorted) * 0.75)
    q3_90 = resid90_sorted[q3_idx]
    max90 = max(resid90_sorted)
    for r in records:
        r["flagged"] = r["resid90"] >= q3_90
        r["flagIntensity"] = (
            max(0.15, min(1.0, (r["resid90"] - q3_90) / max(1.0, (max90 - q3_90))))
            if r["flagged"] else 0.0
        )

    max_abs_resid = max(abs(r["resid50"]) for r in records)
    for r in records:
        r["color"] = resid_color(r["resid50"], max_abs_resid)

    med_capacity = stats.median(r["capacity"] for r in records)
    med_demand = stats.median(r["demand"] for r in records)
    zone_labels = {
        (True, True): ("z1", "Structural bottleneck"),   # low capacity, high demand
        (False, True): ("z2", "Pressure cooker"),         # high capacity, high demand
        (True, False): ("z3", "Low-capacity equilibrium"),# low capacity, low demand
        (False, False): ("z4", "Has slack"),               # high capacity, low demand
    }
    for r in records:
        key = (r["capacity"] < med_capacity, r["demand"] > med_demand)
        r["zone"], r["zoneLabel"] = zone_labels[key]

    # ---- chart geometry ----
    cap_vals = [r["capacity"] for r in records]
    dem_vals = [r["demand"] for r in records]
    vol_vals = [r["volume"] for r in records]
    cap_pad = (max(cap_vals) - min(cap_vals)) * 0.1 or 1
    dem_pad = (max(dem_vals) - min(dem_vals)) * 0.1 or 1
    cap_extent = [min(cap_vals) - cap_pad, max(cap_vals) + cap_pad]
    dem_extent = [min(dem_vals) - dem_pad, max(dem_vals) + dem_pad]
    vol_extent = [min(vol_vals), max(vol_vals)]

    margin = CHART_DEFAULTS["margin"]
    width, height = CHART_DEFAULTS["width"], CHART_DEFAULTS["height"]
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    def sx(v):
        return margin["left"] + (v - cap_extent[0]) / (cap_extent[1] - cap_extent[0]) * plot_w

    def sy(v):
        return margin["top"] + plot_h - (v - dem_extent[0]) / (dem_extent[1] - dem_extent[0]) * plot_h

    def r_scale(v):
        t = (v - vol_extent[0]) / (vol_extent[1] - vol_extent[0]) if vol_extent[1] > vol_extent[0] else 0.5
        return 7 + t * 13

    for r in records:
        r["cx"] = sx(r["capacity"])
        r["cy"] = sy(r["demand"])
        r["radius"] = r_scale(r["volume"])

    flagged_count = sum(1 for r in records if r["flagged"])
    bottleneck_count = sum(1 for r in records if r["zone"] == "z1")

    return {
        "meta": {
            "title": title,
            "chart": {
                "width": width, "height": height, "margin": margin,
                "capExtent": cap_extent, "demExtent": dem_extent, "volExtent": vol_extent,
                "plotWidth": plot_w, "plotHeight": plot_h,
            },
            "demand_is_placeholder": False,
            "dataSource": "BC Ministry of Health — Surgical Wait Times (quarterly), aggregated to fiscal year",
        },
        "summary": {
            "hospitalsShown": len(records),
            "medianCapacity": med_capacity,
            "medianDemand": med_demand,
            "flaggedCount": flagged_count,
            "bottleneckCount": bottleneck_count,
        },
        "hospitals": records,
    }
