
from tourist_recommendation_system import TouristRecommendationSystem, UserProfile

def main():
    print("=== AI Tourist Recommendation System ===")
    
    # 1. Initialize System
    try:
        sys = TouristRecommendationSystem("Cairo_Giza_1000_Real_POIs.xlsx")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return


    # 2. Define User Profile (Interactive Input)
    print("\n--- Enter Your Preferences ---")
    
    # Duration
    while True:
        try:
            days = int(input("How many days is your trip? (e.g., 3): ").strip() or "1")
            if days > 0: break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid number.")

    # Budget
    while True:
        try:
            budget_input = input("What is your DAILY budget in EGP? (e.g., 1000): ").strip()
            budget_daily = float(budget_input) if budget_input else 1000.0
            break
        except ValueError:
            print("Invalid amount. Please enter a number.")

    # Interests
    print("\nSelect your interests (enter weights 0.0 to 1.0, or press Enter to skip)")
    available_interests = ["History", "Culture", "Food", "Nature", "Shopping", "Entertainment", "Religious"]
    user_interests = {}
    
    print("Example: Enter '0.9' for high interest, '0.5' for medium.")
    for interest in available_interests:
        val = input(f" - {interest}: ").strip()
        if val:
            try:
                weight = float(val)
                if weight > 0:
                    user_interests[interest] = weight
            except ValueError:
                pass
    
    # Custom interest
    custom = input("Any other specific interest? (e.g. 'Pharaonic'): ").strip()
    if custom:
        user_interests[custom] = 1.0

    if not user_interests:
        print("No specific interests provided. We will recommend popular attractions.")
    
    # Pace (Removed as per feedback, defaulting to moderate/dynamic)
    pace = "moderate" 

    
    user = UserProfile(
        interests=user_interests,
        budget_daily=budget_daily,
        budget_total=budget_daily * days * 1.5, # Estimate buffer
        duration_days=days,
        pace=pace,
        start_time="09:00",
        end_time="18:00", # Default 6 PM
        geo_center=(30.0444, 31.2357), # Default Downtown Cairo
        indoor_preference="neutral"
    )

    print(f"\nUser Profile:")
    print(f"- Interests: {', '.join([f'{k}({v})' for k,v in user.interests.items()])}")
    print(f"- Budget: {user.budget_daily} EGP/day")
    print(f"- Duration: {user.duration_days} days")
    
    # 3. Generate Itinerary
    print("\nGenerating Itinerary...")
    itinerary = sys.generate_itinerary(user)
    
    # 4. Display Results
    print("\n" + "="*60)
    print("                  YOUR PERSONALIZED ITINERARY")
    print("="*60)
    
    total_trip_cost = 0
    
    for day in sorted(itinerary.keys()):
        events = itinerary[day]
        print(f"\n[ DAY {day} ]")
        if not events:
            print("  (No activities scheduled for this day - constraints too strict?)")
            continue
            
        day_cost = 0
        for event in events:
            poi = event['poi']
            print(f"  {event['start_time']} - {event['end_time']} : {poi.name}")
            print(f"    Category: {poi.category} | {poi.subcategory}")
            print(f"    Cost: {poi.cost} EGP | Duration: {poi.duration_hours}h")
            print(f"    Why: {event['reason']}")
            day_cost += poi.cost
        
        print(f"  --> Daily Total: {day_cost} EGP")
        total_trip_cost += day_cost
        print("-" * 40)
        
    print("="*60)
    print(f"TOTAL ESTIMATED TRIP COST: {total_trip_cost} EGP")
    print("="*60)

if __name__ == "__main__":
    main()
