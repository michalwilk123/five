import functools


def get_constr_size(toks):
    tot = 0

    for item in toks:
        _, content = item

        if isinstance(content, list):
            tot += get_constr_size(content)
        else:
            tot += 1

    return tot


def define_match_function(function):
    @functools.wraps(function)
    def _inner(match_funcs):
        return functools.partial(function, match_funcs)

    return _inner


@define_match_function
def Or_(match_functions, content):
    all_matches = []

    for func in match_functions:
        matched = func(content)
        all_matches.append(matched)

    all_matches = [it for it in all_matches if it is not None]
    return max(all_matches, key=get_constr_size) if all_matches else None


@define_match_function
def And_(match_functions, content):
    all_matches = []

    for func in match_functions:
        matched = func(content[get_constr_size(all_matches) :])
        if matched is None:
            return None

        all_matches += matched

    return all_matches


@define_match_function
def Multi_(func, content):
    all_matches = None

    while True:
        matches = func(content[get_constr_size(all_matches or []) :])

        if matches in (None, []):
            return all_matches or matches

        all_matches = (all_matches or []) + matches


@define_match_function
def Opt_(func, value):
    matches = func(value)
    return [] if matches is None else matches


def Literal_(base_text, tokens):
    if not tokens:
        return None

    current_string = ""
    subtokens = []

    for token_name, matched_text in tokens:
        current_string += matched_text
        subtokens.append((token_name, matched_text))

        if current_string == base_text:
            return [("LITERAL", subtokens)]

        if len(current_string) > len(base_text):
            break

    return None


def Lex_(atom, tokens):
    if not tokens:
        return None

    lex_keyword, _ = tokens[0]

    if atom == lex_keyword:
        return [tokens[0]]
    return None
