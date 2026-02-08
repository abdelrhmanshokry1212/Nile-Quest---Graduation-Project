import pandas as pd
import numpy as np
import random
import os

def generate_pois(input_file="Cairo_Giza_500_POIs.xlsx", output_file="Cairo_Giza_1000_POIs.xlsx", num_new_pois=500):
    print(f"Loading data from {input_file}...")
    if not os.path.exists(input_file):
        # Fallback for running from scripts/ dir potentially
        if os.path.exists(f"../{input_file}"):
            input_file = f"../{input_file}"
            output_file = f"../{output_file}"
        else:
            raise FileNotFoundError(f"File not found: {input_file}")

    df = pd.read_excel(input_file)
    
    # helper for coords
    def parse_coords(x):
        try:
            pts = str(x).split(',')
            return float(pts[0].strip()), float(pts[1].strip())
        except:
            return None, None

    # Identify coordinate column
    coord_col = next((c for c in df.columns if "Lat" in c and "Long" in c), None)
    if not coord_col:
        print("Could not find Latitude/Longitude column. Creating dummy bounds.")
        lat_min, lat_max = 29.9, 30.2
        lon_min, lon_max = 31.1, 31.4
    else:
        coords = df[coord_col].apply(parse_coords).dropna()
        lats = [c[0] for c in coords if c[0] is not None]
        lons = [c[1] for c in coords if c[1] is not None]
        
        if lats and lons:
            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)
        else:
             lat_min, lat_max = 29.9, 30.2
             lon_min, lon_max = 31.1, 31.4

    # Extract domains from existing data
    categories = df['Category'].dropna().unique().tolist()
    sub_categories = df['Sub-category'].dropna().unique().tolist()
    opening_hours_opts = df['Opening hours'].dropna().unique().tolist()
    indoor_outdoor_opts = df['Indoor / outdoor'].dropna().unique().tolist()
    
    # Generate new data
    new_rows = []
    print(f"Generating {num_new_pois} synthetic POIs...")
    
    start_id = len(df) + 1
    
    for i in range(num_new_pois):
        # Random coord within box
        lat = random.uniform(lat_min, lat_max)
        lon = random.uniform(lon_min, lon_max)
        
        # Simple Logic: Assign mainly appropriate sub-cats to cats (optional, but let's keep it simple random for now or try to match)
        # We will just pick random existing values
        cat = random.choice(categories) if categories else "General"
        sub = random.choice(sub_categories) if sub_categories else "Site"
        
        # Cost
        cost = random.choice([0, 10, 20, 50, 100, 150, 200, 500])
        
        row = {
            'Name': f"Synthetic POI {start_id + i}",
            coord_col: f"{lat:.6f}, {lon:.6f}",
            'Category': cat,
            'Sub-category': sub,
            'Estimated visit duration': f"{random.randint(1, 4)} hours",
            'Entry cost (EGP)': cost,
            'Opening hours': random.choice(opening_hours_opts) if opening_hours_opts else "9 AM - 5 PM",
            'Indoor / outdoor': random.choice(indoor_outdoor_opts) if indoor_outdoor_opts else "Outdoor"
        }
        new_rows.append(row)
        
    new_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([df, new_df], ignore_index=True)
    
    print(f"Saving {len(combined_df)} POIs to {output_file}...")
    combined_df.to_excel(output_file, index=False)
    print("Done!")

if __name__ == "__main__":
    generate_pois()
