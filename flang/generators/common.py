from flang.structures import TemplateTree

TEXT_CONTENT_KEY = "{}:content"
CHOICE_INDEX_KEY = "{}:choice-index"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"


def is_constant_cardinality(template: TemplateTree) -> bool:
    return template.get_bool_attrib("hidden") or not (
        "multi" in template.attributes or "optional" in template.attributes
    )
