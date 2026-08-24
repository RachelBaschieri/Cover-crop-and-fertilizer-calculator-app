from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

NUTRIENTS = ["total_n", "dry_matter", "pan4", "pan10", "p2o5", "k2o", "ca", "mg", "s", "b", "cu", "fe", "mn", "zn"]

# Percent values are fresh-weight percentages except pan4/pan10, which are
# lb available N per 100 lb product on a fresh-weight basis.
MATERIALS: Dict[str, Dict[str, float | str]] = {
    "Blood meal (12.5-1.5-0.6)": {"category":"Organic fertilizer","total_n":12.5,"dry_matter":91,"pan4":7.5,"pan10":9.375,"p2o5":1.5,"k2o":0.6},
    "Bone meal (3-20-0.5)": {"category":"Organic fertilizer","total_n":3,"dry_matter":95,"pan4":0.5210526316,"pan10":0.9710526316,"p2o5":20,"k2o":0.5},
    "Chicken manure - dried (4-3-2)": {"category":"Organic fertilizer","total_n":4,"dry_matter":85,"pan4":1.6235294118,"pan10":2.2235294118,"p2o5":3,"k2o":2,"ca":7,"mg":1,"s":0.5},
    "Feather meal (granulated) (13-0-0)": {"category":"Organic fertilizer","total_n":13,"dry_matter":97,"pan4":7.8,"pan10":9.75,"p2o5":0,"k2o":0},
    "Fish meal (10-6-2)": {"category":"Organic fertilizer","total_n":10,"dry_matter":92,"pan4":6,"pan10":7.5,"p2o5":6,"k2o":2},
    "Meat and bone meal (7-8-0)": {"category":"Organic fertilizer","total_n":7,"dry_matter":93,"pan4":4.2,"pan10":5.25,"p2o5":8,"k2o":0},
    "Muriate of potash (KCl) (0-0-60)": {"category":"Organic fertilizer","total_n":0,"dry_matter":100,"pan4":0,"pan10":0,"p2o5":0,"k2o":60},
    "Soy meal (6.5-1.5-2.4)": {"category":"Organic fertilizer","total_n":6.5,"dry_matter":90,"pan4":3.9,"pan10":4.875,"p2o5":1.5,"k2o":2.4,"s":3},
    "Sulfate of potash (0-0-50)": {"category":"Organic fertilizer","total_n":0,"dry_matter":99,"pan4":0,"pan10":0,"p2o5":0,"k2o":50,"s":17},
    "Sulfate of potash magnesia (0-0-22)": {"category":"Organic fertilizer","total_n":0,"dry_matter":99,"pan4":0,"pan10":0,"p2o5":0,"k2o":22,"mg":10.8,"s":22},
    "Triple super phosphate (0-40-0)": {"category":"Synthetic fertilizer","total_n":0,"dry_matter":0,"pan4":0,"pan10":0,"p2o5":40,"k2o":0},
    "Urea (46-0-0)": {"category":"Synthetic fertilizer","total_n":46,"dry_matter":0,"pan4":46,"pan10":46,"p2o5":0,"k2o":0},
    "Composted manure (1.5-0.5-0.5)": {"category":"Compost","total_n":1.5,"dry_matter":60,"pan4":0.075,"pan10":0.15,"p2o5":0.5,"k2o":0.5,"ca":1.8},
}

for material in MATERIALS.values():
    for nutrient in NUTRIENTS:
        material.setdefault(nutrient, 0.0)

EQUIPMENT = {
    "none": {"implement_cost_hr":0,"width_ft":0,"speed_mph":0},
    "drill": {"implement_cost_hr":15.8372554192,"width_ft":10,"speed_mph":3},
    "hand held spin spreader": {"implement_cost_hr":0,"width_ft":0,"speed_mph":0},
    "drop spreader": {"implement_cost_hr":8.3097775610,"width_ft":8,"speed_mph":3},
    "tractor driven spin spreader": {"implement_cost_hr":6.7268472376,"width_ft":20,"speed_mph":4},
    "side dresser": {"implement_cost_hr":15.8372554192,"width_ft":10,"speed_mph":3},
    "manure spreader": {"implement_cost_hr":13.4536944752,"width_ft":10,"speed_mph":3},
    "rotary mow once": {"implement_cost_hr":5.52,"width_ft":6,"speed_mph":4},
    "flail mow once": {"implement_cost_hr":5.52,"width_ft":6,"speed_mph":4},
    "chisel plow once": {"implement_cost_hr":3.6601906673,"width_ft":8,"speed_mph":3},
    "moldboard plow once": {"implement_cost_hr":7.8584678899,"width_ft":6,"speed_mph":3},
    "disc once": {"implement_cost_hr":5.1772728324,"width_ft":12,"speed_mph":3},
}

# Workbook observations for cereal rye + common vetch. Linear interpolation
# reproduces the displayed workbook examples and keeps behavior transparent.
PAN_ANCHORS = [
    (0.0, 0.0, 0.0), (1.94, 8.403, 23.489), (2.32, 24.857, 36.11),
    (2.84, 31.65, 40.53), (3.0, 33.522, 41.89), (3.2, 35.862, 43.59),
]


def num(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def interpolate_pan(n_percent: float) -> tuple[float, float]:
    if n_percent <= 0:
        return 0.0, 0.0
    if n_percent >= PAN_ANCHORS[-1][0]:
        # Extend the final segment instead of silently capping.
        a, b = PAN_ANCHORS[-2], PAN_ANCHORS[-1]
    else:
        a, b = PAN_ANCHORS[0], PAN_ANCHORS[1]
        for left, right in zip(PAN_ANCHORS, PAN_ANCHORS[1:]):
            if left[0] <= n_percent <= right[0]:
                a, b = left, right
                break
    fraction = (n_percent - a[0]) / (b[0] - a[0])
    return (a[1] + fraction * (b[1] - a[1]), a[2] + fraction * (b[2] - a[2]))


def cover_crop_analysis(area_ft2: float, sample_lb: float, n_percent: float, dm_percent: float) -> dict:
    if area_ft2 <= 0:
        raise ValueError("Area sampled must be greater than zero.")
    fraction_acre = area_ft2 / 43560.0
    fresh_lb_ac = sample_lb / fraction_acre
    dry_lb_ac = fresh_lb_ac * dm_percent / 100.0
    total_n_lb_ac = dry_lb_ac * n_percent / 100.0
    pan4_pct, pan10_pct = interpolate_pan(n_percent)
    return {
        "fraction_acre": fraction_acre,
        "fresh_lb_ac": fresh_lb_ac,
        "dry_lb_ac": dry_lb_ac,
        "total_n_lb_ac": total_n_lb_ac,
        "pan4_percent": pan4_pct,
        "pan10_percent": pan10_pct,
        "pan4_lb_ac": total_n_lb_ac * pan4_pct / 100.0,
        "pan10_lb_ac": total_n_lb_ac * pan10_pct / 100.0,
    }


def material_results(rows: List[dict]) -> tuple[List[dict], dict]:
    details, totals = [], {key: 0.0 for key in NUTRIENTS}
    totals["cost"] = 0.0
    for row in rows:
        name = row.get("name", "")
        if name not in MATERIALS:
            continue
        rate, price = max(0, num(row.get("rate"))), max(0, num(row.get("price")))
        material = MATERIALS[name]
        supplied = {}
        for key in NUTRIENTS:
            supplied[key] = rate * num(material[key]) / 100.0
            totals[key] += supplied[key]
        cost = rate * price
        totals["cost"] += cost
        per_lb = {key: (price / (num(material[key]) / 100.0) if num(material[key]) > 0 else None) for key in NUTRIENTS}
        details.append({"name":name,"category":material["category"],"rate":rate,"price":price,"cost":cost,"supplied":supplied,"cost_per_lb":per_lb})
    return details, totals


def operation_cost(data: dict) -> dict:
    method = data.get("method", "none")
    defaults = EQUIPMENT.get(method, EQUIPMENT["none"])
    hp = max(0, num(data.get("tractor_hp")))
    fuel_price = max(0, num(data.get("fuel_price")))
    labor_rate = max(0, num(data.get("labor_rate")))
    width = max(0, num(data.get("width_ft"), defaults["width_ft"]))
    speed = max(0, num(data.get("speed_mph"), defaults["speed_mph"]))
    implement_cost = max(0, num(data.get("implement_cost_hr"), defaults["implement_cost_hr"]))
    fuel_gal_hr = 0.044 * hp
    tractor_cost_hr = 0.125 * hp  # $500/hp / (20 years * 200 hr/year)
    acres_hr = speed * width * 0.85 / 8.247 if speed > 0 and width > 0 else 0.0
    labor_cost_ac = labor_rate / acres_hr if acres_hr else 0.0
    total_cost_ac = (implement_cost + fuel_gal_hr * fuel_price + tractor_cost_hr + labor_rate) / acres_hr if acres_hr else 0.0
    return {"fuel_gal_hr":fuel_gal_hr,"tractor_cost_hr":tractor_cost_hr,"acres_hr":acres_hr,"labor_cost_ac":labor_cost_ac,"total_cost_ac":total_cost_ac}


@app.get("/")
def index():
    materials = [{"name":k, **v} for k, v in MATERIALS.items()]
    return render_template("index.html", materials=materials, equipment=EQUIPMENT)


@app.post("/api/calculate")
def calculate():
    payload = request.get_json(force=True) or {}
    try:
        cc = cover_crop_analysis(
            num(payload.get("cover_crop", {}).get("area_ft2")),
            num(payload.get("cover_crop", {}).get("sample_lb")),
            num(payload.get("cover_crop", {}).get("n_percent")),
            num(payload.get("cover_crop", {}).get("dm_percent")),
        )
        details, totals = material_results(payload.get("materials", []))
        for key in ["total_n", "dry_matter", "pan4", "pan10"]:
            source = {"total_n":"total_n_lb_ac","dry_matter":"dry_lb_ac","pan4":"pan4_lb_ac","pan10":"pan10_lb_ac"}[key]
            totals[key] += cc[source]
        recommendations = payload.get("recommendations", {})
        balance = {key: totals[key] - num(recommendations.get(key)) for key in NUTRIENTS}
        operations = [operation_cost(item) | {"method":item.get("method", "none")} for item in payload.get("operations", [])]
        seed_cost = sum(max(0, num(x.get("cost_per_lb"))) * max(0, num(x.get("rate_lb_ac"))) for x in payload.get("seed", []))
        inoculum = max(0, num(payload.get("inoculum_cost_ac")))
        irrigation = max(0, num(payload.get("irrigations"))) * max(0, num(payload.get("irrigation_cost_ac"), 25))
        management_cost = seed_cost + inoculum + irrigation + sum(x["total_cost_ac"] for x in operations)
        application_cost = max(0, num(payload.get("application_cost_ac")))
        return jsonify({
            "cover_crop": cc,
            "material_details": details,
            "totals": totals,
            "balance": balance,
            "operations": operations,
            "cover_crop_management_cost": management_cost,
            "total_amendment_cost": totals["cost"] + application_cost,
            "grand_total_cost": totals["cost"] + application_cost + management_cost,
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
