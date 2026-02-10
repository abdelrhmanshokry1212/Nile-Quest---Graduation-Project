import pandas as pd
import json
import os
import time
import google.generativeai as genai
import typing_extensions as typing

# --- CONFIGURATION ---
POI_FILE = "Cairo_Giza_Final_Verified_POIs.xlsx"
OUTPUT_FILE = "data/training_data.json"
API_KEY = "AIzaSyB792-Wev46C3ot-ruoQaFihHVsH__qek8"  # Using your key
# We will auto-detect the best model

def get_best_model():
    """Finds the best available Gemini model."""
    genai.configure(api_key=API_KEY)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority list
        preferred = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        for p in preferred:
            if p in models:
                return p
        
        # Fallback to any gemini model
        gemini_models = [m for m in models if 'gemini' in m]
        if gemini_models:
            return gemini_models[0]
            
        return "models/gemini-pro" # Hope for the best
    except Exception as e:
        print(f"Error listing models: {e}")
        return "models/gemini-1.5-flash"

def generate_queries_for_poi(model, row):
    """Generates synthetic queries for a single POI."""
    
    name = row['Name']
    category = row.get('Category', 'Tourist Attraction')
    desc = row.get('Description', '')
    
    prompt = f"""
    I am building a recommendation system for tourists in Cairo and Giza.
    
    Target POI: "{name}"
    Category: "{category}"
    Details: "{desc}"
    
    Generate 5 distinct, natural language user queries/requests that should lead to this recommendation.
    - Mix vague queries (e.g. "somewhere silent") and specific ones (e.g. "history of pharaohs").
    - Do NOT mention the name "{name}" in the query.
    - Format as a JSON list of strings.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        # Clean up json markdown if present
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
        
        # Simple parsing
        queries = json.loads(text)
        if isinstance(queries, list):
            return queries
        return []
    except Exception as e:
        print(f"Error generating for {name}: {e}")
        return []

def main():
    print("=== Synthetic Data Generation ===")
    
    # 1. Load Data
    if not os.path.exists(POI_FILE):
        print(f"Error: {POI_FILE} not found.")
        return
        
    df = pd.read_excel(POI_FILE)
    print(f"Loaded {len(df)} POIs.")
    
    # 2. Setup Model
    model_name = get_best_model()
    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    
    # 3. Generate
    training_data = []
    
    # Create data dir
    os.makedirs("data", exist_ok=True)
    
    # Progress bar simulation
    total = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        print(f"[{i+1}/{total}] Generating for: {row['Name']}...")
        
        queries = generate_queries_for_poi(model, row)
        
        for q in queries:
            training_data.append({
                "query": q,
                "positive": row['Name'], # We train to match Query -> POI Name (or ID)
                "category": row.get('Category', '')
            })
            
        # Rate limit safety (free tier is 15 RPM, but flash is higher)
        time.sleep(1.0) 
        
        # Save periodically
        if (i+1) % 10 == 0:
            with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
                json.dump(training_data, f, indent=2)
                
    # Final Save
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(training_data, f, indent=2)
        
    print(f"\nDone! Generated {len(training_data)} training pairs.")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
