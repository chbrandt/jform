import json
import ipywidgets as widgets

from collections import UserDict
from pathlib import Path
from typing import Any, Union

from . import schema2ipywidgets


# def read_planmap_json(metafile:Union[str,Path]) -> dict:
#     """Return JSON object from 'meta_file'"""
#     filename = Path(metafile)
#     with open(filename) as fp:
#         js = json.load(fp)
#     return js


# def set_data_to_form(json, form):
#     for field, value in json.items():
#         form.set(field, value)


def assemble_widgets(form, layout:Union[str,list,dict,None]):
    """Layout widgets"""
    if isinstance(layout, str):
        return form[layout]

    if isinstance(layout, list):
        _wdgts = [ assemble_widgets(form, l) for l in layout ]
        print(_wdgts)
        return widgets.VBox(_wdgts)

    if isinstance(layout, dict):
        _w = []
        for label in layout:
            _w.append(widgets.Label(label))
            _w.append(assemble_widgets(form, layout[label]))
        return widgets.VBox(_w)

    if layout is None:
        fields = [ field for field in form ]
        print(fields)
        return assemble_widgets(form, fields)


class Form(dict):
    """
    Given a JSON-Schema, create form input widgets accordingly
    """
    _widget = None
    _schema = None

    def __init__(self, schema:Union[dict,None], layout:Union[list,None] = None):
        """
        Create widgets following 'layout' (if given).
        """

        assert 'type' in schema, "Expect attribute 'type' in schema"
        if schema['type'] != 'object':
            raise TypeError("Expected schema['type']='object'")

        super().__init__()

        attribute_widgets = schema2ipywidgets.main(schema)
        print(attribute_widgets)

        self.update(attribute_widgets)

        self._schema = schema

        self.set_layout(layout)

    def set_layout(self, layout):
        self._widget = assemble_widgets(self, layout)

    def set(self, field:str, value:Any) -> bool:
        """Set 'value' to 'field'"""
        assert field in self
        wdgt = self[field]
        wdgt.value = value

    def add(self, field:str, value:Any) -> bool:
        """
        Add 'value' to 'field' if it's a container, if not, return False.
        """
        raise NotImplementedError

    def get(self, field:str) -> Any:
        """Return value in 'field'"""
        return self[field].value

    def read_json(self, js):
        """
        Set form/data (field/value) with JSON content.
        """
        if isinstance(js, (str,Path)):
            with open(js) as fp:
                js = json.load(fp)
        # # Validate the (JSON) filename against self._schema
        # assert schema2ipywidgets.validate_json(js, self._schema)
        for k,v in js.items():
            self.set(k,v)

    def to_json(self):
        js = {}
        for k,v in self.items():
            js[k] = v.value if not isinstance(v.value, tuple) else list(v.value)
        assert schema2ipywidgets.validate_json(js, self._schema)
        return js

    @property
    def widget(self):
        """Return Form "app" """
        return self._widget



# widget_types = dict(
#     text = widgets.Text,
#     float = widgets.FloatText,
#     datetime = widgets.DatePicker,
#     items_one = widgets.Combobox,
#     items_multiple = widgets.SelectMultiple,
# )

# wt = widget_types


# def create_main_widgets() -> dict:
#     from datetime import date

#     map_types = {
#         "Integrated": "I",
#         "Morphologic": "M",
#         "Compositional": "C",
#         "Digital model": "D",
#         "Stratigraphic": "S",
#         "Geo-structural": "G",
#     }

#     d = dict(

#         title = wt['text'](
#             description = "Map title",
#             continuous_update = False
#         ),

#         target = wt['items_one'](
#             options = ['Mars', 'Mercury', 'Moon', 'Venus'],
#             placeholder = "Choose the planet/satelite",
#             description = "Target body",
#             continuous_update = False
#         ),

#         shortname = wt['text'](
#             description = "Shortname",
#             continuous_update = False
#         ),

#         publication_date = wt['datetime'](
#             value = date.today(),
#             description = "Publication date"
#         ),

#         map_type = wt['items_multiple'](
#             options = sorted(map_types.keys()),
#             description = "Map type"
#         ),

#         # authors = schema2ipywidgets.Items("Author (fullname)").widget,
#         authors = schema2ipywidgets.Items("Author (fullname)"),


#         bbox_lon_west = wt['float'](description = "West-Lon"),
#         bbox_lon_east = wt['float'](description = "East-Lon"),
#         bbox_lat_min = wt['float'](description = "Min-Lat"),
#         bbox_lat_max = wt['float'](description = "Max-Lat"),

#         doi = wt['text'](description="DOI")

#     )

#     def create_gmapID_readonly(target_wgt, map_type_wgt, shortname_wgt, map_types_map):
#         gmap_id = wt['text'](
#             description = '<i style="color:gray">GMAP-ID</i>',
#             description_allow_html = True,
#             disabled = True
#             )

#         def on_change_value(change):
#             _target = target_wgt.value.strip().title()
#             _type = ''.join([map_types_map[t].upper() for t in map_type_wgt.value ])
#             _sname = shortname_wgt.value.strip().replace(' ','-').title()
#             _id = ["GMAP", _type, _target, _sname]
#             if not all(_id):
#                 # gmap_id.value = "GMAP_<target>_<type>_<shortname>"
#                 gmap_id.value = ""
#             else:
#                 gmap_id.value = '_'.join(_id)

#         target_wgt.observe(on_change_value, names='value')
#         shortname_wgt.observe(on_change_value, names='value')
#         map_type_wgt.observe(on_change_value, names='value')

#         return gmap_id

#     d['gmap_id'] = create_gmapID_readonly(
#             target_wgt= d['target'],
#             map_type_wgt= d['map_type'],
#             shortname_wgt= d['shortname'],
#             map_types_map= map_types
#         )

#     return d


# def create_other_widgets():

#     d = dict(
#         description = widgets.Textarea(description="Short description of the map"),
#         aims = widgets.Textarea(description="Goal of this map"),
#         units = widgets.Textarea(description="Units color definition"),
#         stratigraphic_info = widgets.Textarea(description="Map stratigraphic elements"),

#         output_scale = widgets.Text(description="Output scale"),
#         crs = widgets.Textarea(description="Original CRS"),

#         ancillary_data = widgets.Textarea(description="Data used"),
#         related_products = widgets.Textarea(description="Related maps"),
#         heritage = widgets.Textarea(description="Heritage information"),
#         extra_data = widgets.Textarea(description="Links to other data"),

#         standards = widgets.Textarea(description="Standards"),
#         comments = widgets.Textarea(description="Notes, errata, caveats"),
#         acknowledge = widgets.Textarea(description="Acknowledgement"),
#     )

#     return d
