import ipywidgets as widgets
from typing import Any, Union


def main(obj:dict) -> dict:
    """
    Return a representation of 'obj' schema with widgets to be used in Form
    """

    assert isinstance(obj, dict), obj
    # assert obj['type'] == 'object', obj

    # First, let's validate the schema
    assert validate_schema(obj)

    res = _handlers[obj['type']](obj)
    # res = _object(obj)

    if not isinstance(res, dict):
        assert isinstance(res, widgets.Widget)
        res = { res.description: res}
        assert None, res

    assert isinstance(res, dict)
    return res


def validate_schema(schema:dict) -> bool:
    from ..json_schema import validate
    try:
        validate.check_schema(schema)
    except Exception as err:
        print(err)
        return False
    else:
        return True


def validate_json(obj:dict, schema:dict) -> bool:
    from jsonschema import validate
    try:
        validate(instance=obj, schema=schema)
    except Exception as err:
        print(err)
        return False
    else:
        return True


def _object(obj:dict, name:str=None, required:bool=False) -> dict:
    """
    Process an 'object' element

    >>> _object({
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"const": "dataset"},
                "date": {"type": "string", "format": "date"}
            },
            "required": ["name"]
        })
    """
    def _properties(obj:dict, required:list = None) -> dict:
        """
        Example:
        >>> _properties(
            obj = {
                "name": {"type": "string"},
                "type": {"const": "dataset"},
                "date": {"type": "string", "format": "date"}
            },
            required = ['name']
            )
        """
        required = set(required) if required else set()
        _props = {}
        for name, prop_obj in obj.items():
            _props[name] = _property(prop_obj, name, required=name in required)
        return _props


    def _property(obj:dict, name:str, required:bool = False):
        """
        Return an widget object according to "obj['type']"

        >>> _property( {"type":"string"} )
        """
        # check supported attributes
        supported_fields = ('type', 'oneOf')
        assert any([ k in obj for k in supported_fields ]), obj
        if 'type' in obj:
            _widget = _handlers[obj['type']](obj, name=name, required=required)
        else:
            assert 'oneOf' in obj, "The only supported optionals are 'oneOf'"
            _widgets = [ _handlers[o['type']](o) for o in obj['oneOf'] ]
            _widget = { 'oneOf': _widgets }
            assert None, "TODO: review this '_widget' dictionary here"
        return _widget

    # Check object's fields
    #
    mandatory_fields = ['type', 'properties']
    missing_fields = list(filter(lambda f:f not in obj, mandatory_fields))
    assert len(missing_fields) == 0, f"Missing fields in {obj}: {missing_fields}"
    assert obj['type'] == 'object'

    props = _properties(obj['properties'])
    if name:
        return {name: props}
    else:
        return props


def _array(obj:dict, name:str, required:bool) -> list:
    """
    Return a container for items' Params
    """
    # check mandatory fields
    assert all([ k in obj for k in ['type', 'items'] ]), obj
    assert obj['type'] == 'array', obj

    return _items(obj['items'], name=name, required=required,
                  minItems = obj.get('minItems', None))


# def _items(obj:dict, name:str, required:bool, minItems=None, maxItems=None):
def _items(obj:dict, **kwargs):
    """
    Return a list of "param types"
    """
    # assert obj['type'] != 'array'
    assert len(obj) > 0, "Expected non-empty 'items' array"

    name = kwargs['name']

    if 'enum' in obj:
        w_cls = widgets.SelectMultiple
        kwargs.update({'options': obj['enum']})
        return make_widget(obj, w_cls, **kwargs)

    if 'type' in obj:
        # Items have all the same schema
        return Items(obj, description=name.title())

    msg = F"I don't know how to handle these 'items' ({name}): {obj}"
    raise NotImplementedError(msg)

# def _string(obj:dict, name:str, required:bool):
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


_handlers = {
    'string': _string,
    'number': _number,
    'array': _array,
    'object': _object,
}


def _date(val, *args) -> tuple:
    """
    Return 'val' (and *args) as datetime.date object if not yet (eg, 'YYYY-MM-DD')
    """
    import datetime

    if val:
        assert isinstance(val, (str, datetime.date))
        val = datetime.date.fromisoformat(val) if isinstance(val, str) else val
    else:
        # val = datetime.date.today()
        val = val

    return (val, *args)


_format_args = {
    "date": _date
}

_wdgt_classes = {
    "string": widgets.Text,
    "date": widgets.DatePicker
}

# def _param(obj_type, *args, **kwargs):
#     """
#     Return Widgets object according to '_param_classes' and 'obj_type'.

#     Input:
#         *args :
#     """
#     wdgt_class = _wdgt_classes[obj_type]
#     _format = _format_args.get(obj_type)
#     args = _format(*args) if _format else args
#     return wdgt_class(*args, **kwargs)



@widgets.register
class Object(widgets.HBox):
    def __init__(self, obj:dict):
        assert obj['type'] == 'object'
        self._schema = obj

        prop_widgets = _handlers[obj['type']](obj)
        assert isinstance(prop_widgets, dict)
        self._widgets = prop_widgets

        super().__init__(list(self._widgets.values()))

    @property
    def value(self):
        return {f:w.value for f,w in self._widgets.items()}

    @value.setter
    def value(self, value:dict):
        assert isinstance(value, dict), f"Expected a dictionary, instead got {type(value)}"
        self._widgets = self._widgets | value

    def is_empty(self):
        return any(not bool(v) for v in self.value.values())




@widgets.register
class Items(widgets.VBox):
    """
    Manage a list of objects ('obj'), provide add/del widgets
    """

    def __init__(self, obj:dict, description = "Text field"):
        """
        Initiate list of objects with an 'Add' button, to create 'obj' widgets.

        Args:
        - obj : a json object (type 'object/string/number/...')
        - description : widget label if obj.type != 'object'
        - *kw* : forward to base class
        """
        from copy import copy, deepcopy
        self._schema = deepcopy(obj)       # save json object (private)
        self._obj = self._schema
        self.description = description  # save description (public)

        add_btn = widgets.Button(icon="plus")
        add_btn.on_click(lambda btn: self.add_item())

        del_btn = widgets.Button(icon="trash")
        del_btn.on_click(lambda btn: self.del_sel_items())

        # save list controls
        self._controls = [add_btn,del_btn]
        self._items = []                #

        super().__init__(copy(self._controls))

    # def _del(self, id_):
    #     _ = self._items.pop(id_)    # _ is the item being removed from children
    #     nctrl = len(self._controls)
    #     self.children = self.children[:nctrl] + tuple(self._items.values())

    def del_sel_items(self):
        indexes = [i for i,item in enumerate(self._items) if item.is_selected()]
        indexes = indexes[::-1]
        for i in indexes:
            self.del_item(i)

        return self

    def del_item(self, index:int):
        if abs(index) >= len(self._items):
            raise IndexError(f"Index out of range (0:{len(self._items)-1})")

        _ = self._items.pop(index)
        nctrl = len(self._controls)
        self.children = self.children[:nctrl] + tuple(self._items.values())
        return self


    def add_item(self, value:Union[dict,str,None] = None):
        """
        Create new widget and add in Baseclass children list

        Args:
        - value : default value
        """
        # Create new items only if there are no empty ones
        if any(item.is_empty()
                for item in self.children
                if hasattr(item, 'children')):
            return self

        new_item = Item(self._schema)

        self._items.append(new_item)
        print(self._items)
        self.children = self.children + (new_item,)
        return self

    def clear(self):
        """Remove all items (but the '+' button)"""
        self._items = {}
        nctrl = len(self._controls)
        self.children = self.children[:nctrl]
        return self

    @property
    def value(self):
        try:
            value = [ item.value for item in self._items.values() ]
        except Exception as err:
            print("XXX", self._items)
            raise
        return value

    @value.setter
    def value(self, value:Union[dict,list,str,int,float]):
        # assert isinstance(value, (dict,list)), "Expected a list or dictionary."
        self.clear()
        if not isinstance(value, (list,tuple)):
            self.add_item(value)
        else:
            for val in value:
                self._add(val)



@widgets.register
class Item(widgets.HBox):
    """
    Create an Item for Items, provide a del widget for self-delete
    """

    def __init__(self, obj:dict):
        assert isinstance(obj, dict), obj

        wdgt = Object(obj)
        assert isinstance(wdgt, widgets.Widget)

        # Create a Del button to self-delete
        # del_btn = widgets.Button(icon="trash")
        # del_btn.on_click(lambda btn: items._del(id(self)))
        sel_btn = widgets.Checkbox()

        # Each entry, then, is a pair of value-widget and del-btn
        super().__init__([wdgt, sel_btn])

    @property
    def value(self):
        return self.children[0].value

    @value.setter
    def value(self, value:Union[dict,list,str,int,float]):
        self.children[0].value = value

    def is_empty(self):
        return self.children[0].is_empty()

    def is_selected(self):
        return self.children[1].value
