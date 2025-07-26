import re
from threading import Event, Thread
from typing import Callable

from .utils import IndexConfig, SearchResult, SymbolDeclaration


def _matches_regex(pattern: str, text: str, case_sensitive: bool = False) -> bool:
    if not pattern:
        return True

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        return bool(re.search(pattern, text, flags))
    except re.error:
        return False


def _search_symbols_core(
    symbols: list[SymbolDeclaration],
    symbol_query: str,
    filepath_query: str,
    max_results: int = 50,
    should_cancel: Callable | None = None,
    batch_callback: Callable | None = None,
    batch_size: int = 1000,
) -> list[SearchResult]:
    if not symbols:
        return []

    results = []

    for i, symbol in enumerate(symbols):
        if should_cancel and should_cancel():
            break

        symbol_matches = _matches_regex(symbol_query, symbol.name)
        file_matches = _matches_regex(filepath_query, symbol.file_path)

        if symbol_matches and file_matches:
            result = SearchResult(
                symbol=symbol,
                symbol_index=i,
                symbol_score=1.0 if symbol_matches else 0.0,
                file_score=1.0 if file_matches else 0.0,
                combined_score=1.0,
            )
            results.append(result)

            if len(results) >= max_results:
                break

        if batch_callback and i % batch_size == 0 and results:
            batch_callback(results[:max_results])

    return results[:max_results]


def _search_symbols(
    symbols: list[SymbolDeclaration],
    symbol_query: str = "",
    filepath_query: str = "",
    max_results: int = 50,
) -> list[SearchResult]:
    return _search_symbols_core(symbols, symbol_query, filepath_query, max_results)


def regex_search_symbols(
    config: IndexConfig,
    symbol_query: str = "",
    filepath_query: str = "",
    max_results: int = 50,
) -> list[SearchResult]:
    return _search_symbols(config.symbols, symbol_query, filepath_query, max_results)


class BackgroundSearch:
    def __init__(self, config: IndexConfig):
        self.config = config
        self._cancel_event = Event()
        self._thread: Thread | None = None
        self._is_running = False

    def start_search(
        self,
        symbol_query: str = "",
        filepath_query: str = "",
        max_results: int = 50,
        batch_size: int = 1000,
        callback: Callable | None = None,
    ) -> None:
        if self._is_running:
            self.cancel()

        self._cancel_event.clear()
        self._is_running = True
        self._thread = Thread(
            target=self._search_worker,
            args=(symbol_query, filepath_query, max_results, batch_size, callback),
        )
        self._thread.daemon = True
        self._thread.start()

    def _search_worker(
        self,
        symbol_query: str,
        filepath_query: str,
        max_results: int,
        batch_size: int,
        callback: Callable | None,
    ) -> None:
        if not self.config.symbols:
            self._is_running = False
            return

        def should_cancel() -> bool:
            return self._cancel_event.is_set()

        def batch_callback(results: list[SearchResult]) -> None:
            if callback and not self._cancel_event.is_set():
                callback(results)

        final_results = _search_symbols_core(
            self.config.symbols,
            symbol_query,
            filepath_query,
            max_results,
            should_cancel,
            batch_callback,
            batch_size,
        )

        if not self._cancel_event.is_set() and callback:
            callback(final_results)

        self._is_running = False

    def cancel(self) -> None:
        self._cancel_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running
