"""Generate fleet_data.ttl (deterministic) for the bfo_cco Voicebox test.

Usage: python gen_fleet_data.py      (writes fleet_data.ttl next to this file)
The expected results in queries/*.rq and ../tests/voicebox/questions.json are derived from
this data; changing the generator changes them.
"""
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fleet_data.ttl"
L = ["@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
     "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
     "@prefix : <https://example.org/fleet#> .",
     "@prefix d: <https://example.org/fleet/data/> .", ""]


def add(s, *po):
    L.append(f"{s} " + " ;\n    ".join(po) + " .")


# Installations
add("d:kirtland", "a :AirBase", 'rdfs:label "Kirtland AFB"')
add("d:nellis", "a :AirBase", 'rdfs:label "Nellis AFB"')
add("d:bliss", "a :ArmyPost", 'rdfs:label "Fort Bliss"')
hangars = {"h1": ("Hangar 1", "kirtland"), "h2": ("Hangar 2", "kirtland"),
           "h3": ("Hangar 3", "nellis"), "h4": ("Hangar 4", "nellis")}
for k, (name, base) in hangars.items():
    add(f"d:{k}", "a :Hangar", f'rdfs:label "{name}"', f":locatedAt d:{base}")
add("d:mp1", "a :MotorPool", 'rdfs:label "Motor Pool A"', ":locatedAt d:bliss")

# Aircraft: 10 fighters, 4 transports
aircraft = [(f"AF-{1000 + i}", "FighterAircraft", 1) for i in range(1, 11)] + \
           [(f"AF-{2000 + i}", "TransportAircraft", 4) for i in range(1, 5)]
housing = {"AF-1001": "h1", "AF-1002": "h1", "AF-1003": "h1", "AF-1004": "h1", "AF-1005": "h1",
           "AF-1006": "h3", "AF-1007": "h3", "AF-1008": "h3", "AF-1009": "h4", "AF-1010": "h4",
           "AF-2001": "h2", "AF-2002": "h2", "AF-2003": "h4", "AF-2004": "h4"}
hours = {t: 180 + (i * 137) % 2400 for i, (t, _, _) in enumerate(aircraft)}
eng_n = 0
for tail, cls, n_eng in aircraft:
    a = f"d:{tail.lower()}"
    add(a, f"a :{cls}", f'rdfs:label "{tail}"', f':tailNumber "{tail}"',
        f':hoursSinceOverhaul "{hours[tail]}.0"^^xsd:decimal', f":housedIn d:{housing[tail]}")
    for _ in range(n_eng):
        eng_n += 1
        e = f"d:eng{eng_n:02d}"
        add(e, "a :TurbofanEngine", f'rdfs:label "Engine ENG-{eng_n:02d}"', f':serialNumber "ENG-{eng_n:02d}"', f":installedOn {a}")
        add(f"d:eng{eng_n:02d}_fan", "a :EngineModule", f'rdfs:label "ENG-{eng_n:02d} fan module"', f":partOf {e}")
        add(f"d:eng{eng_n:02d}_core", "a :EngineModule", f'rdfs:label "ENG-{eng_n:02d} core module"', f":partOf {e}")
        add(f"d:eng{eng_n:02d}_blades", "a :BladeSet", f'rdfs:label "ENG-{eng_n:02d} fan blade set"', f":partOf d:eng{eng_n:02d}_fan")

# Targeting pods with IR cameras on fighters AF-1001..AF-1006; those fighters are sensor platforms
for i in range(1, 7):
    tail = f"AF-{1000 + i}"
    pod, cam = f"d:pod{i}", f"d:cam{i}"
    add(pod, "a :TargetingPod", f'rdfs:label "Targeting pod TP-{i}"', f":installedOn d:{tail.lower()}")
    add(cam, "a :InfraredCamera", f'rdfs:label "IR camera IRC-{i}"', f":partOf {pod}", f":hasCapability d:cam{i}_cap")
    add(f"d:cam{i}_cap", "a :SensorCapability", f'rdfs:label "IRC-{i} infrared imaging capability"')
    add(f"d:{tail.lower()}_spr", "a :SensorPlatformRole", f'rdfs:label "{tail} sensor platform role"')
    L.append(f"d:{tail.lower()} :hasRole d:{tail.lower()}_spr .")

# Ground vehicles: 6 tanks, 5 trucks, all in Motor Pool A
for i in range(1, 7):
    add(f"d:tk{i:02d}", "a :MainBattleTank", f'rdfs:label "Tank TK-{i:02d}"', f':serialNumber "TK-{i:02d}"', ":housedIn d:mp1")
for i in range(1, 6):
    add(f"d:tr{i:02d}", "a :TacticalTruck", f'rdfs:label "Truck TR-{i:02d}"', f':serialNumber "TR-{i:02d}"', ":housedIn d:mp1")

# Satellites: sensors and sensor platforms
for i in range(1, 3):
    s = f"d:sat{i}"
    add(s, "a :ReconSatellite", f'rdfs:label "Satellite SAT-{i}"', f':serialNumber "SAT-{i}"',
        f":hasCapability d:sat{i}_cap", f":hasRole d:sat{i}_spr")
    add(f"d:sat{i}_cap", "a :SensorCapability", f'rdfs:label "SAT-{i} imaging capability"')
    add(f"d:sat{i}_spr", "a :SensorPlatformRole", f'rdfs:label "SAT-{i} sensor platform role"')

# Maintenance: 12 events, dates spread over Jul-Sep 2026 (5 in August)
targets = ["af-1001", "af-1003", "af-2001", "tk01", "af-1006", "af-1002", "tr02", "af-2003", "af-1009", "tk04", "af-1001", "af-2004"]
dates = [date(2026, 7, 6), date(2026, 7, 20), date(2026, 7, 29), date(2026, 8, 3), date(2026, 8, 11),
         date(2026, 8, 18), date(2026, 8, 25), date(2026, 8, 31), date(2026, 9, 2), date(2026, 9, 9),
         date(2026, 9, 15), date(2026, 9, 22)]
for i, (t, dt) in enumerate(zip(targets, dates), start=1):
    add(f"d:mx{i:02d}", "a :MaintenanceEvent", f'rdfs:label "Maintenance WO-26-{i:04d}"',
        f':workOrderNumber "WO-26-{i:04d}"', f':eventDate "{dt.isoformat()}"^^xsd:date', f":performedOn d:{t}")

OUT.write_text("\n".join(L) + "\n")
print(f"wrote {OUT}: {len(aircraft)} aircraft, {eng_n} engines, 6 pods, 11 ground vehicles, 2 satellites, 12 maintenance events")
print("hours since overhaul:", hours)
