import sqlite3
from pathlib import Path

DATA_DIR = Path("data/countries")

def parse_endpoints(name: str):
    parts = name.split(" - ")
    if len(parts) == 2:
        p1 = parts[0].replace("(", "").strip()
        p2 = parts[1].replace(")", "").strip()
        if ": " in p1:
            p1 = p1.split(": ", 1)[1]
        else:
            words = p1.split(" ")
            if len(words) >= 2 and (words[0].isupper() or any(c.isdigit() for c in words[0]) or words[0].lower() in ['mybus', 'bus', 'jeep']):
                p1 = " ".join(words[1:])
        if " (via " in p2:
            p2 = p2.split(" (via ")[0]
        elif " via " in p2:
            p2 = p2.split(" via ")[0]
        return p1.strip(), p2.strip()
    elif "Line" in name or "Monorail" in name:
        return "Start Station", "End Station"
    return "Origin", "Destination"

for country in ["PH", "TH", "VN", "MY", "ID"]:
    db_path = DATA_DIR / country / "loadsense.sqlite"
    if not db_path.exists(): continue
    conn = sqlite3.connect(db_path)
    routes = conn.execute("SELECT route, name FROM routes").fetchall()
    for route_id, name in routes:
        orig, dest = parse_endpoints(name)
        conn.execute("UPDATE routes SET origin_name=?, destination_name=? WHERE route=?", (orig, dest, route_id))
        conn.execute("UPDATE route_points SET label=? WHERE route=? AND sequence_order=0", (orig, route_id))
        max_seq = conn.execute("SELECT MAX(sequence_order) FROM route_points WHERE route=?", (route_id,)).fetchone()[0]
        if max_seq is not None:
            conn.execute("UPDATE route_points SET label=? WHERE route=? AND sequence_order=?", (dest, route_id, max_seq))
    conn.commit()
    conn.close()
    print(f"Updated {country}")
