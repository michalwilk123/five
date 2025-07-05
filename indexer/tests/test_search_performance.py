import unittest
import time

from indexer.utils import IndexConfig, SymbolDeclaration, SymbolType
from indexer.search import (
    BackgroundSearch,
    _should_skip_by_length,
    _calculate_similarity,
    _calculate_combined_score
)


class TestSearchPerformance(unittest.TestCase):
    
    def setUp(self):
        self.config = self.create_test_config(1000)
    
    def create_test_config(self, num_symbols: int = 1000) -> IndexConfig:
        symbols = []
        for i in range(num_symbols):
            symbol_type = SymbolType.FUNCTION if i % 3 == 0 else SymbolType.CLASS if i % 3 == 1 else SymbolType.CONSTANT
            symbols.append(SymbolDeclaration(
                name=f"test_symbol_{i}_very_long_name_for_testing",
                file_path=f"/path/to/file_{i}.py",
                line_number=i + 1,
                symbol_type=symbol_type
            ))
        
        return IndexConfig(
            symbols=symbols,
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01"
        )
    
    def test_should_skip_by_length(self):
        self.assertFalse(_should_skip_by_length("", "short"))
        self.assertFalse(_should_skip_by_length("short", "longer_symbol"))
        self.assertTrue(_should_skip_by_length("very_long_query", "short"))
        self.assertFalse(_should_skip_by_length("exact", "exact"))
    
    def test_calculate_similarity(self):
        self.assertEqual(_calculate_similarity("", "anything"), 0.0)
        self.assertEqual(_calculate_similarity("query", ""), 0.0)
        self.assertEqual(_calculate_similarity("test", "test_symbol"), 1.0)
        self.assertGreater(_calculate_similarity("test", "best"), 0.0)
        self.assertLess(_calculate_similarity("test", "different"), 1.0)
    

class TestBackgroundSearch(unittest.TestCase):
    
    def setUp(self):
        self.config = self.create_test_config(1000)
        self.search = BackgroundSearch(self.config)
    
    def create_test_config(self, num_symbols: int = 1000) -> IndexConfig:
        symbols = []
        for i in range(num_symbols):
            symbol_type = SymbolType.FUNCTION if i % 3 == 0 else SymbolType.CLASS if i % 3 == 1 else SymbolType.CONSTANT
            symbols.append(SymbolDeclaration(
                name=f"test_symbol_{i}_very_long_name_for_testing",
                file_path=f"/path/to/file_{i}.py",
                line_number=i + 1,
                symbol_type=symbol_type
            ))
        
        return IndexConfig(
            symbols=symbols,
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01"
        )
    
    def test_background_search_start_and_cancel(self):
        callback_called = False
        results_received = []
        
        def callback(results):
            nonlocal callback_called
            callback_called = True
            results_received.extend(results)
        
        self.search.start_search(
            symbol_query="test",
            max_results=20,
            batch_size=100,
            callback=callback
        )
        
        # Wait a bit for the search to start and potentially complete
        time.sleep(0.2)
        
        # Search might have completed already, so check if it's running or has results
        if self.search.is_running():
            self.search.cancel()
            time.sleep(0.1)
            self.assertFalse(self.search.is_running())
        
        # Should have either called callback or received results
        self.assertTrue(callback_called or len(results_received) > 0)
    
    def test_background_search_completion(self):
        results_received = []
        
        def callback(results):
            results_received.extend(results)
        
        self.search.start_search(
            symbol_query="test_symbol_0",
            max_results=10,
            batch_size=50,
            callback=callback
        )
        
        # Wait for completion
        while self.search.is_running():
            time.sleep(0.1)
        
        self.assertFalse(self.search.is_running())
        self.assertGreater(len(results_received), 0)
        
        # Check that results are sorted
        for i in range(len(results_received) - 1):
            self.assertGreaterEqual(
                results_received[i].combined_score,
                results_received[i + 1].combined_score
            )
    
    def test_background_search_empty_config(self):
        empty_config = IndexConfig(
            symbols=[],
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01"
        )
        
        search = BackgroundSearch(empty_config)
        callback_called = False
        
        def callback(results):
            nonlocal callback_called
            callback_called = True
        
        search.start_search(symbol_query="test", callback=callback)
        
        # Wait for completion
        time.sleep(0.2)
        
        self.assertFalse(search.is_running())
        # With empty config, callback might not be called, which is acceptable
        # Just ensure search is not running
    
    def test_background_search_multiple_starts(self):
        callback_count = 0
        
        def callback(results):
            nonlocal callback_count
            callback_count += 1
        
        # Start first search
        self.search.start_search(symbol_query="test", callback=callback)
        time.sleep(0.05)
        
        # Start second search (should cancel first)
        self.search.start_search(symbol_query="symbol", callback=callback)
        
        # Wait for completion
        while self.search.is_running():
            time.sleep(0.1)
        
        self.assertFalse(self.search.is_running())
        self.assertGreater(callback_count, 0)


if __name__ == '__main__':
    unittest.main() 