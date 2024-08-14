VNAME = r"[A-Za-z]\w*"
NUMBER = r"-?(([1-9]+\d*)|0)(\.\d*)?"
STRING = r'(?<!\\)(?:\\{2})*"(?:(?<!\\)(?:\\{2})*\\"|[^"])+(?<!\\)(?:\\{2})*"'
C_FUNCTION_CALL = rf"{VNAME}\({VNAME}(,\s*)?\)"
XML_ATTR = rf'{VNAME}="[^"\n]*"'
XML_OPEN_TAG = rf"<{VNAME}(\s*{XML_ATTR})*>"
XML_CLOSE_TAG = rf"</{VNAME}>"
XML_SINGLE_TAG = rf"<{VNAME}(\s*{XML_ATTR})*\s*/>"
