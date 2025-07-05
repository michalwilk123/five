from difflib import SequenceMatcher
from threading import Thread, Event
from typing import Callable

from .utils import IndexConfig, SymbolDeclaration, SearchResult


def _calculate_similarity(query: str, text: str) -> float:
    if not query or not text:
        return 0.0
    
    is_case_insensitive = query.islower()
    
    if is_case_insensitive:
        query_normalized = query.lower()
        text_normalized = text.lower()
    else:
        query_normalized = query
        text_normalized = text
    
    if query_normalized in text_normalized:
        return 1.0
    
    if len(query_normalized) > len(text_normalized):
        return 0.0
    
    matcher = SequenceMatcher(None, query_normalized, text_normalized)
    matches = matcher.get_matching_blocks()
    
    total_matched = sum(size for _, _, size in matches)
    if total_matched == 0:
        return 0.0
    
    query_length = len(query_normalized)
    text_length = len(text_normalized)
    
    if total_matched == query_length:
        return 1.0
    
    match_ratio = total_matched / query_length
    
    penalty = 0.0
    for i, j, size in matches:
        if size > 0:
            penalty += (i + j) * 0.1
    
    final_score = match_ratio - penalty / max(query_length, text_length)
    return max(0.0, final_score)


def _calculate_combined_score(symbol_score: float, file_score: float) -> float:
    return symbol_score + file_score / 10


def _should_skip_by_length(query: str, symbol_name: str) -> bool:
    if not query:
        return False
    return len(query) > len(symbol_name)


def _search_symbols_core(
    symbols: list[SymbolDeclaration],
    symbol_query: str,
    filepath_query: str,
    max_results: int = 50,
    should_cancel: Callable | None = None,
    batch_callback: Callable | None = None,
    batch_size: int = 1000
) -> list[SearchResult]:
    if not symbols or (not symbol_query and not filepath_query):
        return []
    
    exact_matches = []
    partial_matches = []
    
    for i, symbol in enumerate(symbols):
        if should_cancel and should_cancel():
            break
            
        if _should_skip_by_length(symbol_query, symbol.name):
            continue
            
        symbol_score = symbol_query and _calculate_similarity(symbol_query, symbol.name) or 0.0
        file_score = filepath_query and _calculate_similarity(filepath_query, symbol.file_path) or 0.0

        combined_score = _calculate_combined_score(symbol_score, file_score)
        
        if symbol_score > 0.7:
            symbol_index = symbols.index(symbol)
            result = SearchResult(
                symbol=symbol,
                symbol_index=symbol_index,
                symbol_score=symbol_score,
                file_score=file_score,
                combined_score=combined_score
            )
            
            if symbol_score == 1.0:
                exact_matches.append(result)
            else:
                partial_matches.append(result)
            
            if len(exact_matches) + len(partial_matches) >= max_results:
                break
        
        if batch_callback and i % batch_size == 0 and (exact_matches or partial_matches):
            batch_results = _get_sorted_results(exact_matches, partial_matches, max_results)
            batch_callback(batch_results)
    
    return _get_sorted_results(exact_matches, partial_matches, max_results)


def _get_sorted_results(
    exact_matches: list[SearchResult], 
    partial_matches: list[SearchResult], 
    max_results: int
) -> list[SearchResult]:
    exact_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
    partial_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
    return (exact_matches + partial_matches)[:max_results]


def _search_symbols(
    symbols: list[SymbolDeclaration],
    symbol_query: str = "",
    filepath_query: str = "",
    max_results: int = 50
) -> list[SearchResult]:
    return _search_symbols_core(symbols, symbol_query, filepath_query, max_results)


def fuzzy_search_symbols(
    config: IndexConfig,
    symbol_query: str = "",
    filepath_query: str = "",
    max_results: int = 50
) -> list[SearchResult]:
    return _search_symbols(config.symbols, symbol_query, filepath_query, max_results)


class BackgroundSearch:
    def __init__(self, config: IndexConfig):
        self.config = config
        self._cancel_event = Event()
        self._thread: (Thread | None) = None
        self._is_running = False
    
    def start_search(
        self,
        symbol_query: str = "",
        filepath_query: str = "",
        max_results: int = 50,
        batch_size: int = 1000,
        callback: Callable | None = None
    ) -> None:
        if self._is_running:
            self.cancel()
        
        self._cancel_event.clear()
        self._is_running = True
        self._thread = Thread(
            target=self._search_worker,
            args=(symbol_query, filepath_query, max_results, batch_size, callback)
        )
        self._thread.daemon = True
        self._thread.start()
    
    def _search_worker(
        self,
        symbol_query: str,
        filepath_query: str,
        max_results: int,
        batch_size: int,
        callback: Callable | None
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
            batch_size
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

