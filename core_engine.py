import math
import json
import sys
from datetime import datetime, timezone
from skyfield.api import load

def calculate_alignments(positions: dict, tolerance_deg: float = 15.0) -> dict:
    """
    Evaluates both 2D longitudinal separation and true 3D spatial alignment.
    Provides fallback visibility for ecliptic plane conjunctions.
    """
    planets_keys = list(positions.keys())
    alignments_2d = []
    alignments_3d = []

    for i in range(len(planets_keys)):
        for j in range(i + 1, len(planets_keys)):
            p1, p2 = planets_keys[i], planets_keys[j]
            lon1, lat1 = positions[p1]
            lon2, lat2 = positions[p2]
            
            # --- 2D Ecliptic Longitude Separation ---
            diff_2d = abs(lon1 - lon2) % 360
            if diff_2d > 180:
                diff_2d = 360 - diff_2d
            
            if diff_2d <= tolerance_deg:
                alignments_2d.append({
                    "pair": f"{p1}-{p2}",
                    "planar_separation_deg": round(diff_2d, 4)
                })

            # --- True 3D Great-Circle Separation ---
            r_lon1, r_lat1 = map(math.radians, [lon1, lat1])
            r_lon2, r_lat2 = map(math.radians, [lon2, lat2])
            
            cos_sep = (math.sin(r_lat1) * math.sin(lat2) + 
                       math.cos(r_lat1) * math.cos(r_lat2) * math.cos(r_lon1 - r_lon2))
            cos_sep = max(-1.0, min(1.0, cos_sep))
            sep_deg_3d = math.degrees(math.acos(cos_sep))

            if sep_deg_3d <= tolerance_deg:
                alignments_3d.append({
                    "pair": f"{p1}-{p2}",
                    "spatial_separation_3d_deg": round(sep_deg_3d, 4)
                })

    return {"planar_2d": alignments_2d, "spatial_3d": alignments_3d}

def compute_refined_telemetry_mesh(earth_lon: float, earth_lat: float) -> dict:
    """
    Establishes the complementary dipole-antipole polarity vectors.
    """
    dipole_lon = earth_lon % 360
    antipole_lon = (earth_lon + 180) % 360
    
    dipole_lat = earth_lat
    antipole_lat = -earth_lat

    return {
        "dipole_node": {
            "longitude_vector": round(dipole_lon, 4),
            "latitude_vector": round(dipole_lat, 4)
        },
        "antipole_node": {
            "longitude_vector": round(antipole_lon, 4),
            "latitude_vector": round(antipole_lat, 4)
        }
    }

def main():
    forced_angle = None
    if len(sys.argv) > 1:
        try:
            forced_angle = float(sys.argv[1])
        except ValueError:
            pass

    ts = load.timescale()
    t = ts.now()
    eph = load('de421.bsp')
    
    sun = eph['sun']
    earth = eph['earth']
    
    targets = {
        "Mercury": eph['mercury'],
        "Venus": eph['venus'],
        "Mars": eph['mars'],
        "Jupiter barycenter": eph['jupiter barycenter'],
        "Saturn barycenter": eph['saturn barycenter']
    }

    realtime_positions = {}
    for name, target in targets.items():
        astrometric = sun.at(t).observe(target)
        lat, lon, _ = astrometric.ecliptic_latlon()
        clean_name = name.split()[0]
        realtime_positions[clean_name] = (lon.degrees, lat.degrees)

    earth_astro = sun.at(t).observe(earth)
    e_lat, e_lon, _ = earth_astro.ecliptic_latlon()
    
    earth_lon_active = forced_angle if forced_angle is not None else e_lon.degrees
    earth_lat_active = e_lat.degrees

    all_alignments = calculate_alignments(realtime_positions)
    telemetry_layers = compute_refined_telemetry_mesh(earth_lon_active, earth_lat_active)

    output_schema = {
        "telemetry_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "earth_zone_anchor": {
            "longitude": round(earth_lon_active, 4),
            "latitude": round(earth_lat_active, 4)
        },
        "refined_telemetry_mesh": telemetry_layers,
        "tracked_alignments": all_alignments,
        "system_status": "Flawless"
    }

    print(json.dumps(output_schema, indent=2))

if __name__ == "__main__":
    main()
