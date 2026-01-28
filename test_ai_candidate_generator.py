import unittest
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd
import numpy as np
import os
from ai_candidate_generator import AICandidateGenerator

class TestAICandidateGenerator(unittest.TestCase):

    def setUp(self):
        # Mocking the data loading parts to avoid file dependency
        self.sample_data = {
            'Name': ['Pyramids', 'Cairo Tower', 'Museum'],
            'Category': ['History', 'Modern', 'History'],
            'Sub-category': ['Ancient', 'View', 'Art'],
            'Indoor / outdoor': ['Outdoor', 'Indoor', 'Indoor'],
            'Entry cost (EGP)': [200, 150, 100],
            'Latitude': [29.9792, 30.0444, 30.0478],
            'Longitude': [31.1342, 31.2357, 31.2336]
        }
        self.df = pd.DataFrame(self.sample_data)

    @patch('ai_candidate_generator.pd.read_excel')
    @patch('ai_candidate_generator.os.path.exists')
    @patch('ai_candidate_generator.SentenceTransformer')
    @patch('pickle.dump')
    def test_initialization_success(self, mock_dump, mock_transformer, mock_exists, mock_read_excel):
        """Test successful initialization and data loading."""
        # exists returns True for Excel, False for pkl to skip cache load
        def exists_side_effect(path):
            if path.endswith('.xlsx'): return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        mock_read_excel.return_value = self.df.copy()
        
        # Ensure encode returns something valid (list or numpy) to avoid other issues, 
        # though dump is mocked now.
        mock_transformer.return_value.encode.return_value = np.zeros((3, 384))

        generator = AICandidateGenerator()
        
        self.assertIsNotNone(generator.df)
        self.assertEqual(len(generator.df), 3)
        mock_transformer.assert_called_once()
        # Should attempt to save cache since it didn't exist
        mock_dump.assert_called_once()
    
    @patch('ai_candidate_generator.os.path.exists')
    def test_initialization_file_not_found(self, mock_exists):
        """Test initialization failure when file is missing."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            AICandidateGenerator()

    @patch('ai_candidate_generator.pd.read_excel')
    @patch('ai_candidate_generator.os.path.exists')
    @patch('ai_candidate_generator.SentenceTransformer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_load_embeddings_cache_hit(self, mock_pickle_load, mock_file, mock_transformer, mock_exists, mock_read_excel):
        """Test loading embeddings from cache."""
        # Both exist
        mock_exists.return_value = True
        mock_read_excel.return_value = self.df.copy()
        
        # Mock cached data matching dataframe length
        mock_embeddings = np.random.rand(3, 384)
        mock_pickle_load.return_value = mock_embeddings
        
        generator = AICandidateGenerator()
        
        self.assertTrue(np.array_equal(generator.embeddings, mock_embeddings))
        # Ensure model.encode was NOT called since cache was hit
        generator.model.encode.assert_not_called()

    @patch('ai_candidate_generator.pd.read_excel')
    @patch('ai_candidate_generator.os.path.exists')
    @patch('ai_candidate_generator.SentenceTransformer')
    @patch('pickle.dump')
    def test_search_candidates_budget_filter(self, mock_dump, mock_transformer, mock_exists, mock_read_excel):
        """Test filtering by budget."""
        # Excel exists, Cache does NOT (to avoid pickle issues)
        def exists_side_effect(path):
            if path.endswith('.xlsx'): return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        mock_read_excel.return_value = self.df.copy()
        
        # Data for init
        mock_transformer.return_value.encode.return_value = np.zeros((3, 10))

        generator = AICandidateGenerator()
        
        # Setup specific embeddings for search if needed, but init already set them.
        # We need mock_transformer to return vector for the QUERY now.
        # The generator.model is the mock_transformer instance.
        # Logic: generator.model.encode([query])
        
        # We need to distinguish between init call (corpus) and search call (query)
        # But for 'budget_filter', search uses embeddings already in self.embeddings.
        # The query embedding is just used for scoring.
        
        generator.embeddings = np.zeros((3, 10)) 
        generator.model.encode.return_value = np.zeros((1, 10))
        
        # Set preferences
        generator.preferences['free_text_input'] = "something"
        generator.preferences['budget_max'] = 160 # Should exclude Pyramids (200)
        
        results = generator.search_candidates()
        
        self.assertEqual(len(results), 2)
        names = results['Name'].tolist()
        self.assertIn('Cairo Tower', names)
        self.assertIn('Museum', names)
        self.assertNotIn('Pyramids', names)

    @patch('ai_candidate_generator.pd.read_excel')
    @patch('ai_candidate_generator.os.path.exists')
    @patch('ai_candidate_generator.SentenceTransformer')
    @patch('builtins.input')
    @patch('pickle.dump')
    def test_collect_input_interactive(self, mock_dump, mock_input, mock_transformer, mock_exists, mock_read_excel):
        """Test interactive input collection."""
        def exists_side_effect(path):
            if path.endswith('.xlsx'): return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        mock_read_excel.return_value = self.df.copy()
        mock_transformer.return_value.encode.return_value = np.zeros((3, 10))
        
        # inputs: 
        # 1. free text
        # 2. budget
        # 3. location input
        # 4. radius
        mock_input.side_effect = ["Historical tour", "500", "Cairo Tower", "5"]
        
        generator = AICandidateGenerator()
        generator.collect_input_interactive()
        
        self.assertEqual(generator.preferences['free_text_input'], "Historical tour")
        self.assertEqual(generator.preferences['budget_max'], 500.0)
        self.assertEqual(generator.preferences['geo_center'], (30.0444, 31.2357)) # Cords of Cairo Tower
        self.assertEqual(generator.preferences['geo_radius_km'], 5.0)

    @patch('ai_candidate_generator.pd.read_excel')
    @patch('ai_candidate_generator.os.path.exists')
    @patch('ai_candidate_generator.SentenceTransformer')
    @patch('pickle.dump')
    def test_search_candidates_geo_filter(self, mock_dump, mock_transformer, mock_exists, mock_read_excel):
        """Test filtering by location radius."""
        def exists_side_effect(path):
            if path.endswith('.xlsx'): return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        mock_read_excel.return_value = self.df.copy()
        mock_transformer.return_value.encode.return_value = np.zeros((3, 10))
        
        generator = AICandidateGenerator()
        generator.embeddings = np.zeros((3, 10))
        generator.model.encode.return_value = np.zeros((1, 10))
        
        # Center at Cairo Tower
        generator.preferences['geo_center'] = (30.0444, 31.2357)
        generator.preferences['geo_radius_km'] = 1.0 # Very small radius
        
        # Museum is nearby (~300m), Pyramids are far (~12km)
        
        results = generator.search_candidates()
        
        names = results['Name'].tolist()
        self.assertIn('Cairo Tower', names) # Distance 0
        self.assertIn('Museum', names)      # Nearby
        self.assertNotIn('Pyramids', names) # Far away

if __name__ == '__main__':
    unittest.main()
