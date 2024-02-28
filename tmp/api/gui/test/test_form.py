import pytest

from copy import deepcopy

from .. import form, Form

assert form.Form is Form


_widgets_defaults = {

    'string': {
        'type': form.widgets.Text,
        'value': ""
    },

    'number': {
        'type': form.widgets.FloatText, 
        'value': 0
    },

    'array': {
        'type': form.widgets.VBox,
        'value': []
    }
}


def test_empty():
    """
    An empty schema should raise an error
    """
    with pytest.raises(TypeError, match=r"missing .* 'schema'") as excinfo:
        Form()

    with pytest.raises(AssertionError, match="type") as excinfo:
        Form(schema={})


def test_schema_type():
    """
    Form is made to work with 'object' types
    """
    schema = {
        'type': 'other_than_object'
    }
    with pytest.raises(TypeError) as excinfo:
        Form(schema)

    schema['type'] = 'object'
    # 'properties' should be there also
    with pytest.raises(AssertionError, match="properties") as info:
        Form(schema)

    schema['properties'] = {}
    Form(schema)


def test_empty_object():
    """
    Form from empty object properties is a valid, empty Form
    """
    schema = {
        'type': 'object',
        'properties': {}
    }
    f = Form(schema)

    assert isinstance(f, dict), f
    assert len(f) == len(schema['properties'])
    assert isinstance(f.widget, (form.widgets.Widget))
    assert isinstance(f.widget, (form.widgets.VBox)) # default, VBox


def _check_default_types_in_properties(_f, _props:dict):
    """
    Checks if widgets (in properties) have the expected default type/value
    """
    for prop_name, prop_obj in _props.items():
        _js_type = prop_obj['type']
        assert prop_name in _f 
        assert isinstance(_f[prop_name], _widgets_defaults[_js_type]['type'])
        assert _f[prop_name].value == _widgets_defaults[_js_type]['value']


def test_string_property():
    """
    Test optional string field
    """
    schema = {
        'type': 'object',
        'properties': {
            'word': { 'type': 'string'}
        }
    }
    f = Form(schema)

    assert isinstance(f, dict), f
    assert len(f) == len(schema['properties'])
    # assert 'word' in f
    # assert f['word'].value == ''
    _check_default_types_in_properties(f, schema['properties'])


def test_number_property():
    """
    Test optional number field
    """
    schema = {
        'type': 'object',
        'properties': {
            'num': { 'type': 'number'}
        }
    }
    f = Form(schema)

    assert isinstance(f, dict), f
    assert len(f) == len(schema['properties'])
    # assert 'num' in f
    # assert type(f['num']) == _widgets_defaults['number']['type']
    # assert f['num'].value == _widgets_defaults['number']['value']
    _check_default_types_in_properties(f, schema['properties'])


def test_array_property():
    """
    Test array-items field
    """
    schema = {
        'type': 'object',
        'properties': {
            'arr': { 'type': 'array' }
        }
    }

    # Array elements demand 'items' field...
    with pytest.raises(AssertionError):
        Form(schema)

    # ... and only 'items':
    with pytest.raises(AssertionError):
        _schema = deepcopy(schema)
        _schema['properties']['arr'].update({'prefixItems': [{}]})
        Form(_schema)

    with pytest.raises(AssertionError):
        _schema = deepcopy(schema)
        _schema['properties']['arr'].update({'items': {}})
        Form(_schema)


def test_array_items():
    schema = {
        'type': 'object',
        'properties': {
            'arr': { 
                'type': 'array',
                'items': {
                    'type': 'string'
                }
            }
        }
    }

    f = Form(schema)

    assert isinstance(f, dict), f
    assert len(f) == len(schema['properties'])
    _check_default_types_in_properties(f, schema['properties'])


def test_the_whole_thing():
    """
    Test a workflow
    """
    # The schema for GMAP metadata (https://wiki.europlanet-gmap.eu/bin/view/Main/Documentation/Map-wide%20metadata/).
    #
    schema = {
        "type": "object",
        
        "properties": {
            'title': {
                "type": "string",
                "description": "A title"
            },

            'authors': {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "lastname": {"type": "string"},
                        "firstname": {"type": "string"}
                    }
                },
                "minItems": 1
            },

            'publication_date': {
                "description": "Publication date",
                "type": "string",
                "format": "date"
            },

            'bbox_lon_west': {
                "description": "West Longitude",
                "type": "number",
                "minimum": -180,
                "maximum": 180
            }, 

            'bbox_lon_east': {
                "description": "East Longitude",
                "type": "number",
                "minimum": -180,
                "maximum": 180
            },

            'bbox_lat_min': {
                "description": "Min Latitude",
                "type": "number",
                "minimum": -90,
                "maximum": 90
            }, 

            'bbox_lat_max': {
                "description": "Max Latitude",
                "type": "number",
                "minimum": -90,
                "maximum": 90
            }, 

            'map_type': {
                "description": "Map type",
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "Integrated",
                        "Morphologic",
                        "Compositional",
                        "Digital model",
                        "Stratigraphic",
                        "Geo-structural",
                    ]
                },
                "minItems": 1,
                "uniqueItems": True
            },

            'target': {
                "description": "Target body",
                "type": "string",
                "enum": ['Mars', 'Mercury', 'Moon', 'Venus']
            },

            'ID': {
                "type": "string",
                "readOnly": True
            }
        },
        
        "required": [
            "ID",
            "target",
            "map_type",
            "authors",
            "title",
        ]
    }

    f = Form(schema)
    with pytest.raises(AssertionError):
        data = f.to_json()