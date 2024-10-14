from utils import some_utilities


def test1(context, **kwargs):
    context["result"] = "success"
    return None


def test2(context, **kwargs):
    # should throw error
    return 1
