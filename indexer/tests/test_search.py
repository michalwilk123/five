import time
import unittest

from indexer.search import (
    BackgroundSearch,
    _matches_regex,
)
from indexer.utils import IndexConfig, SymbolDeclaration, SymbolType, SymbolScope


class TestSearchPerformance(unittest.TestCase):
    def setUp(self):
        self.config = self.create_test_config(1000)

    def create_test_config(self, num_symbols: int = 1000) -> IndexConfig:
        symbols = []
        for i in range(num_symbols):
            symbol_type = (
                SymbolType.FUNCTION
                if i % 3 == 0
                else SymbolType.CLASS
                if i % 3 == 1
                else SymbolType.CONSTANT
            )
            symbols.append(
                SymbolDeclaration(
                    name=f"test_symbol_{i}_very_long_name_for_testing",
                    file_path=f"/path/to/file_{i}.py",
                    line_number=i + 1,
                    symbol_type=symbol_type,
                    scope=SymbolScope.GLOBAL,
                )
            )

        return IndexConfig(
            symbols=symbols,
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01",
        )

    def test_matches_regex(self):
        self.assertTrue(_matches_regex("", "anything"))
        self.assertTrue(_matches_regex("test", "test_symbol"))
        self.assertTrue(_matches_regex("test.*", "test_symbol"))
        self.assertTrue(_matches_regex("symbol.*", "test_symbol"))
        self.assertFalse(_matches_regex("nonexistent", "test_symbol"))
        self.assertTrue(_matches_regex("TEST", "test_symbol", case_sensitive=False))
        self.assertFalse(_matches_regex("TEST", "test_symbol", case_sensitive=True))
        self.assertTrue(_matches_regex("\\d+", "test_symbol_123"))
        self.assertFalse(_matches_regex("\\d+", "test_symbol"))

    def test_matches_regex_invalid_pattern(self):
        self.assertFalse(_matches_regex("[invalid", "test"))


class TestBackgroundSearch(unittest.TestCase):
    def setUp(self):
        self.config = self.create_test_config(1000)
        self.search = BackgroundSearch(self.config)

    def create_test_config(self, num_symbols: int = 1000) -> IndexConfig:
        symbols = []
        for i in range(num_symbols):
            symbol_type = (
                SymbolType.FUNCTION
                if i % 3 == 0
                else SymbolType.CLASS
                if i % 3 == 1
                else SymbolType.CONSTANT
            )
            symbols.append(
                SymbolDeclaration(
                    name=f"test_symbol_{i}_very_long_name_for_testing",
                    file_path=f"/path/to/file_{i}.py",
                    line_number=i + 1,
                    symbol_type=symbol_type,
                    scope=SymbolScope.GLOBAL,
                )
            )

        return IndexConfig(
            symbols=symbols,
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01",
        )

    def test_background_search_start_and_cancel(self):
        callback_called = False
        results_received = []

        def callback(results):
            nonlocal callback_called
            callback_called = True
            results_received.extend(results)

        self.search.start_search(
            symbol_query="test", max_results=20, batch_size=100, callback=callback
        )

        time.sleep(0.2)

        if self.search.is_running():
            self.search.cancel()
            time.sleep(0.1)
            self.assertFalse(self.search.is_running())

        self.assertTrue(callback_called or len(results_received) > 0)

    def test_background_search_completion(self):
        results_received = []

        def callback(results):
            results_received.extend(results)

        self.search.start_search(
            symbol_query="test_symbol_0",
            max_results=10,
            batch_size=50,
            callback=callback,
        )

        while self.search.is_running():
            time.sleep(0.1)

        self.assertFalse(self.search.is_running())
        self.assertGreater(len(results_received), 0)

        for result in results_received:
            self.assertEqual(result.combined_score, 1.0)
            self.assertEqual(result.symbol_score, 1.0)

    def test_background_search_regex_patterns(self):
        results_received = []

        def callback(results):
            results_received.extend(results)

        self.search.start_search(
            symbol_query="test_symbol_\\d+",
            max_results=10,
            batch_size=50,
            callback=callback,
        )

        while self.search.is_running():
            time.sleep(0.1)

        self.assertFalse(self.search.is_running())
        self.assertGreater(len(results_received), 0)

        for result in results_received:
            self.assertTrue("test_symbol_" in result.symbol.name)

    def test_background_search_empty_config(self):
        empty_config = IndexConfig(
            symbols=[],
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01",
        )

        search = BackgroundSearch(empty_config)
        callback_called = False

        def callback(results):
            nonlocal callback_called
            callback_called = True

        search.start_search(symbol_query="test", callback=callback)

        time.sleep(0.2)

        self.assertFalse(search.is_running())

    def test_background_search_multiple_starts(self):
        callback_count = 0

        def callback(results):
            nonlocal callback_count
            callback_count += 1

        self.search.start_search(symbol_query="test", callback=callback)
        time.sleep(0.05)

        self.search.start_search(symbol_query="symbol", callback=callback)

        while self.search.is_running():
            time.sleep(0.1)

        self.assertFalse(self.search.is_running())
        self.assertGreater(callback_count, 0)


if __name__ == "__main__":
    unittest.main()
