from utils import some_utilities


def test1(context, **kwargs):
    context["result"] = "success"
    return None


def test(context, **kwargs):
    # should throw error
    return 1


def event2(context, **kwargs):
    context["result"] = kwargs["local_content"] + "1"
    return context
