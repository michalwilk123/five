class FuzzyDict(dict):
    """
    fd = FuzzyDict()

    fd["abc"] = "some text"

    print(fd["abc"]) # -> "some text"
    print(fd.fget("abc")) # -> ["some text"]

    fd["def.x"] = "foo"
    fd["def.xy"] = "bar"
    fd["def.z"] = "foobar"


    print(fd.fget("def.x*")) # -> ["foo", "bar"]
    print(fd.fget("def.*")) # -> ["foo", "bar", "foobar"]
    print(fd.fget("*")) # -> ["some text", "foo", "bar", "foobar"]

    """

    pass
