from flang.structures import LexicalAnalysisPattern, LexicalAnalysisPatternStorage

VNAME = r"[A-Za-z]\w*"
INTEGER = r"([1-9][0-9]+)|[0-9]"
NUMBER = r"-?(([1-9]+\d*)|0)(\.\d*)?"
WHITESPACE = r"\s"
STRING = r'(?<!\\)(?:\\{2})*"(?:(?<!\\)(?:\\{2})*\\"|[^"])+(?<!\\)(?:\\{2})*"'
C_FUNCTION_CALL = rf"{VNAME}\({VNAME}(,\s*)?\)"
XML_ATTR = rf'{VNAME}="[^"\n]*"'
XML_OPEN_TAG = rf"<{VNAME}({WHITESPACE}*{XML_ATTR})*>"
XML_CLOSE_TAG = rf"</{VNAME}>"
XML_SINGLE_TAG = rf"<{VNAME}({WHITESPACE}*{XML_ATTR})*{WHITESPACE}*/>"
WSPACE = r"\s+"
XML_CONTENT_CHAR = "[^<>]"
ANY = ".|\n"

VNamePattern = LexicalAnalysisPattern(
    "VNAME", VNAME, ["variable", "funcName", "snake_case_name", "world"]
)
IntegerPattern = LexicalAnalysisPattern("INTEGER", INTEGER, ["123", "10", "2"])
NumberPattern = LexicalAnalysisPattern("NUMBER", NUMBER, ["1.23", "0.5", "10.0"])
WhitespacePattern = LexicalAnalysisPattern("whitespace", WHITESPACE, [" ", "\n"])
StringPattern = LexicalAnalysisPattern(
    "STRING",
    STRING,
    ['"foo"', '"bar"', '"hello world"'],
)
CFunctionCallPattern = LexicalAnalysisPattern(
    "C_FUNCTION_CALL", C_FUNCTION_CALL, ["main(args)"]
)
XmlAttrPattern = LexicalAnalysisPattern(
    "XML_ATTR", XML_ATTR, ['name="value"', 'variant="file"']
)
XmlOpenTagPattern = LexicalAnalysisPattern(
    "XML_OPEN_TAG", XML_OPEN_TAG, ["<html>", "<h1>"]
)
XmlCloseTagPattern = LexicalAnalysisPattern(
    "XML_CLOSE_TAG", XML_CLOSE_TAG, ["</body>", "</div>"]
)
XmlSingleTagPattern = LexicalAnalysisPattern(
    "XML_SINGLE_TAG", XML_SINGLE_TAG, ["<href/>", "<br/>"]
)
WspacePattern = LexicalAnalysisPattern("WSPACE", WSPACE, [" ", "\n", "  "])
XmlContentCharPattern = LexicalAnalysisPattern(
    "XML_CONTENT_CHAR", XML_CONTENT_CHAR, ["a", "b", " ", "c", "1", "2"]
)
AnyPattern = LexicalAnalysisPattern(
    "ANY", ANY, ["a", "b", " ", "c", "1", "2", "<", ".", ">", "\n"]
)

lex_storage = LexicalAnalysisPatternStorage(
    [
        WspacePattern,
        XmlSingleTagPattern,
        XmlCloseTagPattern,
        XmlOpenTagPattern,
        XmlAttrPattern,
        CFunctionCallPattern,
        StringPattern,
        NumberPattern,
        WhitespacePattern,
        IntegerPattern,
        VNamePattern,
        XmlContentCharPattern,
        AnyPattern,
    ]
)
