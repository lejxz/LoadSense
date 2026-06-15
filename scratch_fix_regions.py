import sqlite3
from pathlib import Path

DATA_DIR = Path("data/countries")

def determine_region(route_id, country, name):
    if country == "PH":
        if route_id.startswith("PH-MNL"): return "Metro Manila"
        if route_id.startswith("PH-DVO"): return "Davao Region"
        if route_id.startswith("PH-ILO"): return "Western Visayas"
        return "Cebu"
    elif country == "TH":
        return "Bangkok"
    elif country == "VN":
        if "Hanoi" in name or "My Dinh" in name:
            return "Hanoi"
        return "Ho Chi Minh City"
    elif country == "MY":
        return "Klang Valley"
    elif country == "ID":
        return "Jakarta"
    return "Other"

for country in ["PH", "TH", "VN", "MY", "ID"]:
    db_path = DATA_DIR / country / "loadsense.sqlite"
    if not db_path.exists(): continue
    conn = sqlite3.connect(db_path)
    routes = conn.execute("SELECT route, name FROM routes").fetchall()
    for route_id, name in routes:
        region = determine_region(route_id, country, name)
        conn.execute("UPDATE routes SET region=? WHERE route=?", (region, route_id))
    conn.commit()
    conn.close()
    print(f"Updated {country} regions")
