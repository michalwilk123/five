from fenv.interpreter.syntax import parser

input_text = """
# comment
INSERT AFTER path.to.other.component FOR _ IN node.to.change;

MODIFY item 
    item.other.change := 2 
    item.other.choice.value.text := x.sth.text 
    FOR item IN path.to.other.component 
    WHERE x := node.to.change;

COMMIT;

# this still works. Language is case insensitive for keywords
modify 
    node.to.change[1].value.text := path.to.other.component[2].text;
COmmit;

# this still works continuation:
modify 
    node.to.change[1].value.text := {{path.to.other.component[2].name with spaces .text}};
COmmit;

DEFINE REWRITE source target steps
BEGIN
    INSERT {{target}} AFTER item FOR item IN {{source}};
    MODIFY 
        {{steps}}
        FOR source IN {{source}}
        WHERE target := {{target}};
    DELETE node FOR node IN {{source}};
    COMMIT;
END;

REWRITE {{node.to.change}} {{path.to.other.component}} {{item.other.change := 2 item.other.choice.value.text := x.sth.text}};
COMMIT;
"""

"""



DEFINE REWRITE source target steps
START
    INSERT {{target}} AFTER item FOR item IN {{source}};
    MODIFY 
        {{steps}}
        FOR source IN {{source}}
        WHERE target := {{target}};
    DELETE node FOR node IN {{source}};
    COMMIT;
END;

REWRITE {{node.to.change}} {{path.to.other.component}} {{item.other.change := 2 item.other.choice.value.text := x.sth.text}};
"""

if __name__ == "__main__":
    # input_text = "MODIFY item dsads := 32"
    # input_text = "MODIFY item item.other.change := 2 item.other.choice.value.text := x.sth.text FOR item IN path.to.other.component WHERE x := node.to.change; COMMIT;"
    # input_text = "MODIFY item item.other.choice.value.text := x.sth.text"

    #     input_text = """\
    # DEFINE REWRITE source target steps
    # BEGIN
    #     INSERT {{target}} AFTER item FOR item IN {{source}};
    #     MODIFY 
    #         {{steps}}
    #         FOR source IN {{source}}
    #         WHERE target := {{target}};
    #     DELETE node FOR node IN {{source}};
    #     COMMIT;
    # END;
    # COMMIT;"""

    ast = parser.execute(input_text)
    print("RES:")
    print(ast)