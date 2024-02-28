from IPython.display import display

import ipywidgets as widgets

# from collections import UserList

class Items(object):

    def __init__(self, item_description="Text field"):
        
        add_btn = widgets.Button(icon="plus")

        def add_input_widget(btn):
            """Create new Text input widget in items"""
            text = widgets.Text(description = item_description)
            del_btn = widgets.Button(icon="trash")
            del_btn.on_click(lambda btn: self.del_item(text.value))

            new_item = widgets.HBox([text, del_btn])
            
            if all(item.children[0].value.strip() for item in self.widget.children if hasattr(item, 'children')):
                self.widget.children = tuple(list(self.widget.children) + [new_item])
            # self.widget.children = tuple(list(items) + [new_item])
            
        add_btn.on_click(add_input_widget)

        self._widget = widgets.VBox([add_btn])
        
    def del_item(self, value):
        def not_value(item):
            try:
                found = item.children[0].value == value
            except:
                found = False
            return not found
        
        new_items = filter(not_value, self.widget.children)
        self._widget.children = tuple(new_items)
        
    @property
    def widget(self):
        return self._widget
        

# display(Items().widget)

title = widgets.Text(
    description = "Map title",
    continuous_update = False
)

target = widgets.Combobox(
    options = ['Mars', 'Mercury', 'Moon', 'Venus'],
    placeholder = "Choose the planet/satelite",
    description = "Target body",
    continuous_update = False
)

shortname = widgets.Text(
    description = "Shortname",
    continuous_update = False
)

from datetime import date

publication_date = widgets.DatePicker(
    value = date.today(),
    description = "Publication date"
)

map_types = {
    "Integrated": "I",
    "Morphologic": "M",
    "Compositional": "C",
    "Digital model": "D",
    "Stratigraphic": "S",
    "Geo-structural": "G",
}

map_type = widgets.SelectMultiple(
    options = sorted(map_types.keys()),
    description = "Map type"
)

gmap_id = widgets.Text(
    description = '<i style="color:gray">GMAP-ID</i>', 
    description_allow_html = True,
    disabled = True
    )

def on_change_value(change):
    _target = target.value.strip().title()
    _type = ''.join([map_types[t].upper() for t in map_type.value ])
    _sname = shortname.value.strip().replace(' ','-').title()
    _id = ["GMAP", _type, _target, _sname]
    if not all(_id):
        # gmap_id.value = "GMAP_<target>_<type>_<shortname>"
        gmap_id.value = ""
    else:
        gmap_id.value = '_'.join(_id)

target.observe(on_change_value, names='value')
shortname.observe(on_change_value, names='value')
map_type.observe(on_change_value, names='value')


# add_author_button = widgets.Button(
#     description = 'Add Author',
# )

# def add_author_widget(btn):
#     author = widgets.Text(
#         description = "Author (fullname)"
#     )
#     authors_widgets.children = tuple(list(authors_widgets.children) + [author])
        
# add_author_button.on_click(add_author_widget)

# authors_widgets = widgets.VBox([add_author_button])

authors_widgets = Items("Author (fullname)").widget

bbox_lon_widgets = widgets.VBox([
    widgets.Label("Longitude (west,east) [-180:180]"),
    widgets.VBox([
        widgets.FloatText(description = "West-Lon"),
        widgets.FloatText(description = "East-Lon")
    ])
])

bbox_lat_widgets = widgets.VBox([
    widgets.Label("Latitude (min,max) [-90:90]"),
    widgets.VBox([
        widgets.FloatText(description = "Min-Lat"),
        widgets.FloatText(description = "Max-Lat")
    ])
])

bbox_widgets = widgets.VBox([
    bbox_lon_widgets,
    bbox_lat_widgets
])

doi = widgets.Text(description="DOI")

form_main = widgets.TwoByTwoLayout(
    top_left = widgets.VBox([
        title,
        shortname,
        map_type,
        target,
        bbox_widgets,
        publication_date,
        doi,
        authors_widgets,
    ])
)

# widgets.VBox([gmap_id, form_main])

descr = dict(
    description = widgets.Textarea(description="Short description of the map"),
    aims = widgets.Textarea(description="Goal of this map"),
    units = widgets.Textarea(description="Units color definition"),
    stratigraphic_info = widgets.Textarea(description="Map stratigraphic elements"),

    output_scale = widgets.Text(description="Output scale"),
    crs = widgets.Textarea(description="Original CRS"),

    ancillary_data = widgets.Textarea(description="Data used"),
    related_products = widgets.Textarea(description="Related maps"),
    heritage = widgets.Textarea(description="Heritage information"),
    extra_data = widgets.Textarea(description="Links to other data"),

    standards = widgets.Textarea(description="Standards"),
    comments = widgets.Textarea(description="Notes, errata, caveats"),
    acknowledge = widgets.Textarea(description="Acknowledgement"),
)

form_descr = widgets.Accordion(
    children = [
        widgets.VBox([
            descr['description'],
            descr['aims'],
            descr['units'],
            descr['stratigraphic_info'],
        ]),
        widgets.VBox([
            descr['crs'],
            descr['output_scale']
        ]),
        widgets.VBox([
            descr['ancillary_data'],
            descr['related_products'],
            descr['heritage'],
            descr['extra_data'],
        ]),
        widgets.VBox([
            descr['standards'],
            descr['comments'],
            descr['acknowledge'],
        ])
    ]
)

titles = [
    "Map description",
    "Spatial attributes",
    "Ancillary data",
    "Notes"
]

for i,bx in enumerate(form_descr.children):
    form_descr.set_title(i, titles[i])
    
form_descr.selected_index = None
# form_descr

# app = widgets.AppLayout(
#     header = gmap_id,
#     center = widgets.VBox([
#         form_main,
#         form_descr
#     ]),
#     left_sidebar = None,
#     right_sidebar = None,
#     footer = None
# )

del form_descr
del form_main
del gmap_id 
del widgets
