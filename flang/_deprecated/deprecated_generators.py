import fnmatch
import random

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot
from flang.utils.exceptions import SymbolNotFoundError
from flang.utils.regex import lex_storage

from .core.utils import get_cardinality_key, resolve_use_node


class GeneratorSetup:
    def __init__(self, ast: FlangAST) -> None:
        self.patches: dict[str, str | int] = {}
        self.enforce_full_specification: bool = False
        self.ast = ast

    def _generate_random_content(self, location: str):
        flang_node = self.ast.full_search(location)

        if flang_node is None:
            raise SymbolNotFoundError

        if flang_node.type == "sequence":
            return None
        elif flang_node.type == "choice":
            return random.randrange(len(flang_node.children))
        elif flang_node.type == "text":
            flang_ast_text = flang_node.get_attrib("value", flang_node.text)
            return (
                lex_storage.generate_example(flang_ast_text)
                if flang_node.get_bool_attrib("regex")
                else flang_ast_text
            )
        elif flang_node.type == "file":
            filename = flang_node.get_attrib("filename")
            return (
                lex_storage.generate_example(filename)
                if flang_node.get_attrib("variant") == "regex"
                else filename
            )

        raise RuntimeError

    def _generate_cardinality(self, flang_node: FlangAST):
        if flang_node.get_bool_attrib("hidden"):
            return 0

        number_choice = [1]

        if flang_node.get_bool_attrib("multi"):
            number_choice = number_choice + [2, 3]

        if flang_node.get_bool_attrib("optional"):
            number_choice = number_choice + [0]

        return random.choice(number_choice)

    def get_cardinality(self, flang_node: BaseUserAST):
        cardinality_key = get_cardinality_key(flang_node.location)

        for key, value in self.patches.items():
            if fnmatch.fnmatchcase(cardinality_key, key):
                return value

        return self._generate_cardinality(flang_node)

    def get(self, node: BaseUserAST):
        location = node.location

        for key, value in self.patches.items():
            if fnmatch.fnmatchcase(location, key):
                return value

        return self._generate_random_content(node.flang_ast_path)


def create_empty_setup(flang_ast: FlangAST):
    return GeneratorSetup(flang_ast)


def generate_empty_node(flang_ast: FlangAST) -> BaseUserAST:
    if flang_ast.type == "sequence":
        return UserBranch(
            flang_ast_path=flang_ast.location, name=flang_ast.name, children=[]
        )
    elif flang_ast.type == "choice":
        return UserBranch(
            flang_ast_path=flang_ast.location, name=flang_ast.name, children=[]
        )
    elif flang_ast.type == "text":
        return UserLeaf(
            flang_ast_path=flang_ast.location, name=flang_ast.name, content="dummy_text"
        )
    elif flang_ast.type == "regex":
        return UserLeaf(
            flang_ast_path=flang_ast.location,
            name=flang_ast.name,
            content="dummy_[0-9]regex",
        )
    elif flang_ast.type == "use":
        resolved_node = resolve_use_node(flang_ast)
        return generate_empty_node(resolved_node)
    elif flang_ast.type == "file":
        return UserBranch(
            filename="dummy-name",
            children=[],
            flang_ast_path=flang_ast.location,
            name=flang_ast.name,
        )


def fill_node_content(
    flang_ast: FlangAST, node_to_fill: BaseUserAST, data
) -> list | None:
    if flang_ast.type == "sequence":
        assert isinstance(node_to_fill, UserBranch)
        return [child for child in flang_ast.children]

    elif flang_ast.type == "choice":
        assert isinstance(node_to_fill, UserBranch)
        chosen_child = flang_ast.children[data]

        if chosen_child.get_bool_attrib("terminal"):
            node_to_fill.is_terminal = None

        return [chosen_child]
    elif flang_ast.type == "text" or flang_ast.type == "regex":
        assert isinstance(node_to_fill, UserLeaf)
        node_to_fill.content = data
        return None
    elif flang_ast.type == "use":
        assert 0, "ImpossibleOperationError"
    elif flang_ast.type == "file":
        assert isinstance(node_to_fill, UserBranch)

        node_to_fill.filename = data
        return [child for child in flang_ast.children]

    assert 0, "ImpossibleOperationError"


def generate_filled_node_with_cardinality(
    flang_node: FlangAST, parent: BaseUserAST, setup: GeneratorSetup
) -> None:
    if flang_node.get_bool_attrib("hidden") or flang_node.type in ["event"]:
        return

    quantity = setup.get_cardinality(flang_node)

    for _ in range(quantity):
        node = generate_empty_node(flang_node)
        flang_node = flang_node.full_search(node.flang_ast_path)

        assert flang_node is not None

        parent.add_node(node)
        data = setup.get(node)
        children_to_setup = fill_node_content(flang_node, node, data) or []

        for child in children_to_setup:
            generate_filled_node_with_cardinality(child, node, setup)

        if hasattr(node, "is_terminal"):
            break


def generate_ast(flang_ast: FlangAST, setup=None):
    setup = setup or create_empty_setup(flang_ast)
    root = UserRoot()

    generate_filled_node_with_cardinality(flang_ast, root, setup)

    return root


## Second try on the generators, also deprecated

import random

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot
from flang.utils.regex import lex_storage


class SpecificationKeyValueStore(dict):
    def get_cardinality_key(self, parent_location: str, child_name: str) -> str:
        return f"{parent_location}::card({child_name})"

    def set_cardinality(
        self, parent_location: str, child_name: str, cardinality: int
    ) -> str:
        assert isinstance(cardinality, int)
        key = self.get_cardinality_key(parent_location, child_name)
        self[key] = cardinality

    def get_cardinality(self, parent_location: str, child_name: str) -> int:
        return self.get(self.get_cardinality_key(parent_location, child_name))

    def get_choice_node_key(self, location: str) -> str:
        return f"{location}::choice"

    def get_choice_node(self, location: str):
        return self.get(self.get_choice_node_key(location))

    def set_choice_node(self, location: str, chosen_node: str):
        assert isinstance(chosen_node, str)
        key = self.get_choice_node_key(location)
        self[key] = chosen_node

    def get_regex_content_key(self, location: str) -> str:
        return f"{location}::regex"

    def get_regex_content(self, location: str) -> str:
        return self.get(self.get_regex_content_key(location))

    def set_regex_content(self, location: str, content: str):
        self[self.get_regex_content_key(location)] = content


def get_node_cardinality(
    flang_node: FlangAST, parent_location: str, specification: SpecificationKeyValueStore
):
    quantity = specification.get_cardinality(parent_location, flang_node.name)

    if quantity is not None:
        return quantity

    if flang_node.get_bool_attrib("hidden") or flang_node.type in ["event"]:
        return 0

    number_choice = [1]

    if flang_node.get_bool_attrib("multi"):
        number_choice = number_choice + [2, 3]

    if flang_node.get_bool_attrib("optional"):
        number_choice = number_choice + [0]

    quantity = random.choice(number_choice)

    return quantity


def get_choice_node(
    flang_node: FlangAST, parent_location: str, specification: SpecificationKeyValueStore
) -> int:
    chosen_node = specification.get_cardinality(parent_location, flang_node.name)

    if chosen_node is not None:
        return chosen_node

    return random.randrange(len(flang_node.children))


def get_regex_content(
    flang_node: FlangAST, node_location: str, specification: SpecificationKeyValueStore
) -> int:
    content = specification.get_regex_content(node_location, flang_node.name)

    if content is not None:
        return content

    content = flang_node.get_attrib("value", flang_node.text)

    return lex_storage.generate_example(content)


def determine_node_and_children(
    flang_node: FlangAST,
    parent_node: BaseUserAST,
    node_index: int,
    spec: SpecificationKeyValueStore,
) -> BaseUserAST:
    assert flang_node is not None

    node_name = parent_node.generate_child_name(amount_of_duplicates=node_index)
    node_location = parent_node.join_paths(parent_node.location, node_name)

    if flang_node.type == "sequence":
        return (
            UserBranch(flang_ast_path=flang_node.location, name=node_name),
            flang_node.children,
        )
    elif flang_node.type == "choice":
        node = UserBranch(flang_ast_path=flang_node.location, name=node_name)
        index = get_choice_node(flang_node, node_location)

        return node, [flang_node.children[index]]
    elif flang_node.type == "text":

        if flang_node.get_bool_attrib("regex"):
            content = get_regex_content(flang_node, node_location)
        else:
            content = flang_node.get_attrib("value", flang_node.text)

        node = UserLeaf(
            flang_ast_path=flang_node.location, name=node_name, content=content
        )

        flang_ast_text = flang_node.get_attrib("value", flang_node.text)

        return (
            lex_storage.generate_example(flang_ast_text)
            if flang_node.get_bool_attrib("regex")
            else flang_ast_text
        )
    elif flang_node.type == "file":
        filename = flang_node.get_attrib("filename")
        return (
            lex_storage.generate_example(filename)
            if flang_node.get_attrib("variant") == "regex"
            else filename
        )

    raise RuntimeError


def generate_node_with_cardinality(
    flang_node: FlangAST, parent: BaseUserAST, spec: SpecificationKeyValueStore
) -> list[BaseUserAST]:
    quantity = get_node_cardinality()
    list_of_nodes = []

    for idx in range(quantity):
        node, children = determine_node_and_children(
            flang_node, parent, parent.location, spec
        )
        # node.name = node_name

        if children is not None:
            children_nodes = []

            for child in children:
                children_nodes += generate_node_with_cardinality(child, node, spec)

            node.children = children_nodes

        list_of_nodes.append(node)

    return list_of_nodes


def generate_ast_from_specification(
    flang_ast: FlangAST, specification: SpecificationKeyValueStore
): ...


def _join_children(content: list) -> list[VirtualFileRepresentation] | str:
    is_directory = None

    for item in content:
        if isinstance(item, str):
            assert (
                is_directory != True
            ), "Ast cannot contain strings and files. Cannot create directory with text content!"
            is_directory = False
        elif isinstance(item, VirtualFileRepresentation):
            assert (
                is_directory != False
            ), "Ast cannot contain strings and files. Cannot create directory with text content!"
            is_directory = True

    if is_directory:
        return [file for sublist in content for file in sublist]
    return "".join(content)


def _inner_materialize_ast(user_ast: BaseUserAST) -> VirtualFileRepresentation | str:
    if isinstance(user_ast, UserLeaf):
        return user_ast.content
    elif isinstance(user_ast, UserBranch):
        materialized = [_inner_materialize_ast(child) for child in user_ast.children]
        content = _join_children(materialized)

        return (
            VirtualFileRepresentation(name=user_ast.filename, content=content)
            if user_ast.filename
            else content
        )

    raise RuntimeError


def materialize_ast(user_ast: BaseUserAST, file_target: str | None = None):
    assert isinstance(user_ast, UserBranch)

    if file_target:
        user_ast.filename = file_target

    return _inner_materialize_ast()


def get_cardinality_key(location: str) -> str:
    return f"_card:{location}"


def get_cardinality(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
    node: FlangBranch,
    node_name: str,
):
    key = CHILDREN_KEY.format(node.location)

    if is_constant_cardinality(template):  # NOTE: Czy na pewno powinnismy to sprawdzac?
        assert node_name not in specification.get(
            key, {}
        ), f"Node with constant cardinality had it set manually. This {specification.get(key, {})} should not be set in specification {template}"
        return 1

    cardinality_dict = specification.get(key, {})

    if node_name in cardinality_dict:
        return cardinality_dict[node_name]

    return on_missing_value(template, key)


# def get_content(
#     template: TemplateTree,
#     specification: Specification,
#     on_missing_value: MissingSpecificationValueEvent,
#     name: str,
# ):
#     key = None

#     if template.type == "text":
#     elif template.type == "file":
#     # elif template.type == "choice":
#     #     key = CHOICE_INDEX_KEY.format(name)
#     #     if (chosen_index := specification.get(key)) is not None:
#     #         return chosen_index
#     elif template.type in ("sequence", ""):
#         return

#     if key is not None:
#         print(specification)
#         return on_missing_value(template, key)

#     raise ImpossibleOperationError(template.type)


# def get_node_and_children(
#     template: TemplateTree,
#     specification: Specification,
#     path_to_node: str,
#     on_missing_value: MissingSpecificationValueEvent,
# ) -> tuple[FlangAST, list[TemplateTree]]:
#     assert not isinstance(template, TemplateRoot)

#     if template.type == "use":
#         resolved_template = resolve_use_node(template)
#         node, children = get_node_and_children(
#             resolved_template, specification, path_to_node, on_missing_value
#         )
#         node.name = template.get_id()
#         node.template_id = template.location
#         return node, children

#     children = None
#     content = get_content(template, specification, on_missing_value, path_to_node)

#     if template.type == "text":
#         node = FlangLeaf(
#             name=template.get_id(), template_id=template.location, content=content
#         )
#     elif template.type == "sequence":
#         node = FlangBranch(name=template.get_id(), template_id=template.location)
#         children = get_available_children(template)
#     elif template.type == "file":
#         node = FlangBranch(
#             name=template.get_id(), template_id=template.location, filename=content
#         )
#         children = get_available_children(template)
#     elif template.type == "choice":
#         # NOTE: trzeba sie upewnic ze wpisywany indeks tez nie bieze pod uwage czy komponent jest ukryty
#         node = FlangBranch(name=template.get_id(), template_id=template.location)
#         assert not is_flang_node_hidden(child_node := template.children[content])
#         children = [child_node]

#         if children[0].get_bool_attrib("terminal"):
#             node.is_terminal = None
#     else:
#         raise Exception

#     return node, children


# def create_ast_for_children(
#     node: FlangAST,
#     children: list[TemplateTree],
#     specification: Specification,
#     on_missing_value: MissingSpecificationValueEvent,
#     ast_builder_callback: AstBuilderCallback,
# ):
#     for child in children:
#         cardinality = get_cardinality(
#             child,
#             specification,
#             on_missing_value,
#             node,
#             child.get_id(),
#         )

#         for _ in range(cardinality):
#             child_node_path = get_child_node_path(node, child)
#             node, children = get_node_and_children(
#                 child,
#                 specification,
#                 child_node_path,
#                 on_missing_value,
#             )
#             node.add_node(child_node)

#             child_node = ast_builder_callback(
#                 child,
#                 child_node_path,
#             )
#             # print(f"{ child_node_path=}")
#             # try:
#             # except Exception as e:
#             #     pass
#             #     raise e

#             assert child_node_path == child_node.location, (
#                 child_node_path,
#                 child_node.location,
#             )

#             if hasattr(child_node, "is_terminal"):
#                 break

#     return node

# def get_children_templates(
#     template: TemplateTree,
#     specification: Specification,
#     node_path: str,
#     on_missing_value: MissingSpecificationValueEvent,
# ):
#     if template.type == "use":
#         resolved_template = resolve_use_node(template)
#         children = get_children_templates(
#             resolved_template, specification, node_path, on_missing_value
#         )
#         return children
#     elif template.type == "choice":
#         content = get_content(template, specification, on_missing_value, node_path)
#         assert not is_flang_node_hidden(child_node := template.children[content])
#         if child_node.get_bool_attrib("terminal"):
#             child_node.is_terminal = None

#         return [child_node]

#     return get_available_children(template) if template.children else None


# def create_children_for_ast(
#     template: TemplateTree,
#     node: FlangAST,
#     specification: Specification,
#     on_missing_value: MissingSpecificationValueEvent,
# ) -> FlangAST:
#     # node, children = get_node_and_children(
#     #     template,
#     #     specification,
#     #     path,
#     #     on_missing_value,
#     # )

#     # if template.type == "use":
#     #     target_template = resolve_use_node(template)
#     #     return create_ast(target_template, specification, on_missing_value)
#     # elif isinstance(template, TemplateRoot):
#     #     node = FlangRoot()
#     # else:
#     #     node = get_node(
#     #         child_template,
#     #         specification,
#     #         on_missing_value,
#     #     )

#     # children_templates = get_children_templates(node.location)

#     if template.type == "use":
#         tempe = resolve_use_node(template)

#     if tempe.children:
#         children = []

#         get_cardinality(tempe, specification, on_missing_value)

#         for child_template in tempe.children:

#             for _ in range(
#                 get_cardinality(
#                     child_template, specification, on_missing_value, node, node.location
#                 )
#             ):
#                 child_node = get_node(
#                     child_template,
#                     specification,
#                     on_missing_value,
#                 )
#                 children.append(child_node)
#                 # node.add_node(child_node)

#     return node

#     for child_template in children_templates:
#         child_node_path = get_child_node_path(node, child_template)
#         child_node = get_node(
#             child_template,
#             specification,
#             on_missing_value,
#         )
#         node.add_node(child_node)
#         assert child_node_path == child_node.location, (
#             child_node_path,
#             child_node.location,
#         )

#     for child_node in node.children:
#         create_ast(child_node, specification, on_missing_value)

#     return node

# create_ast_for_children(
#     node,
#     children_templates,
#     specification,
#     on_missing_value,
#     lambda child, child_path: create_ast(
#         child, specification, child_path, on_missing_value
#     ),
# )

# return node


# def get_node(
#     template: TemplateTree,
#     specification: Specification,
#     node_path: str,
#     on_missing_value: MissingSpecificationValueEvent,
# ):
#     assert not isinstance(template, TemplateRoot)

#     if template.type == "use":
#         resolved_template = resolve_use_node(template)
#         node = get_node(resolved_template, specification, node_path, on_missing_value)
#         node.name = template.get_id()
#         node.template_id = template.location
#         return node

#     if template.type == "text":
#         key = TEXT_CONTENT_KEY.format(node_path)

#         if content := specification.get(key):
#             pass
#         elif not template.get_bool_attrib("regex"):
#             content = template.get_attrib("value", template.text)
#         elif "default" in template.attributes:
#             content = template.attributes["default"]

#         node = FlangLeaf(
#             name=template.get_id(), template_id=template.location, content=content
#         )
#     elif template.type in ["sequence", "choice"]:
#         node = FlangBranch(name=template.get_id(), template_id=template.location)
#     elif template.type == "file":
#         key = FILENAME_KEY.format(node_path)

#         if filename := specification.get(key):
#             pass
#         elif not template.get_bool_attrib("regex"):
#             filename = template.get_attrib("pattern")
#         elif "default" in template.attributes:
#             filename = template.attributes["default"]

#         node = FlangBranch(
#             name=template.get_id(), template_id=template.location, filename=filename
#         )
#     else:
#         raise Exception

#     return node
