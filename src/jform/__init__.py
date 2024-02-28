from . import _version
__version__ = _version.get_versions()['version']

from typing import Any, Union


class JForm:
    _schema:dict = None

    def __init__(self, schema:dict):
        """
        Create widget(s) from schema
        """

        assert 'type' in schema, "Expect attribute 'type' in schema"
        # if schema['type'] != 'object':
        #     raise TypeError("Expected schema['type']='object'")

        super().__init__()

        attribute_widgets = schema2ipywidgets.main(schema)
        print(attribute_widgets)

        self.update(attribute_widgets)

        self._schema = schema
