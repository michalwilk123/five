from flang.generators.specification_to_ast import create_ast_with_patched_values
from flang.structures import FlangAST, TemplateTree


def diff(first: FlangAST, other: FlangAST):
    if first.get_id() != other.get_id():
        print(f"NAME DIFFERENT: {first.get_id()=} {other.get_id()=}")
        return False

    if first.template_id != other.template_id:
        print(f"PATH DIFFERENT: {first.template_id=} {other.template_id=}")
        return False

    if first.children:
        if not other.children or len(first.children) != len(other.children):
            print(
                f"CHILDREN DIFFERENT: {first.get_id()=} {other.get_id()=}: \n{first.children=} \n{other.children=}"
            )
            print(ast_to_string(first))
            print("======")
            print(ast_to_string(other))
            print(first.location)
            return False

        return all(
            diff(child1, child2) for child1, child2 in zip(first.children, other.children)
        )

    return True


def ast_to_string(ast: FlangAST):
    if hasattr(ast, "content"):
        if ast.content is None:
            pass

        return ast.content
    if ast.children:
        try:
            return "".join(ast_to_string(child) for child in ast.children)
        except Exception as e:
            print([type(a) for a in ast.children])
            raise e
    return ""


def generate_text(template_tree: TemplateTree, path: str) -> str:
    subtree = template_tree.resolve_path(path)
    flang_tree = create_ast_with_patched_values(subtree, {}, fill_missing=True)
    return ast_to_string(flang_tree)
