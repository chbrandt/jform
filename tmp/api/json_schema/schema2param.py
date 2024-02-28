"""
Translates a JSONSchema document (without $refs) into an equivalent Params model
"""
import param


# Parameters metadata:
# - https://param.holoviz.org/user_guide/Parameters.html#parameter-metadata
#

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

_param_classes = {
    "string": param.String,
    str: param.String,
    int: param.Integer,
    "date": param.CalendarDate
}

def _param(obj_type, *args, **kwargs) -> param.Parameterized:
    print(args, kwargs)
    _class = _param_classes[obj_type]
    _format = _format_args.get(obj_type)
    args = _format(*args) if _format else args
    return _class(*args, **kwargs)


# def _string(obj):
#     assert 'type' in obj
#     assert obj['type'] == 'string'
#
#     obj_type = obj['type']
#
#     if 'format' in obj:
#         obj_type = obj['format']
#     elif 'const' in obj:
#         default_value = obj['const']
#         obj_type = type(default_value)
#         kwargs.update({ 'constant': True})

def _property(obj, name, required=False) -> param.Parameterized:
    """
    Return a "Param(*args, **kwargs)" object according to "obj['type']"

    >>> _property( {"type":"string"} )
    """
    assert any([ k in obj for k in ('type', 'const', 'oneOf') ]), obj

    kwargs = {}
    if 'type' in obj:
        obj_type = obj['type']

        if obj_type == 'array':
            param_container = _array(obj)
            param_obj = param_container

        elif obj_type == 'object':
            param_obj = _object(obj)

        else:
            kwargs.update({ "allow_None": not required })
            default_value = None

            if 'format' in obj:
                obj_type = obj['format']
            elif 'const' in obj:
                default_value = obj['const']
                kwargs.update({ 'constant': True})

            doc = obj.get('$comment', None)
            kwargs.update({ 'doc': doc })

            param_obj = _param(obj_type, default_value, **kwargs)

    elif 'const' in obj:
        default_value = obj['const']
        obj_type = type(default_value)
        kwargs.update({ 'constant': True})
        param_obj = _param(obj_type, default_value, **kwargs)

    else:
        assert 'oneOf' in obj, obj
        param_objs = [ _handlers[o['type']](o) for o in obj['oneOf'] ]
        # param_obj = param.Selector(param_objs)
        # param_obj = param_objs
        param_obj = { 'oneOf': param_objs }

    return param_obj


def _properties(obj, required:list=None) -> dict:
    """
    >>> _properties({"name": {"type": "string"}, "type": {"const": "dataset"}, "date": {"type": "string", "format": "date"}})
    """
    required = set(required) if required else set()
    print(required)
    _props = {}
    for name, prop in obj.items():
        _props[name] = _property(prop, name, required=name in required)

    return _props


def _object(obj:str) -> dict:
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
    # check mandatory fields
    assert all([ k in obj for k in ['type', 'properties'] ])
    assert obj['type'] == 'object'

    props = _properties(obj['properties'],
                        required = obj.get('required', None))
    return props


def _items(obj, minItems=None) -> param.Parameterized:
    """
    Return a list of "param types"
    """
    assert 'type' in obj
    assert obj['type'] != 'array'

    param_obj = _handlers[obj['type']](obj)
    return param_obj


def _array(obj) -> list:
    """
    Return a container for items' Params
    """
    # check mandatory fields
    assert all([ k in obj for k in ['type', 'items'] ])
    assert obj['type'] == 'array'

    items = [_items(obj['items'],
                    minItems = obj.get('minItems', None))]
    return items


_handlers = {
    'object': _object,
    'array': _array,
    # 'string': _string,
    # str: _string,
}


def main(obj) -> dict:
    assert isinstance(obj, dict)
    res = _handlers[obj['type']](obj)
    return res
