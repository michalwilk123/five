### SAMPLES
TEST_BASIC_SAMPLE = "hello world"
TEST_BASIC_SAMPLE_FAILURE_1 = "goodbye world"
TEST_BASIC_SAMPLE_FAILURE_2 = "hello cruel world"
TEST_CHOICE_NESTED_SAMPLE = r"""
Lorem ipsum, dolor sit amet...
end"""
TEST_OPTIONAL_SAMPLE_1 = "this is a number: 123"
TEST_OPTIONAL_SAMPLE_2 = 'this is a text: "some text"'
TEST_OPTIONAL_SAMPLE_3 = "this is a text: 111"
TEST_CHOICE_AND_MULTI_SAMPLE = """\
My name is Zoe.
My name is Tom.
My name is empty.
My name is some, other, things.
"""

TEST_SAMPLE_MULTI = """\
AAAAAAAAAAAA
AAA
AAAAAA
variable: somevalue;
variable: someothervalue;
"""

TEST_SAMPLE_RECURSIVE_1 = """\
<html>
foo
</html>\
"""

TEST_SAMPLE_RECURSIVE_2 = """\
<html>
<body><strong>some bolded text</strong></body>
</html>\
"""

TEST_SAMPLE_RECURSIVE_3 = """\
<html>
<head><link some="attribute">some link</link><link>some other link</link></head>
<body>
<script>console.log("hello")</script>
some <em>fancy</em> text
<div>
<div>
    nested
</div>
</div>
</body>
</html>\
"""

TEST_SAMPLE_TERMINAL_PARSING = """
<html>
<body>
    <strong>this is text with < and > symbols</strong>
</body>
</html>\
"""

TEST_SAMPLE_TERMINAL_PARSING_INVALID = """
<html>
<body>
    <strong>this is double strong tag</strong></strong>
</body>
</html>\
"""

TEST_SAMPLE_FILES = "tests/flang/test_files"

TEST_SAMPLE_LINKING = """
from math import sin
from math import pi
from math import cos

sin(10)
cos(pi)
"""

### TEMPLATES

TEST_BASIC_TEMPLATE = """
<sequence>
    <text value="hello "/><text regex="true" name="subject" value="{vname}"/>
</sequence>
"""

TEST_TEMPLATE_CHOICE = """
<sequence name="import">
<choice>
<text name="text-val">AAA</text>
<text regex="true" name="regex">{vname}</text>
<text name="wrong">
THIS IS WRONG
</text>
</choice>
</sequence>
"""

# this would be useful with combination of "use" construct
# f.e.: choice of variable declaration or types or raw values
TEST_TEMPLATE_CHOICE_NESTED = r"""
<sequence name="nested">
<choice name="all-pieces" multi="true">
<choice name="text-pieces">
<text value="ipsum"/>
<text value="Lorem"/>
<text name="wrong" value="wrong!"/>
<text value="dolor"/>
<text value="amet"/>
<text value="sit"/>
</choice>
<choice name="my-regexes">
<text regex="true" name="whitespace">\s</text>
<text regex="true" name="separators">[,.]</text>
<text regex="true" name="wrong">[:;%$]+</text>
<text regex="true" name="number">{number}</text>
</choice>
<text name="wrong">wrong</text>
</choice>
<text value="end"/>
</sequence>
"""

TEST_TEMPLATE_OPTIONAL = """
<sequence name="opt">
<text value="this is a "/>
<sequence name="num" optional="true">
<text value="number: "/><text regex="true" value="{number}"/>
</sequence>
<sequence name="txt" optional="true">
<text value="text: "/><text regex="true" value="{string}"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_CHOICE_AND_MULTI = r"""
<sequence name="test" multi="true">
<text value="My name is "/>
<choice optional="true">
<text value="Sam"/>
<text value="Tom"/>
<text value="Zoe"/>
<sequence multi="true">
<text regex="true" name="other" value="[a-z]+(, )?" multi="true"/>
</sequence>
</choice>
<text value="."/>
<text regex="true" value="\s"/>
</sequence>
"""

TEST_TEMPLATE_USE = """
<sequence name="import">
<sequence name="foo" hidden="true">
<text>foo</text>
</sequence>
<sequence name="bar">
<use ref="..foo"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_MULTI = r"""
<sequence name="import">
<sequence name="header" multi="true">
<text multi="true">AAA</text>
<text regex="true">\s</text>
</sequence>
<sequence name="variable" multi="true">
<text value="variable: "/><text regex="true" name="name" value="{vname}"/><text regex="true" value=";\n?"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_RECURSIVE = r"""
<sequence name="xml-body" multi="true">
    <text optional="true" regex="true" name="top-level-whitespace">\s+</text>
    <sequence optional="true" name="xml-node" multi="true">
        <text regex="true" name="open-tag" value="{xml_open_tag}"/>
        <choice name="xml-content" multi="true">
            <text multi="true" regex="true" name="raw-content" value="{XML_CONTENT_CHAR}"/>
            <use multi="true" ref="...xml-node"/>
        </choice>
        <text regex="true" name="close-tag" value="{xml_close_tag}"/>
    </sequence>
</sequence>
"""

# Slower version of above parser that uses explicit terminal symbols
TEST_TEMPLATE_CHOICE_TERMINAL = r"""
<sequence name="xml-body" multi="true">
    <text optional="true" regex="true" name="top-level-whitespace">\s+</text>
    <sequence optional="true" name="xml-node" multi="true">
        <text regex="true" name="open-tag" value="{xml_open_tag}"/>
        <choice name="xml-content" multi="true">
            <text regex="true" name="raw-content" value="{ANY}"/>
            <use multi="true" ref="...xml-node"/>
            <text terminal="true" regex="true" name="close-tag" value="{xml_close_tag}"/>
        </choice>
    </sequence>
</sequence>
"""

"""
<-- terse preprocessor -->
<s n=xml-body multi>
    <t optional regex n=top-level-whitespace>\s+/>
    <s optional n=xml-node multi>
        <t regex n=open-tag v={xml_open_tag}/>
        <c n=xml-content multi="true">
            <t regex n=raw-content v={ANY}/>
            <u ref=...xml-node/>
            <t terminal regex n=close-tag v={xml_close_tag}/>
        />
    />
/>
"""

TEST_TEMPLATE_FILES_EASY = r"""
<file pattern="easy" name="html-project">
    <file multi="true" pattern="{filename}.html" regex="true">
        <sequence name="html">
            <text name="content" value="some text "/>
            <text regex="true" name="number" value="{number}"/>
        </sequence>
    </file>
</file>
"""

TEST_TEMPLATE_FILES_XML = rf"""
<file pattern="xml" name="html-project">
<file multi="true" pattern="{{filename}}.html" regex="true">
{TEST_TEMPLATE_RECURSIVE}
</file>
</file>
"""
TEST_TEMPLATE_FILES_MEDIUM = r"""
"""

# this example tbh does not make real-world sense here
TEST_TEMPLATE_LINKING = r"""
<sequence name="code" multi="true">
<choice name="code-parts">
<sequence name="import">
  <text value="from "/><text regex="true" name="module" value="{vname}"/>
  <text value=" import "/><text regex="true" name="object" value="{vname}"
    link-name="imported" scope-start="..code-parts"/>
  <use ref="..nl"/>
</sequence>
<text regex="true" name="nl" value="\s"/>
<sequence name="function-call">
    <text regex="true" name="reference" value="{vname}"/>
    <text value="("/>
    <text regex="true" name="argument" value="{vname}|{number}" 
        optional="true" refers-to-link="imported"/>
    <sequence multi="true" optional="true">
        <text regex="true" name="separator" value="\s*,\s*"/>
        <use ref="..argument" optional="false"/>
    </sequence>
    <text value=")"/>
    <use ref="..nl" optional="true"/>
</sequence>
</choice>
</sequence>
"""

TEST_TEMPLATE_FUNCTION_1 = r"""
<sequence multi="true">
<event name="add-message">
    context["result"] = kwargs["local_content"]
</event>
<sequence>
<text value="say "/><text regex="true" event_5_read="..add-message" value="{string}|{vname}|{number}" name="value"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_FUNCTION_2 = r"""
<sequence>
<event alias="func" source="tests/flang/test_files/test_module/sample_events.py:event2"/>
<sequence>
<text value="say "/><text regex="true" value="{string}|{vname}|{number}" name="value" event_10_read="@func"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_FUNCTION_3 = r"""
<sequence>
<event alias="func">
    if "executed" not in context:
        context["message"] = kwargs["local_content"]
    else:
        context["message"] = kwargs["local_content"]
</event>
<sequence>
<text regex="true" value="{vname}" event_5_read="@func" name="value1"/>
<text value=" "/>
<text regex="true" value="{vname}" event_10_read="@func" name="value2"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_REWRITE = """
<sequence>
    <sequence alias="polish" hidden="true">
        <text value="Dzień dobry! Nazywam się "/>
        <text regex="true" value="\\w+" name="name"/>
    </sequence>
    <sequence alias="english" hidden="true">
        <choice>
            <text value="Good morning!"/>
            <text value="Good afternoon!"/>
        </choice>
        <text value=" My name is "/>
        <text regex="true" value="\\w+" name="name"/>
        <sequence name="extra-message" optional="true">
            <text value=". "/>
            <text regex="true" value="[A-Z].+"/>
        </sequence>
    </sequence>
    <sequence name="greeting" multi="true">
        <choice>
            <use name="polish" ref="@polish"/>
            <use name="english" ref="@english"/>
        </choice>
        <text regex="true" value="\\.?\\n"/>
    </sequence>
    <text optional="true" multi="true" value="dot"/>
</sequence>
"""

REWRITE_SAMPLE_1 = """\
Dzień dobry! Nazywam się Michał.
Good morning! My name is Alan. How are you?
Dzień dobry! Nazywam się Piotr.
Good afternoon! My name is Victor. How was your day?
Good morning! My name is Ernest.
dotdot"""

TEST_TEMPLATE_EDGE_CASES = """
<sequence name="p" alias="parent" multi="true">
    <text name="foo" alias="foo" value="a"/>
    <use optional="true" ref="@parent"/>
    <use ref="@bar"/>
    <use ref="@bar" multi="true"/>
    <use ref="@parent" optional="true"/>
    <sequence optional="true">
        <sequence optional="true">
            <sequence>
            <choice>
            <text name="foo" alias="bar" value="b"/>
            </choice>
            </sequence>
        </sequence>
    </sequence>
    <text value="END"/>
</sequence>
"""

EDGE_CASE_SAMPLE = "aabbbbbbENDbbbabbENDbEND"

HALTING_TEST_TEMPLATE = """
<sequence multi="true">
    <text optional="true" value="A"/>
</sequence>
"""

HALTING_TEST_SAMPLE = "AB"

# END
## END
### END
#### END
##### END
###### END
####### END
######## END
######### END
########## END
########### END
############ END
############# END
############## END
############### END
################ END
################# END
################## END
################### END
#################### END
########### END
############ END
############# END
############## END
############### END
################ END
################# END
################## END
################### END
#################### END
##################### END
###################### END
####################### END
######################## END
######################### END
########################## END
########################### END
################## END
################### END
#################### END
##################### END
###################### END
####################### END
######################## END
######################### END
########################## END
########################### END
############################ END
############################# END
############################## END
############################### END
################################ END
################################# END
################################## END
################################### END
#################################### END
##################################### END

# DUMMY_TEST_TEMPLATE_EVENT = r"""
# <sequence name="code">
# <sequence name="import">
# <text value="import "/><regex value="{vname}"/><text value="\\n"/>
# </sequence>
# <sequence name="function-call" on-create=".">
# <event args="tree">
# print("hello world")
# </event>
# <regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
# <regex name="arguments" value="[^)]*"/>
# <text value=")"/>
# </sequence>
# </sequence>
# """

SAMPLE_CHOICE = "AAAAAA"
SPEC_EVENT = None

# DUMMY_TEST_TEMPLATE_EVENT = r"""
# <sequence name="code">
# <sequence name="import">
# <text value="import "/><regex value="{vname}"/><text value="\\n"/>
# </sequence>
# <sequence name="function-call" on-create=".">
# <event args="tree">
# print("hello world")
# </event>
# <regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
# <regex name="arguments" value="[^)]*"/>
# <text value=")"/>
# </sequence>
# </sequence>
# """


# def main():
#     parser = FlangXMLParser()
#     # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_CHOICE_1)
#     # print(flang_object)
#     # processor = FlangTextProcessor(flang_object)
#     # match_obj = processor.backward(SAMPLE_CHOICE)
#     # print()
#     # print(match_obj)
#     # generated = processor.forward(match_obj)
#     # print()
#     # print(generated)

#     # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_EVENT)
#     # processor = FlangTextProcessor(flang_object)
#     # print(processor.forward)
#     # generated = processor.forward(SPEC_EVENT)
#     # print(generated)

#     # print()
#     # parser.clear()
#     flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_MULTI)
#     processor = FlangTextProcessor(flang_object)
#     match_obj = processor.forward(SAMPLE_MULTI)
#     print(match_obj)
#     generated = processor.backward(match_obj)
#     print(generated)
