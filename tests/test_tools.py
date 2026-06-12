import sys
import os
import unittest

# Add root folder to sys.path to resolve backend imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent.tools import _query_mock_database, discover_movies

class TestMovieAgentTools(unittest.TestCase):
    def test_mock_db_genre_filter(self):
        """Test filtering the mock database by genre."""
        results = _query_mock_database(genre="Horror", start_year=None, end_year=None, certification=None, watch_provider=None)
        self.assertTrue(len(results) > 0, "Should return at least one horror movie")
        for m in results:
            self.assertIn("Horror", m["genres"])
            
    def test_mock_db_year_filter(self):
        """Test filtering the mock database by release year range (90s)."""
        results = _query_mock_database(genre=None, start_year=1990, end_year=1999, certification=None, watch_provider=None)
        self.assertTrue(len(results) > 0, "Should return at least one 90s movie")
        for m in results:
            year = int(m["release_date"][:4])
            self.assertTrue(1990 <= year <= 1999, f"Movie year {year} should be between 1990 and 1999")
            
    def test_mock_db_certification_filter(self):
        """Test filtering the mock database by age rating certification."""
        results = _query_mock_database(genre=None, start_year=None, end_year=None, certification="R", watch_provider=None)
        self.assertTrue(len(results) > 0, "Should return at least one R-rated movie")
        for m in results:
            self.assertEqual(m["certification"], "R", "Movie certification should be R")
            
    def test_tool_json_parsing(self):
        """Test that the discover_movies tool handles JSON string inputs correctly."""
        result_str = discover_movies.invoke('{"genre": "Horror", "start_year": 1990, "end_year": 1999, "certification": "R"}')
        self.assertIn("Scream", result_str, "Scream should be found in the results")
        self.assertIn("The Silence of the Lambs", result_str, "The Silence of the Lambs should be found in the results")

if __name__ == "__main__":
    unittest.main()
