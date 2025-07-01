from pprint import pformat

from prompt_engineering.connection import (
    LITE_MODEL,
    MEDIUM_MODEL,
    LanguageModelQuery,
    execute_prompt,
    prepare_prompt,
)
from prompt_engineering.templates.indexer.prompts import (
    FIND_SYMBOLS_IN_FILE_PROMPT,
    FIND_SYMBOLS_IN_FILE_SYSTEM_PROMPT,
    PARSE_IMPORT_STATEMENTS_PROMPT,
    PARSE_IMPORT_STATEMENTS_SYSTEM_PROMPT,
    FindSymbolsInFileConfig,
    ParseImportStatementsConfig,
)

logfile = "logs_indexer.txt"


def prompt_parse_import_statements(config: ParseImportStatementsConfig):
    prompt = prepare_prompt(PARSE_IMPORT_STATEMENTS_PROMPT, config)
    system_prompt = PARSE_IMPORT_STATEMENTS_SYSTEM_PROMPT
    llm_query = LanguageModelQuery(
        prompt=prompt,
        system_prompt=system_prompt,
        model_name=MEDIUM_MODEL,
    )

    return execute_prompt(llm_query)


def prompt_find_symbols_in_file(config: FindSymbolsInFileConfig):
    prompt = prepare_prompt(FIND_SYMBOLS_IN_FILE_PROMPT, config)
    system_prompt = FIND_SYMBOLS_IN_FILE_SYSTEM_PROMPT
    llm_query = LanguageModelQuery(
        prompt=prompt,
        system_prompt=system_prompt,
        model_name=MEDIUM_MODEL,
    )

    with open(logfile, "a") as f:
        f.write("Prompt:\n")
        f.write(llm_query.prompt)
        f.write("\nSystem prompt:\n")
        f.write(llm_query.system_prompt)
        f.write("\nModel:\n")
        f.write(llm_query.model_name)
        f.write("\n===================\n")

    return execute_prompt(llm_query)
