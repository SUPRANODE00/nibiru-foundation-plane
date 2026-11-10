import math
import json
import sys

def calculate_alignment(planets: dict, tolerance_deg: float = 15.0) -> dict:
    """
    Evaluates planetary positions relative to the Earth Zone coordinate origin.
    Determines alignment states based on angular distribution.
    """
    sorted_planets = sorted(planets.items(), key=lambda x: x[1])
    alignments = []
    
    for i in range(len(sorted_planets)):
        for j in range(i + 1, len(sorted_planets)):
            p1, a1 = sorted_planets[i]
            p2, a2 = sorted_planets[j]
            diff = abs(a1 - a2) % 360
            if diff > 180:
                diff = 360 - diff
                
            if diff <= tolerance_deg:
                alignments.append({"pair": f"{p1}-{p2}", "separation_deg": round(diff, 2)})
    return alignments

def compute_dipole_antipole(earth_longitude: float) -> dict:
    """
    Generates the exact inverse vector for the Earth Zone node.
    Establishes the complementary polarity boundary.
    """
    dipole = earth_longitude % 360
    antipole = (earth_longitude + 180) % 360
    return {
        "dipole_vector": round(dipole, 4),
        "antipole_vector": round(antipole, 4)
    }

def main():
    # Sample planetary longitudes (degrees along the ecliptic)
    mock_ephemeris = {
        "Mercury": 45.2,
        "Venus": 48.7,
        "Mars": 120.3,
        "Jupiter": 52.1,
        "Saturn": 280.5
    }
    
    earth_zone_long = 46.0  # Core reference coordinate
    
    alignment_results = calculate_alignment(mock_ephemeris)
    polarity_mesh = compute_dipole_antipole(earth_zone_long)
    
    output_schema = {
        "earth_zone_anchor": {"longitude": earth_zone_long},
        "polarity_axis": polarity_mesh,
        "detected_alignments": alignment_results,
        "system_status": "Flawless"
    }
    
    print(json.dumps(output_schema, indent=2))

if __name__ == "__main__":
    main()
