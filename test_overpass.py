import requests
import json
import time

def test_overpass():
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    (
      node["tourism"](29.9,31.1,30.2,31.4);
      node["amenity"="restaurant"](29.9,31.1,30.2,31.4);
      node["historic"](29.9,31.1,30.2,31.4);
    );
    out 5;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_overpass()
