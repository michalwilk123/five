"""
The Five language

The language for specifying the frames and examples defining code.
Using this application you would be able to
ask the program: "Create me component like XYZ with red color"
and it would be able to create the proper code

Maybe the language for the user would be different but the
idea is exact same.

It would be possible by using the Minsky idea of frames and examples.
We here will define some useful frames and some examples.
Users will be able to put here their own either custom frames or examples

We will be asking the system for some functionality and using 
reverse matching it will look for most appropriate example and
fill out the details that the user will propose
"""

# from core.parser import FlangParser
# from core.processors import FlangStandardProcessorToolchain


def main(filename):
    with open(filename) as f:
        ...


DUMMY_TEST_TEMPLATE = """
<component name="import">
<text>from </text><predicate name="module" pattern="{vname}"/> import <predicate name="object" pattern="{vname}"/>
</component>
"""

DUMMY_TEST_TEMPLATE_CHOICE = """
<component name="import" type="choice">
    <component name="short">
    import <predicate name="module" pattern="{vname}"/>
    </component>
    <component name="detail">
    from <predicate name="module" pattern="{vname}"/> import <predicate name="object" pattern="{vname}"/><component type="optional">as <predicate name="as" pattern="{vname}"/></component>
    </component>
</component>
"""

DUMMY_TEST_TEMPLATE_CHOICE_1 = """
<component name="import">
<component name="lalala">
<text>AAA</text>
<regex>{vname}</regex>
</component>
</component>
"""

DUMMY_TEST_TEMPLATE_REF = """
<component name="abc">
    <component name="start" visible="false">quick fox <predicate name="verb" pattern="[a-z]+"/></component>
    <component name="end">
        <ref path="..start"> jumps over lazy <predicate name="animal" pattern="[a-z]+"/>
    </component>
</component>
"""

DUMMY_TEST_SAMPLE_1 = "from json import dumps"
DUMMY_TEST_SAMPLE_2 = "from itertools import chain"
DUMMY_TEST_SAMPLE_3 = "AAA"
DUMMY_TEST_SAMPLE_4 = "AAAAAA"


def dummy_main():
    ...

    # interpreter = FlangParser()
    # flang_ast = interpreter.parse_text(DUMMY_TEST_TEMPLATE_CHOICE_1)
    # match_processor = FlangStandardProcessorToolchain(flang_ast)
    # ret = match_processor.backward(DUMMY_TEST_SAMPLE_1)
    # text = match_processor.forward(ret)

    # print(ret)
    # print(text)
    # interpreter.feed(DUMMY_TEST_SAMPLE_1)
    # interpreter.feed(DUMMY_TEST_SAMPLE_2)
    # generator = parse_text(DUMMY_TEST_TEMPLATE)
    # generator.feed(DUMMY_TEST_SAMPLE_1)
    # generator.feed(DUMMY_TEST_SAMPLE_2)
    # print(generator.samples)

    # generated = interpreter.generate({"object": "chain"})
    # print(generated)


if __name__ == "__main__":
    dummy_main()
