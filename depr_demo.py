import json

import tqdm
from five_persistance.core import (
    get_symbol_declarations_db,
    get_symbol_file_locations_db,
)

from indexer.files import (
    create_chunk_with_line_numbers,
    get_file_chunks,
    get_project_structure,
)
from prompt_engineering.templates.indexer.prompts import (
    FindSymbolsInFileConfig,
    ParseImportStatementsConfig,
)
from prompt_engineering.templates.indexer.setup import (
    prompt_find_symbols_in_file,
    prompt_parse_import_statements,
)


def process_definitions_tinydb():
    chunks = get_file_chunks("test_repositories/tinydb")
    previous_file = None
    symbols = {}
    locations = {}

    for i, (file_path, start_line, chunk_content) in tqdm.tqdm(enumerate(chunks)):
        if file_path != previous_file:
            previous_symbols = []
            previous_file = file_path

        config = FindSymbolsInFileConfig(
            file_path=file_path,
            numbered_code_content=create_chunk_with_line_numbers(
                chunk_content, start_line
            ),
            previous_symbols=str(previous_symbols),
        )
        tqdm.tqdm.write(f"Filename: {file_path} Line start: {start_line} chunk: {i}")
        results: list[str] = prompt_find_symbols_in_file(config)

        config_path = "test_repositories/tinydb/.five"
        with (
            get_symbol_declarations_db(config_path) as symbol_declarations_db,
            get_symbol_file_locations_db(config_path) as file_locations_db,
        ):
            for symbol in results:
                symbol_name, line_number = symbol.split(":")
                key = f"{file_path}:{symbol_name}"

                if key not in locations:
                    file_locations_db[key] = [int(line_number)]
                    locations[key] = [int(line_number)]
                else:
                    existing_lines = file_locations_db[key] + [int(line_number)]
                    file_locations_db[key] = sorted(list(set(existing_lines)))

                    locations[key] = sorted(
                        list(set(locations[key] + [int(line_number)]))
                    )

                symbol_declarations_db[key] = file_path
                symbols[key] = file_path

        previous_symbols.extend(results)

    with open("symbols.jsonl", "w") as f:
        f.write(json.dumps(symbols, indent=2))
        f.write("\n\n")
        f.write(json.dumps(locations, indent=2))


def process_imports_tinydb():
    chunks = get_file_chunks("test_repositories/tinydb")
    previous_file = None

    for i, (file_path, start_line, chunk_content) in tqdm.tqdm(enumerate(chunks[:1])):
        if file_path != previous_file:
            previous_symbols = []
            previous_file = file_path

        config = ParseImportStatementsConfig(
            file_path=file_path,
            numbered_code_content=create_chunk_with_line_numbers(
                chunk_content, start_line
            ),
            project_structure=get_project_structure("test_repositories/tinydb"),
        )
        tqdm.tqdm.write(f"Filename: {file_path} Line start: {start_line} chunk: {i}")
        results: list[str] = prompt_parse_import_statements(config)

        config_path = "test_repositories/tinydb/.five"
        with (
            get_symbol_declarations_db(config_path) as symbol_declarations_db,
            get_symbol_file_locations_db(config_path) as file_locations_db,
        ):
            for symbol in results:
                symbol_name, line_number = symbol.split(":")
                print("SYMBOL:", symbol_name, line_number)
                key = f"{file_path}:{symbol_name}"

                if key not in file_locations_db:
                    file_locations_db[key] = [int(line_number)]
                else:
                    existing_lines = file_locations_db[key] + [int(line_number)]
                    file_locations_db[key] = sorted(list(set(existing_lines)))

                print("FILE LOCATIONS DB:", file_locations_db[key])
                symbol_declarations_db[key] = file_path

        previous_symbols.extend(results)


def resolve_imports_tinydb(): ...


if __name__ == "__main__":
    # chunks = get_file_chunks("test_repositories/tinydb", chunk_size=500, overlap=10)
    # print(create_chunk_with_line_numbers(chunks[19][2], chunks[19][1]))
    # print(create_chunk_with_line_numbers(chunks[20][2], chunks[20][1]))
    # print(chunks[19][2])
    # pass

    process_definitions_tinydb()
    # process_imports_tinydb()
