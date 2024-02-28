"""
Functions to transform a JSON-schema to IPython-Widgets
"""
from ipywidgets import (
    Widget,
    Dropdown,
    Text,
    FloatText,
    VBox
)


class BaseForm(object):
    _schema:dict = None

    def __init__(self, schema:dict):
        self._schema = schema

    @propert
    def schema(self):
        return self._schema


class StringForm(Text,BaseForm):
    def __init__(self, schema):
        super().__init__(schema)


def schema2widget(schema:dict) -> Widget:
    assert isinstance(obj, dict), obj

    # First, let's validate the schema
    assert validate_schema(obj)

    if 'enum' in obj:
        return DropdownForm(obj)

    match obj['type']:
        case 'string':
            return StringForm(obj)
        case 'number':
            wcls = NumberForm(obj)
        case 'array':
            wcls = ArrayForm(obj)
        case 'object':
            res = ObjectForm(obj)

    if not isinstance(res, dict):
        assert isinstance(res, widgets.Widget)
        res = { res.description: res}
        assert None, res

    return res


def _string(obj:dict, **kwargs):
    """
    Return a Text iPywidget
    """
    if 'enum' in obj:
        w_cls = widgets.Dropdown
        kwargs.update({'options': obj['enum']})
    else:
        w_cls = widgets.Text

    return make_widget(obj, widget_class=w_cls, **kwargs)


def _number(obj:dict, **kwargs):
    """
    Return a FloatText iPywidget
    """
    w_cls = widgets.FloatText
    return make_widget(obj, widget_class=w_cls, **kwargs)


def make_widget(obj:dict, widget_class, **kwargs):
    ro = obj['readOnly'] if 'readOnly' in obj else False

    name = kwargs.pop('name', obj['type'].title())
    description = name.replace('_', ' ').title()

    required = kwargs.pop('required', False)
    if required:
        description = F'<strong style="color:red">{description}</strong>'
    if ro:
        description = F'<i>{description}</i>'

    kwargs.update(dict(
        description = description,
        description_allow_html = True,
        disabled = ro
    ))

    try:
        widget = widget_class(**kwargs)
    except:
        print(obj)
        raise

    return widget
