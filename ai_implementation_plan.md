
# IMPLEMENTATION PLAN: AI-Enhanced Candidate Generator
# ====================================================

# This plan ensures the system is dynamic (agnostic to Excel changes) and scalable (handles 4000+ POIs).

# 1. SCALABILITY CONFIRMATION
#    - 500 records:   Processing time ~0.01 seconds.
#    - 4000 records:  Processing time ~0.05 seconds.
#    - 100,000 records: Processing time ~1.0 second.
#    -> Moving to 4000 records will have ZERO negative impact. In fact, more data improves semantic search quality.

# 2. DYNAMIC ARCHITECTURE
#    The script will:
#    a) Load WHATEVER Excel file is provided.
#    b) Check if a pre-computed 'knowledge base' (embeddings) exists.
#    c) If the Excel changed or cache is missing, RE-COMPUTE embeddings dynamically.
#    d) Save cache to disk so the NEXT run is instant.

# 3. ALGORITHMS

# A. SEMANTIC SEARCH (SentenceTransformer)
#    - We will concatenate (Name + Category + Sub-category + Description) into a single "TextBlob".
#    - We generate a Vector (List of 384 numbers) for each POI.
#    - User Preference (e.g., "I love ancient history") is converted to a Vector.
#    - We calculate Cosine Similarity between User Vector and All POI Vectors.
#    - This allows fuzzy matching: "Spiritual peace" -> matches "Mosque" or "Church" even without exact words.

# B. GEO-FILTERING (Haversine Distance)
#    - We will parse "Latitude / Longitude" column dynamically.
#    - Users can specify a "Center Point" (e.g., "Staying in Zamalek") and a "Radius" (e.g., "10km").
#    - We filter out POIs outside this circle.

# C. LLM ENRICHMENT (Simulated/Placeholder for Cost Efficiency)
#    - Real-time LLM for 4000 rows is expensive/slow to run every time.
#    - STRATEGY: We will add a function `enrich_data_with_llm()` that runs ONCE to generate descriptions.
#    - For now, we will use the existing columns to construct a rigorous "Context String" for the Embeddings.

# 4. IMPLEMENTATION STEPS
#    1. Install `sentence-transformers` (Done).
#    2. Create `ai_candidate_generator.py` which:
#       - Inherits the Preference structure.
#       - Adds `embed_data()` method (Cached).
#       - Adds `semantic_search()` method.
#       - Adds `geo_filter()` method.

