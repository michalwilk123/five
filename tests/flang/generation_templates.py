PYTHON_CODE_TEMPLATE = """
<sequence>
    <choice alias="bool-stmt" hidden="true">
        <text name="true" value="True"/>
        <text name="false" value="False"/>
        <sequence>
            <text regex="true" value="{vname}|{integer}" name="l-value"/><text value=" % "/>
            <text regex="true" value="{vname}|{integer}" name="r-value"/><text value=" == "/>
            <text regex="true" value="{vname}|{integer}" name="equality-r-value"/>
        </sequence>
    </choice>
    <text alias="tab" value="    " hidden="true"/>
    <choice name="code" multi="true" optional="false" alias="code">
        <sequence name="for-in-loop">
            <text value="for "/><text regex="true" value="{vname}" name="index"/><text value=" in range(" />
            <sequence optional="true">
                <text regex="true" value="{integer}" name="start"/><text value=", "/>
            </sequence>
            <text regex="true" value="{integer}" name="end"/>
            <text value="):&#xA;"/>
            <sequence name="for-loop-body" multi="true">
                <use ref="@tab"/>
                <use ref="@code"/>
            </sequence>
        </sequence>
        <sequence name="if-stmt">
            <text value="if "/><use ref="@bool-stmt"/><text value=":&#xA;"/>
            <choice>
                <sequence multi="true">
                    <use ref="@tab"/>
                    <use ref="@code"/>
                </sequence>
                <sequence>
                    <text value="elif "/><use ref="@bool-stmt"/><text value=":&#xA;"/>
                    <sequence multi="true">
                        <use ref="@tab"/>
                        <use ref="@code"/>
                    </sequence>
                </sequence>
            </choice>
            <sequence optional="true">
                <text value="else:&#xA;"/>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                </sequence>
            </sequence>
        </sequence>
        <sequence>
            <text value="print("/>
            <text regex="true" value="{integer}|{string}|{vname}"/>
            <text value=")"/>
        </sequence>
        <text value="pass"/>
        <text regex="true" name="wspace">{whitespace}</text>
    </choice>
</sequence>
"""

JAVASCRIPT_CODE_TEMPLATE = """
<sequence>
    <text alias="wspace" regex="true" hidden="true" multi="true">{whitespace}</text>
    <choice alias="primitive" hidden="true">
        <text regex="true" value="{integer}"/>
        <text regex="true" value="{string}"/>
        <text regex="true" value="{vname}"/>
        <text value="true"/>
        <text value="false"/>
    </choice>
    <sequence hidden="true" alias="expression">
        <use ref="@primitive"/>
        <sequence name="operation" multi="true" optional="true">
            <use optional="true" ref="@wspace"/>
            <choice>
                <text value="=="/>
                <text value="+"/>
                <text value="-"/>
                <text value="%"/>
                <text value="&gt;"/>
                <text value="&lt;"/>
                <text value="&lt;="/>
                <text value="&gt;="/>
            </choice>
            <use optional="true" ref="@wspace"/>
            <use ref="@primitive"/>
        </sequence>
    </sequence>
    <sequence alias="code-block" hidden="true">
        <text value="{"/>
        <use optional="true" ref="@wspace"/>
        <use multi="true" ref="@construct"/>
        <use optional="true" ref="@wspace"/>
        <text value="}"/>
    </sequence>
    <sequence alias="construct" hidden="true">
        <choice>
            <sequence alias="if-statement" name="if-statement">
                <text value="if"/>
                <use optional="true" ref="@wspace"/>
                <text value="("/>
                <use optional="true" ref="@wspace"/>
                <use ref="@expression"/>
                <use optional="true" ref="@wspace"/>
                <text value=")"/>
                <use optional="true" ref="@wspace"/>
                <use ref="@code-block"/>
                <use optional="true" ref="@wspace"/>
                <sequence name="else-statement" optional="true">
                    <text value="else"/>
                    <use ref="@wspace"/>
                    <choice>
                        <use ref="@if-statement"/>
                        <use ref="@code-block"/>
                    </choice>
                </sequence>
            </sequence>
            <sequence name="for-loop">
                <text value="for"/>
                <use optional="true" ref="@wspace"/>
                <text value="("/>
                <use optional="true" ref="@wspace"/>
                <text regex="true" value="var {vname} = "/>
                <use ref="@primitive"/>
                <use optional="true" ref="@wspace"/>
                <text value=";"/>
                <use optional="true" ref="@wspace"/>
                <use ref="@expression"/>
                <use optional="true" ref="@wspace"/>
                <text value=";"/>
                <use optional="true" ref="@wspace"/>
                <text regex="true" value="{vname}"/>
                <choice>
                    <text value="++"/>
                    <text value="--"/>
                </choice>
                <use optional="true" ref="@wspace"/>
                <text value=")"/>
                <use optional="true" ref="@wspace"/>
                <use ref="@code-block"/>
            </sequence>
            <sequence name="console-log">
                <text value="console.log("/>
                <use ref="@expression"/>
                <text value=");"/>
            </sequence>
            <use ref="@wspace"/>
        </choice>
    </sequence>
    <sequence multi="true">
        <use ref="@construct"/>
    </sequence>
</sequence>
"""

PYTHON_CODE_SAMPLE_1 = """
print("hello world")
pass
"""

PYTHON_CODE_SAMPLE_2 = """
pass
for i in range(10):
    pass
    print(10)
"""

PYTHON_CODE_SAMPLE_3 = """
if i % 2 == 0:
    print(123)
"""

PYTHON_CODE_SAMPLE_4 = """
if i % 2 == 0:
    for value in range(111):
        if i % 10 == 2:
            print("nested")
"""

JS_CODE_SAMPLE_1 = """
console.log(1);
console.log(1);
"""

JS_CODE_SAMPLE_2 = """
for(var i=0; i<10; i++) {
    console.log(1);
}
"""
JS_CODE_SAMPLE_2 = """
for(var snake_case_name = true; false;world--){ console.log(variable
- false); }
"""

JS_CODE_SAMPLE_3 = """
if (value % 10 == 2) {
    console.log("lorem ipsum");
} else if (true) {
    console.log(32332);
} else {
    console.log(10);
}
"""

JS_CODE_SAMPLE_3 = """
if ( 
  true ) { console.log(1);}
"""

PYTHON_CODE_SAMPLE_FIZZBUZZ = """
for i in range(1, 101):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
"""

JAVASCRIPT_CODE_SAMPLE_FIZZBUZZ = """
for (var i=0; i<101; i++) {
    if (i % 15 == 0) {
        console.log("FizzBuzz");
    }
    else if (i % 3 == 0) {
        console.log("Fizz");
    }
    else if (i % 5 == 0) {
        console.log("Buzz");
    }
    else {
        console.log(i);
    }
}
"""

REWRITE_SCRIPT = """
modify python.component.1 javascript.component.1 
argument.lala -> argument.other, foo -> bar;

"""
