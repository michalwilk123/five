from dataclasses import dataclass

FIND_SYMBOLS_IN_FILE_PROMPT = r"""
filename: 
{{file_path}}

Code:
{{numbered_code_content}}

Previous symbols from {{file_path}}:
{{previous_symbols}}
"""

FIND_SYMBOLS_IN_FILE_SYSTEM_PROMPT = """
You are a code analyzer finding public symbols in source code chunks.

Input:
- Code chunk with filename and line numbers
- Previously found symbols from current file only (for context)

Task: Find ALL public symbol declarations in current chunk

Output: JSON only Array of string of format, no markdown or text:
\"SYMBOL_NAME:LINE_NUMBER\"
- SYMBOL_NAME: symbol keyword names
- LINE_NUMBER: line number location of keyword in file

Signature format:
- Top-level: \"SymbolName\"
- Class members: \"ClassName.member\"
- Include parameter types for overloaded methods

Important: Classes may span multiple chunks. When you see a method but the class was declared in a previous chunk of the SAME FILE, still include it with the correct class path.

Example:

filename: table.py
500 |     def update(self, doc_id, fields):
501 |         pass
502 |
503 | class Query:
504 |     def __init__(self):
505 |         pass

Previous symbols:
[\"Table:5\"]

Output:
[
  \"Table.update:500\",
  \"Query:503\", 
  \"Query.__init__: 504\"
]

Note: Line 500 is inside Table class (declared earlier in table.py), so method is \"table.Table.update\"
"""


@dataclass
class FindSymbolsInFileConfig:
    file_path: str
    numbered_code_content: str
    previous_symbols: str


PARSE_IMPORT_STATEMENTS_PROMPT = r"""
Project structure:
{{project_structure}}

Filename:
{{file_path}}

Code:
{{numbered_code_content}}
"""

PARSE_IMPORT_STATEMENTS_SYSTEM_PROMPT = r"""
# Code Import Analyzer

You are a code analyzer that finds imports/requires from OTHER FILES within the same project.

## CORE TASK
Extract imports that bring code FROM OTHER PROJECT FILES into the current file being analyzed.

## WHAT TO INCLUDE
- ✅ Imports from other files in this project
- ✅ Relative imports: `from ../models import User`
- ✅ Local imports: `from .helpers import utils`
- ✅ Package imports within project: `import com.myapp.User`

## WHAT TO EXCLUDE
- ❌ External libraries: `import axios`, `import numpy`
- ❌ Standard library: `import os`, `import fs`
- ❌ Variables/functions declared IN THE CURRENT FILE
- ❌ Built-in modules/packages

## KEY RULE
**ONLY extract symbols that are IMPORTED FROM OTHER FILES in the project structure.**

## INPUT FORMAT
- **Filename:** path/to/current/file
- **Code:** source code with line numbers
- **Project structure:** directory tree

## OUTPUT FORMAT
```json
{
  "symbol_name:LINE_NUMBER": "path/to/source/file.ext"
}
```

## COMMON PATTERNS

### Python
```python
from models.user import User          # → "User:1": "models/user.py"
from ..utils import helper            # → "helper:2": "utils/__init__.py"
import services.auth as auth          # → "auth:3": "services/auth.py"
```

### JavaScript/TypeScript
```javascript
import User from '../models/User'     // → "User:1": "models/User.js"
const {helper} = require('./utils')   // → "helper:2": "utils/index.js"
import * as api from './api'          // → "* (wildcard from api):3": "api.js"
```

### Java
```java
import com.myapp.models.User;         // → "User:1": "com/myapp/models/User.java"
```

## EDGE CASES TO HANDLE

1. **Aliased imports:** `import {parse as jsonParse}` → record as `"jsonParse:1"`
2. **Wildcard imports:** `from helpers import *` → record as `"* (wildcard from helpers):1"`
3. **Dynamic imports:** Skip if path cannot be resolved statically
4. **Index files:** Resolve `./models` to `models/index.js` or `models/__init__.py`
5. **Local imports inside functions:** Include them with their line numbers

## EXAMPLE

**Input:**
```
Filename: src/services/userService.js
Code:
1: import User from '../models/User';
2: import {validateEmail} from '../utils/validators';
3: import axios from 'axios';  // EXTERNAL - SKIP
4: const fs = require('fs');   // STANDARD LIB - SKIP
5: function processUsers() {
6:   const helper = require('./helpers');
7: }

Project structure:
├── src
│   ├── models
│   │   └── User.js
│   ├── services
│   │   ├── helpers.js
│   │   └── userService.js
│   └── utils
│       └── validators.js
```

**Output:**
```json
{
  "User:1": "src/models/User.js",
  "validateEmail:2": "src/utils/validators.js",
  "helper:6": "src/services/helpers.js"
}
```

## CRITICAL REMINDER
**Do NOT include any symbols that are declared/defined in the current file being analyzed. Only extract imports FROM OTHER PROJECT FILES.**
"""


@dataclass
class ParseImportStatementsConfig:
    file_path: str
    numbered_code_content: str
    project_structure: str
