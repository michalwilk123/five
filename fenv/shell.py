from flang.helpers import convert_to_bool
from flang.structures import FlangConstruct, FlangObject


class FenvShell:
    def __init__(
        self, flang_object: FlangObject, root: FlangConstruct | None = None
    ) -> None:
        self.root = root or flang_object.root_construct
        self.flang_object = flang_object

    def start(self):
        return self.create(self.root)

    def create(self, construct: FlangConstruct):
        match construct.construct_name:
            case "component":
                text = ""
                while True:
                    print(f"Generating {construct.name}")
                    text += "".join(
                        self.create(child)
                        for child in self.flang_object.iterate_children(
                            construct.location
                        )
                    )

                    if not construct.get_bool_attrib("multi") or not convert_to_bool(
                        input("Continue?: ")
                    ):
                        break

                return text
            case "regex":
                if construct.name:
                    return input(f"{construct.name}: ")
                elif default := construct.get_attrib("default"):
                    return default
                else:
                    raise RuntimeError
            case "text":
                return construct.text
