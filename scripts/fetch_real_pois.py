import pandas as pd
import requests
import time
import os
import random
import math

def fetch_real_pois(input_file="Cairo_Giza_500_POIs.xlsx", output_file="Cairo_Giza_1000_Real_POIs.xlsx", target_total_count=1000):
    print(f"Loading existing data from {input_file}...")
    
    # Handle path variations
    if not os.path.exists(input_file):
         if os.path.exists(f"../{input_file}"):
            input_file = f"../{input_file}"
            # adjust output path to match input location
            if "/" in output_file or "\\" in output_file:
                 pass # User provided path, keep it
            else:
                 output_file = f"../{output_file}"
         else:
             print(f"Warning: {input_file} not found. Starting with empty dataset.")

    try:
        df_existing = pd.read_excel(input_file)
        print(f"Loaded {len(df_existing)} existing POIs.")
    except FileNotFoundError:
        df_existing = pd.DataFrame(columns=['Name', 'Latitude', 'Longitude', 'Category', 'Sub-category', 'Estimated visit duration', 'Entry cost (EGP)', 'Opening hours', 'Indoor / outdoor'])
        print("Starting with empty dataframe.")

    # Standardize existing names for deduplication
    existing_names = set()
    if not df_existing.empty and 'Name' in df_existing.columns:
        existing_names = set(df_existing['Name'].astype(str).str.strip().str.lower())
    
    # Target new count
    current_count = len(df_existing)
    needed = target_total_count - current_count
    if needed <= 0:
        print(f"Already have {current_count} POIs (Target: {target_total_count}). No new data needed.")
        return

    print(f"Need to fetch approximately {needed} new real POIs.")

    # Expanded Bounding box for greater Cairo/Giza:
    # South: 29.8, West: 30.8, North: 30.2, East: 31.5 -> This covers standard Cairo.
    # Expanded slightly: 29.7, 30.7, 30.3, 31.7
    bbox = "29.7,30.7,30.3,31.7"
    
    overpass_urls = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    # Query for Nodes, Ways, Relations
    # Expanded categories to reach target count
    query = f"""
    [out:json][timeout:180];
    (
      nwr["tourism"]({bbox});
      nwr["historic"]({bbox});
      nwr["leisure"]({bbox});
      
      nwr["amenity"="restaurant"]({bbox});
      nwr["amenity"="cafe"]({bbox});
      nwr["amenity"="fast_food"]({bbox});
      nwr["amenity"="ice_cream"]({bbox});
      nwr["amenity"="cinema"]({bbox});
      nwr["amenity"="theatre"]({bbox});
      nwr["amenity"="place_of_worship"]({bbox});
      nwr["amenity"="arts_centre"]({bbox});
      nwr["amenity"="library"]({bbox});
      nwr["amenity"="university"]({bbox});
      nwr["amenity"="hospital"]({bbox});
      nwr["amenity"="pharmacy"]({bbox});
      nwr["amenity"="bank"]({bbox});

      nwr["shop"="mall"]({bbox});
      nwr["shop"="department_store"]({bbox});
      nwr["shop"="supermarket"]({bbox});
      nwr["shop"="books"]({bbox});
      nwr["shop"="clothes"]({bbox});
      nwr["shop"="jewelry"]({bbox});
      nwr["shop"="gift"]({bbox});
      nwr["shop"="electronics"]({bbox});
      
      nwr["building"="public"]({bbox});
      nwr["office"="government"]({bbox});
    );
    out center;
    """
    
    elements = []
    success = False
    
    for url in overpass_urls:
        print(f"Querying Overpass API at {url}...")
        try:
            response = requests.get(url, params={'data': query}, timeout=200)
            if response.status_code == 200:
                try:
                    data = response.json()
                    elements = data.get('elements', [])
                    print(f"Fetched {len(elements)} raw elements from OSM.")
                    success = True
                    break
                except ValueError:
                    print(f"Error: Invalid JSON response from {url}")
            elif response.status_code == 429:
                print(f"Rate limited at {url}. Waiting 5s...")
                time.sleep(5)
            else:
                print(f"Error fetching data from {url}: {response.status_code}")
        except Exception as e:
            print(f"Network error with {url}: {e}")
            
    if not success:
        print("Failed to fetch data from all Overpass endpoints.")
        return

    new_pois = []
    
    def estimate_details(tags):
        category = "General"
        sub_category = "Site"
        indoor = "Outdoor"
        duration = "1 hour"
        cost = 0
        hours = tags.get('opening_hours', "9 AM - 10 PM")

        if 'tourism' in tags:
            t = tags['tourism']
            category = "Tourism"
            sub_category = t.capitalize().replace('_', ' ')
            if t in ['museum', 'gallery', 'artwork']:
                indoor = "Indoor"
                duration = "2 hours"
                cost = 100
            elif t in ['hotel', 'hostel']:
                sub_category = "Hotel"
                indoor = "Indoor"
            elif t == 'attraction':
                duration = "1.5 hours"
                cost = 50
            elif t == 'theme_park': # Added
                indoor = "Outdoor"
                duration = "4 hours"
                cost = 200

        elif 'historic' in tags:
            category = "Historic"
            sub_category = tags['historic'].capitalize().replace('_', ' ')
            duration = "1.5 hours"
            cost = 80
            
        elif 'amenity' in tags:
            a = tags['amenity']
            sub_category = a.capitalize().replace('_', ' ')
            if a in ['restaurant', 'cafe', 'fast_food', 'ice_cream']:
                category = "Food"
                indoor = "Indoor"
                duration = "1.5 hours"
                cost = 150
            elif a in ['cinema', 'theatre', 'arts_centre']:
                category = "Entertainment"
                indoor = "Indoor"
                duration = "3 hours"
                cost = 150
            elif a == 'place_of_worship':
                category = "Religious"
                indoor = "Indoor"
                duration = "0.5 hours"
            elif a in ['library', 'university', 'school']:
                category = "Education"
                indoor = "Indoor"
            elif a in ['hospital', 'pharmacy', 'bank']: # Added
                category = "Services"
                indoor = "Indoor"
                duration = "0.5 hours"

        elif 'leisure' in tags:
            l = tags['leisure']
            category = "Leisure"
            sub_category = l.capitalize().replace('_', ' ')
            if l in ['park', 'garden', 'nature_reserve']:
                indoor = "Outdoor"
                duration = "2 hours"
            elif l in ['sports_centre', 'stadium', 'fitness_centre']:
                indoor = "Indoor"
                duration = "2 hours"
                cost = 50
                
        elif 'shop' in tags:
            s = tags['shop']
            category = "Shopping"
            sub_category = s.capitalize().replace('_', ' ')
            indoor = "Indoor"
            duration = "1 hour"
            if s == 'mall':
                duration = "3 hours"
            if s in ['jewelry', 'electronics']: # Higher cost heuristic
                 pass 
                 
        elif 'office' in tags: # Added
             category = "Business"
             sub_category = tags.get('office', 'Office').capitalize().replace('_', ' ')
             indoor = "Indoor"
        
        elif 'building' in tags: # Added
             category = "Public"
             sub_category = tags.get('building', 'Building').capitalize().replace('_', ' ')
             indoor = "Indoor"

        # Heuristics for cost based on keywords in name if not already set
        if cost == 0 and ('club' in sub_category.lower() or 'cinema' in sub_category.lower()):
             cost = 100
        
        # Ensure non-zero cost for some types
        if cost == 0 and category in ['Shopping', 'Food', 'Entertainment']:
             cost = 50 # Minimum spend estimate

        return category, sub_category, indoor, duration, cost, hours

    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name:en') or tags.get('name') or tags.get('alt_name')
        
        if not name:
            continue
            
        clean_name = name.strip()
        lower_name = clean_name.lower()
        
        if len(clean_name) < 3: 
            continue
        if lower_name in existing_names:
            continue
            
        # Coords (Center for ways/relations)
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        
        if not lat or not lon:
            continue

        cat, sub, indoor, dur, cost, hours = estimate_details(tags)

        poi = {
            'Name': clean_name,
            'Latitude': lat,
            'Longitude': lon,
            'Category': cat,
            'Sub-category': sub,
            'Estimated visit duration': dur,
            'Entry cost (EGP)': cost,
            'Opening hours': hours,
            'Indoor / outdoor': indoor
        }
        
        new_pois.append(poi)
        existing_names.add(lower_name)
        
        if len(new_pois) >= needed:
            break
            
    print(f"Generated {len(new_pois)} new valid unique POIs from OSM.")
    
    if len(new_pois) == 0:
        print("No new unique POIs found.")
        return

    new_df = pd.DataFrame(new_pois)
    
    # Handle column alignment for Lat/Long
    coord_cols = [c for c in df_existing.columns if "Lat" in c and "Long" in c]
    has_separate_cols = 'Latitude' in df_existing.columns and 'Longitude' in df_existing.columns
    
    if coord_cols and not has_separate_cols:
        # Combined column case: "Latitude / Longitude" or similar
        col_name = coord_cols[0]
        new_df[col_name] = new_df.apply(lambda row: f"{row['Latitude']}, {row['Longitude']}", axis=1)
        # Drop separate cols
        new_df = new_df.drop(columns=['Latitude', 'Longitude'])
    elif not coord_cols and not has_separate_cols:
         # Create separate if neither exists (unlikely given empty df creation)
         pass

    # Merge
    combined_df = pd.concat([df_existing, new_df], ignore_index=True)
    
    print(f"Saving {len(combined_df)} total POIs to {output_file}...")
    combined_df.to_excel(output_file, index=False)
    print("Done!")

if __name__ == "__main__":
    fetch_real_pois()
