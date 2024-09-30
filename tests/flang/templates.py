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
    <text value="hello "/><regex name="subject" value="{vname}"/>
</sequence>
"""
TEST_TEMPLATE_CHOICE = """
<sequence name="import">
<choice>
<text name="text">AAA</text>
<regex name="regex">{vname}</regex>
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
<regex name="whitespace">\s</regex>
<regex name="separators">[,.]</regex>
<regex name="wrong">[:;%$]+</regex>
<regex name="number">{number}</regex>
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
<text value="number: "/><regex value="{number}"/>
</sequence>
<sequence name="txt" optional="true">
<text value="text: "/><regex value="{string}"/>
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
<regex name="other" value="[a-z]+(, )?" multi="true"/>
</sequence>
</choice>
<text value="."/>
<regex value="\s"/>
</sequence>
"""

TEST_TEMPLATE_USE = """
<sequence name="import">
<sequence name="foo" visible="false">
<text>foo</text>
</sequence>
<sequence name="bar">
<use ref="..foo"/>
</sequence>
</sequence>
"""

"""
Wiadomo ze jezeli chcialbys sparsowac cokolwiek to wszystko mozna owinac
w regexy i sobie znacznie ulatwic sprawe.
Zapominasz tylko po co tak naprawde istnieje ta klazura multi

bardziej w tym chodzi o to aby okreslic ze zwracana jest lista jakis
obiektow, np sequenceow ze zmatchowanym tekstem. Jakby musisz wciaz o tym
pamietac
"""
TEST_TEMPLATE_MULTI = r"""
<sequence name="import">
<sequence name="header" multi="true">
<text multi="true">AAA</text>
<regex>\s</regex>
</sequence>
<sequence name="variable" multi="true">
<text value="variable: "/><regex name="name" value="{vname}"/><regex value=";\n?"/>
</sequence>
</sequence>
"""

TEST_TEMPLATE_RECURSIVE = r"""
<choice name="xml-body" multi="true">
    <regex name="wspace">\s+</regex>
    <sequence name="xml-node" multi="true">
        <regex name="open-tag" value="{xml_open_tag}"/>
        <choice name="xml-content" multi="true">
            <regex name="raw-content" value="[^{lt}{rt}]+"/>
            <use ref="....xml-body"/>
        </choice>
        <regex name="close-tag" value="{xml_close_tag}"/>
    </sequence>
</choice>
"""

TEST_TEMPLATE_FILES_EASY = r"""
<file pattern="easy" variant="filename" name="html-project">
<file multi="true" pattern="*.html" variant="glob">
<sequence name="html">
<text name="content" value="some text "/>
<regex name="number" value="{number}"/>
</sequence>
</file>
</file>
"""

TEST_TEMPLATE_FILES_XML = r"""
<file pattern="xml" variant="filename" name="html-project">
<file multi="true" pattern="*.html" variant="glob">
{template}
</file>
</file>
""".format(
    template=TEST_TEMPLATE_RECURSIVE
)
TEST_TEMPLATE_FILES_MEDIUM = r"""
"""

# this example tbh does not make real-world sense here
TEST_TEMPLATE_LINKING = r"""
<sequence name="code" multi="true">
<choice name="code-parts">
<sequence name="import">
  <text value="from "/><regex name="module" value="{vname}"/>
  <text value=" import "/><regex name="object" value="{vname}"
    link-definition="imported" scope="..code-parts"/>
  <use ref="..nl"/>
</sequence>
<regex name="nl" value="\s"/>
<sequence name="function-call">
    <regex name="reference" value="{vname}"/>
    <text value="("/>
    <regex name="argument" value="{vname}|{number}" 
        optional="true" link-from="imported"/>
    <sequence multi="true" optional="true">
        <regex name="separator" value="\s*,\s*"/>
        <use ref="..argument" optional="false"/>
    </sequence>
    <text value=")"/>
    <use ref="..nl" optional="true"/>
</sequence>
</choice>
</sequence>
"""

TEST_TEMPLATE_FUNCTION = r"""
<sequence multi="true">
<event name="print-message" alias="func">
    print("hello")
</event>
<sequence execute-1=".print-message">
<text value="say"/><regex value="{string|vname|number}" name="value"/>
</sequence>
</sequence>
"""

DUMMY_TEST_TEMPLATE_EVENT = r"""
<sequence name="code">
<sequence name="import" multi="true">
<text value="import "/><regex name="import_name" value="{vname}"/><text value="\n"/>
</sequence>
<sequence name="function-call" on-create=".">
<event args="tree">
function_name = tree.get("name")
tree.parent().get("import").insert(name=function_name)
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</sequence>
</sequence>
"""

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

DUMMY_TEST_TEMPLATE_EVENT = r"""
<sequence name="code">
<sequence name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</sequence>
<sequence name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</sequence>
</sequence>
"""

SAMPLE_CHOICE = "AAAAAA"
SPEC_EVENT = None

DUMMY_TEST_TEMPLATE_EVENT = r"""
<sequence name="code">
<sequence name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</sequence>
<sequence name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</sequence>
</sequence>
"""


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
