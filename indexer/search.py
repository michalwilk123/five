from difflib import SequenceMatcher
from threading import Thread, Event
from typing import Callable, Optional

from .utils import IndexConfig, SymbolDeclaration, SearchResult


def _calculate_similarity(query: str, text: str) -> float:
    if not query:
        return 1.0
    if not text:
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
    
    return SequenceMatcher(None, query_normalized, text_normalized).ratio()


def _calculate_combined_score(symbol_score: float, file_score: float) -> float:
    return symbol_score * 0.8 + file_score * 0.2


def _should_skip_by_length(query: str, symbol_name: str) -> bool:
    if not query:
        return False
    return len(query) > len(symbol_name)


def _search_symbols(
    symbols: list[SymbolDeclaration],
    symbol_query: str = "",
    filepath_query: str = "",
    max_results: int = 50
) -> list[SearchResult]:
    if not symbols:
        return []
    
    if not symbol_query and not filepath_query:
        return [SearchResult(symbol=s, symbol_score=1.0, file_score=1.0, combined_score=1.0) 
                for s in symbols[:max_results]]
    
    results = []
    exact_matches = []
    partial_matches = []
    
    for symbol in symbols:
        if _should_skip_by_length(symbol_query, symbol.name):
            continue
            
        symbol_score = _calculate_similarity(symbol_query, symbol.name)
        if symbol_score == 0:
            continue
            
        file_score = _calculate_similarity(filepath_query, symbol.file_path)
        combined_score = _calculate_combined_score(symbol_score, file_score)
        
        if symbol_score > 0.1 or (file_score > 0.3 and symbol_score > 0.05):
            result = SearchResult(
                symbol=symbol,
                symbol_score=symbol_score,
                file_score=file_score,
                combined_score=combined_score
            )
            
            if symbol_score == 1.0:
                exact_matches.append(result)
            else:
                partial_matches.append(result)
    
    exact_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
    partial_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
    
    results = exact_matches + partial_matches
    return results[:max_results]


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
        self._thread: Optional[Thread] = None
        self._is_running = False
    
    def start_search(
        self,
        symbol_query: str = "",
        filepath_query: str = "",
        max_results: int = 50,
        batch_size: int = 1000,
        callback: Optional[Callable[[list[SearchResult]], None]] = None
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
        callback: Optional[Callable[[list[SearchResult]], None]]
    ) -> None:
        if not self.config.symbols:
            self._is_running = False
            return
        
        results = []
        exact_matches = []
        partial_matches = []
        
        for i, symbol in enumerate(self.config.symbols):
            if self._cancel_event.is_set():
                break
                
            if _should_skip_by_length(symbol_query, symbol.name):
                continue
                
            symbol_score = _calculate_similarity(symbol_query, symbol.name)
            if symbol_score == 0:
                continue
                
            file_score = _calculate_similarity(filepath_query, symbol.file_path)
            combined_score = _calculate_combined_score(symbol_score, file_score)
            
            if symbol_score > 0.1 or (file_score > 0.3 and symbol_score > 0.05):
                result = SearchResult(
                    symbol=symbol,
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
            
            if i % batch_size == 0 and callback and (exact_matches or partial_matches):
                batch_results = self._get_sorted_results(exact_matches, partial_matches, max_results)
                callback(batch_results)
        
        if not self._cancel_event.is_set() and callback:
            final_results = self._get_sorted_results(exact_matches, partial_matches, max_results)
            callback(final_results)
        
        self._is_running = False
    
    def _get_sorted_results(
        self, 
        exact_matches: list[SearchResult], 
        partial_matches: list[SearchResult], 
        max_results: int
    ) -> list[SearchResult]:
        exact_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
        partial_matches.sort(key=lambda x: (-x.combined_score, -x.symbol_score, x.symbol.name))
        return (exact_matches + partial_matches)[:max_results]
    
    def cancel(self) -> None:
        self._cancel_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._is_running = False
    
    def is_running(self) -> bool:
        return self._is_running

