"""
Planmap packages parser

Example of Planmap README:
```
---
<img src="./document/PM-MAR-MS-Arsinoes.browse.png" width="800"/>

| Field                                                        | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| Map name (PM_ID)                                             | PM-MAR-MS-Arsinoes                                           |
| Map version                                                  | 03                                        |
| Target body                                                  | Mars                                                         |
| Title of map                                                 | Geological Map of Arsinoes and Pyrrhae Chaos, Mars           |
| Bounding box - Min Lat                                       | -12                                                          |
| Bounding box - Max Lat                                       | -5.8                                                         |
| Bounding box - Min Lon (0-360)                               | 329.7                                                        |
| Bounding box - Max Lon (0-360)                               | 334.5                                                        |
| Author(s)                                                    | E. Luzzi, A.P. Rossi                                         |
| Type                                                         | Preliminary                                                  |
| Output scale                                                 | 1:3.000.000                                                  |
| Original Coordinate Reference System                         | Projected Coordinate System: Equirectangular Projection: Plate_Carree false_easting: 0.00000000 false_northing: 0.00000000 central_meridian: 0.00000000 Linear Unit: Meter Geographic Coordinate System: GCS_Geographic_Coordinate_System Datum: D_MARS Prime Meridian: Reference Meridian Angular Unit: Degree |
| Data used                                                    | MOLA Elevation Model MEGDR (463 m/pixel)CTX mosaic by MurrayLabCTX DTM (18 m)HiRISE RED (0,25 m/pixel) |
| Standards adhered to                                         | Planmap mapping standards document                           |
| DOI                                                          |                                                              |
| Aims (one sentence)                                          | Morpho-stratigraphic mapping                                 |
| Short description                                            | This map shows the contacts between the disrupted bedrock of the Chaotic terrain Units and the overlying sedimentary units. In addition, it shows the distribution of the graben/fissures and pit chains that are probably related to an intense past of magmatic activity and calderic collapse. In order to better characterize the mineralogical characteristics of the occurring deposits, also spectral analyses were tried out on the only available CRISM cube in the area (still in progress) |
| Related products (cross link to other Planmap products)      |                                                              |
| Units Definition                                             | Post-collapse craters, PCC, 51-160-44Cap Unit, CAP, 182-162-255Light-toned Layered deposits units, LLD, 77-205-255High Thermal Inertia Chaotic terrain, ChH, 227-28-28Knobby Terrain, ChK, 255-127-0Fractured Plains, ChF, 255-238-3 |
| Stratigraphic info (e.g. production function used)           | N/A                                                          |
| Other comments (reviewer comments, notes on post-processing) |                                                              |
| Heritage used                                                | Glotch and Christensen 2005                                  |
| Link to other repositories                                   |                                                              |
| Acknowledgements beyond Planmap                              | N/A                                                          |
```
"""
import os
import json
import lxml
import requests

from os import path
from datetime import date
from dataclasses import dataclass, asdict
from typing import Union, List



ALLOWED_EXTS = ('pdf','jpg','jpeg','png','zip')
DOCS_MAXSIZE = 100 * 10**6 # 100 * megabytes

README_SCHEMA = 'planmap_readme.schema.json'
META_SCHEMA = 'planmap_meta.schema.json'

def validate(json:dict, schema:str):
    from .json_schema.validate import validate
    try:
        return validate(json, schema = schema)
    except:
        print(json)
        print(schema)
        raise


def dms2deg(coord:Union[str,float]):
    """
    Convert degrees-minutes-seconds to degrees
    """
    import re
    
    try:
        _ = coord + 1.2
    except:
        pass 
    else:
        return coord 

    coord = coord.replace('°','')
    north = 'N' in coord[-1].upper()
    south = 'S' in coord[-1].upper()
    east = 'E' in coord[-1].upper()
    west = 'W' in coord[-1].upper()
    
    if any([north, south, east, west]):
        coord = coord[:-1]
        
    negative = south or west
    
    vals = [ float(v) for v in re.split('[dm\'s\"]', coord) if v ]
    assert len(vals) <= 3
    d,m,s = vals if len(vals)==3 else vals + [0]*(3-len(vals))

    minutes_in_a_day = 24*60
    d += m * 360/minutes_in_a_day

    seconds_in_a_day = minutes_in_a_day * 60
    d += s * 360/seconds_in_a_day

    if negative:
        d *= -1
        
    return d


def parse_package(pathdir, docs_maxsize=DOCS_MAXSIZE):
    from glob import glob
    meta = None
    readme = None
    docs_dir = None
    for filepath in glob(f"{pathdir}/*"):
        if path.basename(filepath).lower() == 'readme.md':
            readme = filepath
        if path.basename(filepath).lower() == 'document':
            docs_dir = filepath
        if path.basename(filepath).lower() == 'meta.json':
            meta = filepath

    # assert readme or meta
    assert readme and meta

    if not meta:
        assert False
        payload = parse_readme_file(readme)
    else:
        payload = parse_metajson(meta)

    if docs_dir:
        documents = []
        for doc in glob(f"{docs_dir}/*.*"):
            if os.path.getsize(doc) > DOCS_MAXSIZE:
                print(f"File {os.path.basename(doc)} too big (> {DOCS_MAXSIZE} bytes)."
                       "I'm not including it.")
                continue
            else:
                documents.append(doc)

        payload.add_files(documents)

    return payload


def parse_readme_url(url):
    res = requests.get(url)
    readme = res.text

    _url = '/'.join(url.split('/')[:-1])
    _zip = _url.replace('/pub/','/zip/') + '.zip'

    # return _parse_readme(readme, _zip)
    return parse_readme(readme)


def parse_readme_file(filename):
    with open(filename, 'r') as fp:
        readme = fp.read()

    # _zip = os.path.dirname(filename) + '.zip'
    return parse_readme(readme)


def markdown2json(readme: Union[str,List[str]]):
    table = {}
    if isinstance(readme, str):
        readme = readme.split('\n')

    assert isinstance(readme, list)
    
    for line in readme:
        line = line.strip()
        if not line.startswith('|'):
            continue

        try:
            # split and remove whitespaces around key-value-etc strings
            #
            k, v, *x = [ o.strip() for o in line.split('|') if o ]
        except:
            continue

        if k.lower() == 'field' or k.startswith('-'):
            continue
            
        if v:
            if any([ v.lower() == na for na in ('na','nan','n/a')]):
                v = ""
            else:
                try:
                    _v = float(v)
                    v = _v
                except:
                    if "bounding box" in k.lower():
                        v = dms2deg(v)

        table.update({ k: v })

    return table 


def parse_readme(readme:str, zip_package:str=None):
    """
    Input:
    - readme: str
        '\n'-separated readme text content
    """

    table = markdown2json(readme)

    return _parse_meta_table(table, schema=README_SCHEMA)


def parse_metajson(jsonfile:str):
    with open(jsonfile, 'r') as fp:
        table = json.load(fp)

    return _parse_meta_table(table, schema=META_SCHEMA)


def _parse_meta_table(table:dict, schema:str):

    def _parse_bbox(tab):
        """
        Map's bounding-box fields to ours
        """
        _bbox = {
            'min lon': 'westlon',
            'max lon': 'eastlon',
            'min lat': 'minlat',
            'max lat': 'maxlat'
        }

        def match_bbox(field):
            for bf in _bbox:
                if bf in field.lower():
                    return bf

        bbox = {}
        for field in list(tab.keys()):
            if key := match_bbox(field):
                value = tab.pop(field)
                bbox.update({ _bbox[key] : float(value) })

        return bbox

    def _get_value(key, tab):
        for tk in list(tab.keys()):
            if key.lower() in tk.lower():
                return tab.pop(tk)
        return None

    bla = validate(table, schema)
    del bla

    _authors = _get_value('Author', table)
    assert isinstance(_authors, list)

    _meta = {
        'publisher': 'Planmap',
        'name': _get_value('Map name (PM_ID)', table),
        'body': _get_value('Target body', table),
        'title': _get_value('Title of map', table),
        # 'authors': _get_value('Author', table).split(','),
        'authors': _authors,
        'description': _get_value('Short description', table),
        'pub_date': _get_value('Publication date', table) or date.today().isoformat(),
        'identifiers': {
            'doi': _get_value('DOI', table),
        },
        'bounding_box': _parse_bbox(table),
        'files': {}
    }

    _meta.update({'extra': table})

    return InvenioPlanmap(**_meta)
    # return _meta


@dataclass
class BasePayload:
    """
    Formatter from our/astropedia metadata to invenio-rdm records
    """
    title: str
    authors: list
    pub_date: str
    publisher: str
    description: str
    bounding_box: dict
    name: str
    body: str
    extra: dict
    # Example identifiers = {'url': 'https://.../path', 'doi': '123.45/6'}
    identifiers: dict = None
    # Example files = {'browse': 'image.jpg', 'document': 'map.pdf', 'data': None}
    files: dict = None

    def asdict(self):
        return asdict(self)
    to_dict = asdict

    def add_files(self, filenames):
        def is_allowed_file(fname):
            return any([fname.endswith(ext) for ext in ALLOWED_EXTS])

        from os import path
        files = self.files if self.files else {}
        filelist = filenames if isinstance(filenames, (list,tuple)) else filenames.split(',')
        for f in filelist:
            if f and is_allowed_file(f):
                files.update({path.basename(f): f})
        self.files = files

    def read_file(self, key):
        filename = self.files[key]
        with open(filename, 'rb') as fp:
            data = fp.read()
        return data

    def create_record_payload(self):
        payload = {
            "access": {
                "record": "public",
                "files": "public"
            },
            "files": {
                "enabled": False
            },
            "metadata": {
                'title': "",
                'creators': [],
                'publisher': "",
                'description': "",
                'resource_type': "",
                'publication_date': "",
                # 'identifiers': None,
            },
        }

        return payload

    def create_files_payload(self):
        payload = []
        return payload


class InvenioPlanmap(BasePayload):
    def create_files_payload(self):
        """
        Return array of `{'key':<filename>}` objects
        (See https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records
        """
        payload = super().create_files_payload()
        # payload = [] # "entries"
        preview = None
        for labe,filename in self.files.items():
            payload.append({ 'key': os.path.basename(filename) })

        return payload

    def create_record_payload(self) -> dict:
        """
        Return json data for InvenioRDM record draft
        (See https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records
        """

        def _creators(authors:str):
            """
            Define list of creators (authors)
            """
            import re

            def is_org(name):
                HINTS = ('center','centre','corporation','technology','science')
                return any([ (word in name.lower()) for word in HINTS ])

            if not authors:
                print("Empty list of authors!")
                return None

            out = []
            for name in authors:
                if is_org(name):
                    crt = {'name': f"{name}",
                           'type': 'organizational'
                          }
                else:
                    _name = re.sub('\(.*\)', '', name)
                    _name = _name.split()
                    f_name = _name[-1]
                    g_name = ' '.join(_name[:-1])
                    crt = {'family_name': f"{f_name}",
                            'given_name': f"{g_name}",
                            'type': 'personal'
                          }

                out.append({'person_or_org': crt})

            return out

        def _description(description, **kwargs):
            description = description.strip() if description else ""
            if not description.endswith('.'):
                description += '.'

            description = "<p>"+description+"</p>"

            spatial_args = { k:kwargs.pop(k)
                             for k in list(kwargs.keys())
                             if k in ['bounding_box', 'body']}

            if spatial_args:
                sup_info = "\n<b>Spatial information:</b>\n"
                sup_info += "<ul>"
                for k,v in spatial_args.items():

                    if k == 'body':
                        _sub = ("<li>"
                                 f"Target body: {v}"
                                 "</li>")

                    elif k == 'bounding_box':
                        _sub = ("<li>"
                                "Bounding-Box: "
                                 f"{', '.join(str(k_)+' = '+str(v_) for k_,v_ in v.items())}"
                                 "</li>")

                    # sup_info += f"<li>{_sub}</li>"
                    sup_info += _sub

                sup_info += "</ul>"
                description += sup_info

            if kwargs:
                kwargs = kwargs['extra']
                sup_info = f"\n<b>Ancillary information:</b>\n"
                sup_info += "<ul>"
                for k,v in kwargs.items():
                    if v is None:
                        continue
                    try:
                        if isinstance(v, str) and len(vals := v.split('\n')) > 1:
                            _sub = f"{str(k)}:<ul><li>"
                            _sub += "</li><li>".join(str(_) for _ in vals)
                            _sub += "</li></ul>"
                        else:
                            _sub = f"<li>{str(k)}: {str(v)}</li>"
                        sup_info += _sub
                    except Exception as err:
                        print("Error:", err)
                        print(k,v)
                        pass

                sup_info += "</ul>"
                description += sup_info

            return description

        def _identifiers(ids):
            out = []
            for k,v in ids.items():
                if v:
                    out.append({ 'scheme': k, 'identifier': v})
            return out

        def _files(files_dict):
            # Use order in ALLOWED_EXTS
            files = list(files_dict.keys())
            files.sort(key=lambda f:ALLOWED_EXTS.index(f.split('.')[-1].lower()))
            default = [f for f in files if f.lower().endswith('pdf')]
            default = default[0] if default else None
            d = {
                'enabled': bool(len(files)),
                'default_preview': default,
                'order': files
            }
            (d)
            return d


        # payload = self._RECORD_TEMPLATE.copy()
        payload = super().create_record_payload()

        title = self.title
        publisher = self.publisher
        publication_date = self.pub_date
        resource_type = {'id': 'dataset'}

        creators = _creators(self.authors)
        if not creators:
            print("Empty list of authors!")
            return None

        description = _description(
                description=self.description,
                bounding_box=self.bounding_box,
                body=self.body,
            extra=self.extra
        )

        files = _files(self.files)
        identifiers = _identifiers(self.identifiers)

        payload.update({
            'metadata': {
                'creators': creators,
                'publisher': publisher,
                'publication_date': publication_date,
                'resource_type': resource_type,
                'title': title,
                'description': description,
                'identifiers': identifiers
            },
            'files': files
        })

        return payload
