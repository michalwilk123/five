import os
import shutil

import bm25s

from common import get_last_commit_hash
from core.project_config import FiveProjectConfig
from utils.chatbot_controller import FiveChatbotController
from utils.project_tree_controller import FiveProjectTreeController
from utils.prompt_templates import (
    CREATE_INDEX_PROMPT,
    SEARCH_INDEX_PROMPT,
    generate_prompt_with_args,
)


class FiveProjectSearchEngine:
    # 1. Initialization & Configuration
    def __init__(
        self,
        config: FiveProjectConfig,
        project_tree_controller: FiveProjectTreeController,
        chatbot_controller: FiveChatbotController,
        overrides: bool,
    ):
        self.config: FiveProjectConfig = config
        self.project_tree_controller: FiveProjectTreeController = project_tree_controller
        self.chatbot: FiveChatbotController = chatbot_controller
        self.overrides: bool = overrides

    def _get_index_path(self, object_name: str) -> str:
        return os.path.join(
            self.project_tree_controller.project_location,
            ".five",
            object_name,
        )

    # 2. Core Passage Processing Utilities (Private Helpers)
    def _merge_search_terms(self, search_terms: list[str]) -> str:
        search_terms_merged = set()

        for search_term_string in search_terms:
            search_terms_merged.update(search_term_string.split())

        return " ".join(search_terms_merged)

    def _convert_passages_to_bm25_format(
        self, passages: list[tuple[str, str, int, int]]
    ) -> list[dict]:
        bm25_format = []

        for passage_data in passages:
            bm25_format.append(
                {
                    "text": passage_data[0],
                    "metadata": {
                        "filepath": passage_data[1],
                        "start_line_number": passage_data[2],
                        "end_line_number": passage_data[3],
                        "commit_hash": get_last_commit_hash(
                            self.project_tree_controller.project_location, passage_data[1]
                        ),
                    },
                }
            )
        return bm25_format

    def _conditionally_finalize_and_add_passage_block(
        self,
        merged_passages_list: list[tuple[str, str, int, int]],
        current_block_text_list: list[str],
        filepath: str | None,
        start_line: int,
        end_line: int
    ) -> None:
        """Helper to conditionally finalize a passage block and add it to the list of merged passages."""
        if current_block_text_list and filepath is not None:
            merged_text = self._merge_search_terms(current_block_text_list)
            merged_passages_list.append(
                (
                    merged_text,
                    filepath,
                    start_line,
                    end_line,
                )
            )

    def _merge_passages(
        self, passages: list[tuple[str, str, int, int]]
    ) -> list[tuple[str, str, int, int]]:
        if not passages:
            return []

        passages.sort(key=lambda x: (x[1], x[2]))

        merged_passages: list[tuple[str, str, int, int]] = []
        
        passage_list_for_current_block: list[str] = []
        current_block_start_line: int = 0
        current_block_end_line: int = -1
        current_block_filepath: str | None = None

        for passage_chunk in passages:
            (
                string_containing_search_terms,
                filepath,
                start_line_number,
                end_line_number,
            ) = passage_chunk

            if current_block_filepath == filepath and \
               start_line_number <= current_block_end_line:
                passage_list_for_current_block.append(string_containing_search_terms)
                current_block_end_line = max(current_block_end_line, end_line_number)
            else:
                self._conditionally_finalize_and_add_passage_block(
                    merged_passages,
                    passage_list_for_current_block,
                    current_block_filepath,
                    current_block_start_line,
                    current_block_end_line
                )
                
                passage_list_for_current_block = [string_containing_search_terms]
                current_block_start_line = start_line_number
                current_block_end_line = end_line_number
                current_block_filepath = filepath
        
        # Finalize the last accumulated block after the loop
        self._conditionally_finalize_and_add_passage_block(
            merged_passages,
            passage_list_for_current_block,
            current_block_filepath,
            current_block_start_line,
            current_block_end_line
        )
        return merged_passages

    # 3. BM25 Index Management (Core BM25 operations)
    def generate_bm25_index(self, object_name: str, passages_bm25_data: list[dict]):
        corpus_texts = [passage["text"] for passage in passages_bm25_data]
        if not corpus_texts:
            pass

        corpus_tokens = bm25s.tokenize(corpus_texts, stopwords="en")

        retriever = bm25s.BM25(corpus=passages_bm25_data)
        retriever.index(corpus_tokens)

        index_path = self._get_index_path(object_name)
        if self.overrides and os.path.exists(index_path):
            shutil.rmtree(index_path)

        if not os.path.exists(index_path):
            os.makedirs(index_path)

        retriever.save(index_path, corpus=passages_bm25_data)
        return retriever

    def create_retriever(self, object_name: str):
        index_path = self._get_index_path(object_name)
        return bm25s.BM25.load(index_path, load_corpus=True)

    # 4. Project Indexing Workflow
    def index_code_object(
        self, description: str, object_name: str, passages_input: list[tuple[str, str]]
    ) -> list[dict]:
        chatbot_generated_passages: list[tuple[str, str, int, int]] = []
        for file_path, passage_content in passages_input:
            prompt = generate_prompt_with_args(
                CREATE_INDEX_PROMPT,
                {
                    "OBJECT_DESCRIPTION": description,
                    "OBJECT_NAME": object_name,
                    "FILEPATH": file_path,
                    "LINE_NUMERATED_FILE_CONTENT": passage_content,
                },
            )
            response = self.chatbot.run(prompt, output_format="json")
            if isinstance(response, list):
                chatbot_generated_passages.extend(response) # type: ignore
            # else: handle cases where response is not a list or has unexpected format

        merged_passages = self._merge_passages(chatbot_generated_passages)
        passages_bm25 = self._convert_passages_to_bm25_format(merged_passages)
        return passages_bm25

    def index_project(self):
        for code_object_data in self.config.settings.objects:
            passages_bm25 = self.index_code_object(
                code_object_data.description,
                code_object_data.name,
                self.project_tree_controller.get_passages(code_object_data.globs),
            )
            if passages_bm25:
                self.generate_bm25_index(code_object_data.name, passages_bm25)

    # 5. Project Search/Retrieval Workflow
    def get_project_context(self, object_name: str, user_instruction: str):
        code_object_data = self.config.get_object_by_name(object_name)
        if not code_object_data:
            return []

        retriever = self.create_retriever(object_name)

        prompt = generate_prompt_with_args(
            SEARCH_INDEX_PROMPT,
            {
                "OBJECT_DESCRIPTION": code_object_data.description,
                "OBJECT_NAME": code_object_data.name,
                "EXAMPLES": "\n".join(code_object_data.examples[:2]),
                "USER_INSTRUCTION": user_instruction,
            },
        )
        response_terms = self.chatbot.run(prompt, output_format="string")
        results = retriever.retrieve(response_terms, k=3, return_as="documents")

        return results
