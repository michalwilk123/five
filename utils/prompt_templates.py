CREATE_INDEX_PROMPT = """
You are a semantic parser of code. Your responsibility is to find and index code objects from raw code files

{{OBJECT_DESCRIPTION}}

Create a BM25 search index for {{OBJECT_NAME}} that helps determine:
1. Whether an existing {{OBJECT_NAME}} should be used or deleted
2. What new {{OBJECT_NAME}} should be created if none match

Path: {{FILEPATH}}
File content:
```
{{LINE_NUMERATED_FILE_CONTENT}}
```
Given the numbered Python file, create an index entry for each {{OBJECT_NAME}} containing:
1. Language variations (Polish + English equivalents)
2. Identifiers in code  (variable/function/class name in code)
3. Conceptual keywords from both languages

Format as JSON ( output:[string, string, number, number][] ) [string_containing_search_terms, filepath, start_line_number, end_line_number]. 
Separate each index entry with a space
  
Return ONLY valid JSON
"""

SEARCH_INDEX_PROMPT = """
You are a query expansion assistant. Your responsibility is to expand a 
user query to include more relevant information based on the provided context.

{{OBJECT_DESCRIPTION}}

{{EXAMPLES}}

{{USER_INSTRUCTION}}
"""


def generate_prompt_with_args(prompt: str, prompt_kwargs: dict) -> str:
    for key, value in prompt_kwargs.items():
        prompt = prompt.replace("{{%s}}" % key, value)
    return prompt
