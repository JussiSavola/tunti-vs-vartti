import requests
import pandas as pd
import argparse
from datetime import datetime

def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) and len(data) > 0 else []
        return []
    except Exception:
        return []

def get_transfer_price(dt_str, day_price, night_price):
    dt = datetime.fromisoformat(dt_str)
    hour = dt.hour
    return day_price if 7 <= hour < 22 else night_price

def calculate_day(data_60, data_15, args):
    if not data_60 or not data_15:
        return None

    energy_target = args.energy
    hours_to_use = args.hours

    # Lasketaan kokonaishinnat kaikille jaksoille (Pörssi + Siirto + Marginaali)
    for item in data_60:
        transfer = get_transfer_price(item['DateTime'], args.day, args.night)
        item['TotalTotal'] = item['PriceWithTax'] + (transfer / 100) + (args.margin / 100)
    for item in data_15:
        transfer = get_transfer_price(item['DateTime'], args.day, args.night)
        item['TotalTotal'] = item['PriceWithTax'] + (transfer / 100) + (args.margin / 100)

    # A) Optimi 60 min
    sorted_60 = sorted(data_60, key=lambda x: x['TotalTotal'])
    best_60 = sorted(sorted_60[:hours_to_use], key=lambda x: x['DateTime'])
    cost_a = sum(h['TotalTotal'] * (energy_target / hours_to_use) for h in best_60)

    # B) Optimi 15 min
    num_15min_slots = hours_to_use * 4
    sorted_15 = sorted(data_15, key=lambda x: x['TotalTotal'])
    best_15 = sorted_15[:num_15min_slots]
    cost_b = sum(s['TotalTotal'] * (energy_target / num_15min_slots) for s in best_15)

    result = {
        "A": {"cost": cost_a, "avg": (cost_a / energy_target) * 100, "times": ", ".join([datetime.fromisoformat(h['DateTime']).strftime('%H:%M') for h in best_60])},
        "B": {"cost": cost_b, "avg": (cost_b / energy_target) * 100},
        "C": None
    }

    # C) No Brains (22, 23, 00, 01...)
    if args.nobrains:
        nb_order = [22, 23, 0, 1, 2, 3, 4, 5, 6, 21, 20, 19] 
        selected_nb = []
        hour_map = {datetime.fromisoformat(i['DateTime']).hour: i for i in data_60}
        
        for h in nb_order:
            if h in hour_map and len(selected_nb) < hours_to_use:
                selected_nb.append(hour_map[h])
        
        if len(selected_nb) == hours_to_use:
            selected_nb_print = sorted(selected_nb, key=lambda x: x['DateTime'])
            cost_c = sum(h['TotalTotal'] * (energy_target / hours_to_use) for h in selected_nb)
            result["C"] = {
                "cost": cost_c,
                "avg": (cost_c / energy_target) * 100,
                "times": ", ".join([datetime.fromisoformat(h['DateTime']).strftime('%H:%M') for h in selected_nb_print])
            }

    return result

def main():
    parser = argparse.ArgumentParser(description="Sähkön hintavertailu.")
    parser.add_argument("-e", "--energy", type=float, default=12.0)
    parser.add_argument("-o", "--hours", type=int, default=5)
    parser.add_argument("-d", "--day", type=float, default=5.58)
    parser.add_argument("-n", "--night", type=float, default=3.44)
    parser.add_argument("-m", "--margin", type=float, default=0.61)
    parser.add_argument("--nobrains", action="store_true")
    args = parser.parse_args()

    for label, param in [("TÄNÄÄN", "Today"), ("HUOMENNA", "DayForward")]:
        d60 = fetch_data(f"https://api.spot-hinta.fi/{param}?priceResolution=60")
        d15 = fetch_data(f"https://api.spot-hinta.fi/{param}?priceResolution=15")
        
        res = calculate_day(d60, d15, args)
        if not res:
            if param == "DayForward": print(f"\n--- {label}: Dataa ei vielä saatavilla ---")
            continue

        print(f"\n--- {label} ({args.energy} kWh / {args.hours} h) ---")
        rows = [
            ["Optimi 1h", f"{res['A']['cost']:.4f} €", f"{res['A']['avg']:.2f} s/kWh", res['A']['times']],
            ["Optimi 15min", f"{res['B']['cost']:.4f} €", f"{res['B']['avg']:.2f} s/kWh", "Vartti-optimointi"]
        ]
        if res["C"]:
            rows.append(["No Brains", f"{res['C']['cost']:.4f} €", f"{res['C']['avg']:.2f} s/kWh", res['C']['times']])
        
        print(pd.DataFrame(rows, columns=["Skenaario", "Hinta", "s/kWh", "Ajat"]).to_string(index=False))

        # Säästövertailu
        if args.nobrains and res["C"]:
            saving_euro = res["C"]["cost"] - res["B"]["cost"]
            saving_pct = (saving_euro / res["C"]["cost"]) * 100
            print(f"\n>> OPTIMOINNIN HYÖTY (B vs C): {saving_euro:.4f} € ({saving_pct:.1f} %)")
        print("-" * 50)

if __name__ == "__main__":
    main()