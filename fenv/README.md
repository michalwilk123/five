
# Fenv
Fenv is a set of tools what work with Flang that combined create Five: a semantic
version control system

### Tools
* Fenv scripting language
* Fenv command line interface

### Fenv Scripting language (five script) (.fs extension)


#### The example of the scripting language 


# comment
INSERT AFTER path.to.other.component FOR _ IN node.to.change;
MODIFY item 
    item.other.change := 2
    item.other.choice.value.text := x.sth.text
    FOR item IN path.to.other.component
    WHERE x := node.to.change;
DELETE NODE FOR node IN node.to.change;
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
