"""
Astropedia pages (html/xml) parsers

In Astropedia products html pages, the data we want is in DOM's
`<html><body><div...<section class="block data">`.
There, the (metadata) sections are defined by `<h2>` elements, and the elements
`<p>` (paragraph) and `<dl>` (description lists) in between are their content.

This module's variable '_EXAMPLE_ASTROPEDIA_HTML' contains an example of
as Astropedia product html (Cleaned from element/blocks without
useful information to us).
"""
import json
import lxml
import requests

from os import path
from dataclasses import dataclass, asdict



def parse_astropedia_html(url:str) -> dict:
    """
    Parse Astropedia html pages.

    Ex: https://astrogeology.usgs.gov/search/map/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS_v2
    """
    # Auxiliary function (TODO: move from here)
    def _parse_description(nodes):
        text = []
        for node in nodes:
            text.append(node.text_content())
            # if node.text:
            #     text.append(node.text.strip())
        return '\n\n'.join(text)

    def _parse_authors(nodes):
        """
        Clean/Split the authors from 'text'.

        The text/names are in a linear comma-separated list ("and" possibly):
        "Fulano de Tal, Maria Brasil (, and) Carlos H. Brandt".
        The output is a list of "lastname, firstname" strings
        """
        line = nodes[0].text.strip()

        # if ',' not in line:
        #     authors = [ line ]
        # else:
        #     authors = [ author.strip()
        #                 for author in line.replace(' and ',',').split(',') ]
        #     authors = [ author.split()[-1] + ', ' + ' '.join(author.split()[:-1])
        #                 for author in authors
        #                 if author ]
        authors = [ author.strip()
                    for author in line.replace(' and ',',').split(',') ]

        return authors

    def _parse_href(nodes):
        return nodes[0].attrib['href']

    def _parse_bbox(nodes):
        """Map astropedia's bounding-box fields to ours"""
        _bbox = {
            'Minimum Longitude': 'westlon',
            'Maximum Longitude': 'eastlon',
            'Minimum Latitude': 'minlat',
            'Maximum Latitude': 'maxlat'
        }
        out = {}
        for node in nodes:
            if node.text in _bbox:
                out.update({ _bbox[node.text]: float(node.getnext().text) })

        return out

    def _parse_date(nodes):
        from datetime import datetime
        return datetime.strptime(nodes[0].text, "%d %B %Y").date().isoformat()

    # Metadata mappings (ours x astropedia)
    #
    _maps = dict(
        meta = dict(
            title = {'path': 'h2[1]' },

            # abstract
            description = {'path': 'p', 'proc': _parse_description },

            # pub_data
            date_pub = {'path': 'dl[1]/dt[.="Publication Date"]/following-sibling::dd[1]',
                        'proc': _parse_date},

            # authors
            authors = {'path': 'dl[1]/dt[.="Author"]/following-sibling::dd[1]',
                        'proc': _parse_authors },

            # publisher
            origin = {'path': 'dl[1]/dt[.="Publisher"]/following-sibling::dd[1]'},

            # url_document
            document_url = {'path': '//dt[.="Supplemental Information"]/following-sibling::dd[1]/a'},

            # purpose
            # purpose = {'path': '//dt[text()="Purpose"]/following-sibling::dd[1]/p'},

            # bounding_box
            bounding_box = {'path': 'h2[text()="Geospatial Information"]//following-sibling::dl[1]/dt',
                            'proc': _parse_bbox },
        ),
        header = dict(
            browse = {'path': '//div[@class="downloads"]//a[.="Sample"]', 'proc': _parse_href},

            # url_data
            product_url = {'path': '//div[@class="downloads"]//a[.="Data" or text()="Original"]' , 'proc': _parse_href},
        )
    )

    def map_data(tree, mappings:dict):
        """
        Return object like 'mappings', with values from (astropedia) 'tree'
        """
        def _map(tree, mapping):
            """
            Return value of key at the leaf of "obj['path']",
            (optional) processed by "obj['proc']()" (if available)
            """
            nodes = tree.xpath(mapping['path'])

            _default = lambda nodes: nodes[0].text

            out = mapping.get('proc', _default)(nodes)

            return out

        out = {}
        for keyword, mapping in mappings.items():
            value = _map(tree, mapping)
            out.update({ keyword: value })

        return out


    import requests
    res = requests.get(url)
    res.raise_for_status()

    import lxml.html

    tree = lxml.html.fromstring(res.content,
      parser=lxml.html.HTMLParser(remove_comments=True))

    # Select (html/xml) node to start, the data we need is in "block metadata":
    #     <body><div...<section class="block metadata">(.)
    #
    tmeta = tree.xpath('//div[@class="content"]/section[@class="block metadata"]')[0]
    theader = tree.xpath('//div[@class="downloads"]//a[.="Sample"]')[0]

    out_js = {}
    out_js.update(map_data(tmeta, _maps['meta']))
    out_js.update(map_data(theader, _maps['header']))
    out_js.update({'url': url})

    return InvenioAstropedia(**out_js)


# def parse_astropedia_xml(url:str) -> dict:
#     """
#     Parse Astropedias product/map xml from 'url'
#
#     Example url:
#     https://astrogeology.usgs.gov/search/map/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS_v2.xml
#     """
#     import xmltodict
#
#     xml_file = path.basename(url)
#     rootname = '.'.join(xml_file.split('.')[:-1])
#
#     # Get the XML from 'url'
#     #
#     res = requests.get(url)
#     res.raise_for_status()
#
#     # Save it, for convenience, in local directory
#     #
#     result = res.text
#     with open(xml_file, 'w') as fp:
#         fp.write(result)
#
#     # Transform to JSON (simpler to handle)
#     #
#     js = xmltodict.parse(res.text)
#
#     # Define structure to map between "theirs" (astropedia), and "ours" (invenio).
#     # Let's define it as a dictionary of fields we want to fill from input object,
#     # the input is the JSON object from Astropedia's XML.
#     # Auxiliary, some individual functions to process the data values during mapping.
#     #
#     _clean_CDATA = lambda s: s.replace('![[CDATA]', '').replace(']]','')
#     """Remove "![[CDATA].*]]' from string"""
#
#     def _parse_bbox(bbox):
#         """Map astropedia's bounding-box fields to ours"""
#         _bbox = {
#             'westlon': 'westbc',
#             'eastlon': 'eastbc',
#             'minlat': 'southbc',
#             'maxlat': 'northbc'
#         }
#         return { k:float(bbox[v]) for k,v in _bbox.items() }
#
#     _split_sep = lambda s,sep=',': [w.strip() for w in s.split(sep)]
#     """Return a list of comma-separated terms (Ex: 'ABC, XYZ')"""
#
#     def _parse_authors(text):
#         """
#         Clean/Split the authors from 'text'.
#         (Ex: ...\n<b>References:</b>\n\nLastname, N.I., Lastname, N.I. and Lastname, N.I. (2020)...
#         """
#         refs = []
#         flag = False
#         for line in text.split('\n'):
#             line = line.strip()
#             if line == '':
#                 continue
#             if 'References:' in line:
#                 flag = True
#                 continue
#             if flag:
#                 refs.append(line)
#
#         authors = []
#         for line in refs:
#             l_authors = line.split('(')[0]
#             _authors = [ a2 for a1 in _split_sep(l_authors, ' and ')
#                             for a2 in _split_sep(a1, ',') ]
#             _authors = [ f"{_authors[i-1]}, {_authors[i]}"
#                             for i in range(1,len(_authors),2) ]
#             authors.extend(_authors)
#
#         return authors
#
#
#     def _publication_date(date_string:str):
#         from dateutil.parser import isoparse
#         return isoparse(date_string).date().isoformat()
#
#     # metadata mappings (ours: astropedia)
#     #
#     _meta = dict(
#         title = {'path': 'metadata/idinfo/citation/citeinfo/title' },
#
#         date_pub = {'path': 'metadata/idinfo/citation/citeinfo/pubdate',
#                     'proc': _publication_date},
#
#         origin = {'path': 'metadata/idinfo/citation/citeinfo/origin'},
#
#         description = {'path': 'metadata/idinfo/descript/abstract',
#                        'proc': _clean_CDATA },
#
#         authors = {'path': 'metadata/idinfo/descript/abstract',
#                    'proc': _parse_authors },
#
#         document_url = {'path': 'metadata/idinfo/descript/supplinf',
#                         'proc': _clean_CDATA },
#
#         status = {'path': 'metadata/idinfo/status/progress' },
#
#         bounding_box = {'path': 'metadata/idinfo/spdom/bounding',
#                         'proc': _parse_bbox },
#
#         scope = {'path': 'metadata/idinfo/accscope',
#                  'proc': _split_sep },
#
#         browse = {'path': 'metadata/idinfo/browse/browsen'},
#
#         product_url = {'path': 'metadata/distinfo/stdorder/digform/digtopt/onlinopt/computer/networka/networkr' }
#     )
#
#
#     # Function to do the whole thing
#     #
#     def map_jsons(js:dict, mappings:dict):
#         """
#         Return object like 'mappings', with values from (astropedia) 'js'
#
#         Ex:
#         > js = {'key1': {'key2': "val"}}
#         > mappings = {
#         >     'my_key1' : dict(path='key1/key2', proc=lambda s:s.upper()),
#         >     'my_key2' : dict(path='key1/key2')
#         > }
#         > map_jsons(js, mappings)
#         # {'my_key1': 'VAL', 'my_key2': 'val'}
#         """
#         def _map(js, obj):
#             """
#             Return value of key at the leaf of "obj['path']",
#             (optional) processed by "obj['proc']()" (if available)
#             """
#             val = js
#             for node in obj['path'].split('/'):
#                 val = val[node]
#
#             out = val
#             if 'proc' in obj:
#                 out = obj['proc'](val)
#
#             return out
#
#         out = {}
#         for keyword, mapping in mappings.items():
#             value = _map(js, mapping)
#             out.update({ keyword: value })
#
#         return out
#
#     our_js = map_jsons(js, _meta)
#     # our_js
#
#     with open(f'{rootname}.json', 'w') as fp:
#         json.dump(js, fp, indent=2)
#
#     with open(f'{rootname}_OurMeta.json', 'w') as fp:
#         json.dump(our_js, fp, indent=2)
#
#     return InvenioAstropedia(**our_js)



@dataclass
class InvenioAstropedia:
    """
    Formatter from our/astropedia metadata to invenio-rdm records
    """
    title: str
    date_pub: str
    origin: str
    url: str
    description: str
    authors: str
    document_url: str
    # status: str
    bounding_box: dict
    # scope: str
    browse: str
    product_url: str

    _RECORD_TEMPLATE = {
      "access": {
        "record": "public",
        "files": "public"
      },
      "files": {
        "enabled": True
      },
      "metadata": {
      }
    }

    def __post_init__(self):
        from os import path
        files = {}
        for f in [self.document_url, self.browse]:
            if f and any([f.endswith(ext) for ext in ('pdf','jpg','png','jpeg')]):
                files.update({path.basename(f): f})
        self._files = files

    def asdict(self):
        return asdict(self)

    to_dict = asdict

    def read_file(self, key):
        url = self._files.get(key)
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except Exception as err:
            print(f"Request for '{url}' failed, code: {resp.status_code}")
            return None

        return resp.content

    def create_files_payload(self):
        """
        Return array of `{'key':<filename>}` objects
        (See https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records
        """
        payload = [] # "entries"
        preview = None
        for key in self._files.keys():
            payload.append({ 'key': key })

        return payload

    def create_record_payload(self) -> dict:
        """
        Return json data for InvenioRDM record draft
        (See https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records
        """

        def _creators(authors:list, person_or_org:list=None):
            """
            Define list of creators (authors)
            """
            import re

            def is_org(name):
                HINTS = ('center','centre','corporation','technology','science')
                return any([ (word in name.lower()) for word in HINTS ])

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
            description = description.replace('References:', '<b>References:</b>')
            if kwargs:
                sup_info = "\n<b>Extra:</b>\n"
                sup_info += "<ul>"
                for k,v in kwargs.items():
                    if k == 'bounding_box':
                        _sub = "Bounding-Box:"
                        _sub += "<ul>"
                        _sub += ("<li>"
                                 f"{', '.join(str(k_)+' = '+str(v_) for k_,v_ in v.items())}"
                                 "</li>")
                        _sub += "</ul>"
                    else:
                        _sub = f"{k.title().replace('_',' ')}:"
                        _sub += "<ul>"
                        if isinstance(v, str) and v.startswith('http'):
                            _sub += f"<li><a href='{str(v)}'>{str(v)}</a></li>"
                        else:
                            _sub += f"<li>{str(v)}</li>"
                        _sub += "</ul>"
                    sup_info += f"<li>{_sub}</li>"
                sup_info += "</ul>"
                description += sup_info

            description = (description.replace('<b><b>', '<b>')
                                      .replace('</b></b>', '</b>')
                                      .replace('<b>', '<p/><b>')
                                      .replace('\n\n', '<br>')
                                      .replace('\n',''))
            return description

        def _identifiers(url):
            return [{
                'identifier': url,
                'scheme': 'url'
            }]

        payload = self._RECORD_TEMPLATE.copy()
        creators = _creators(self.authors)
        publisher = self.origin
        publication_date = self.date_pub
        resource_type = {'id': 'dataset'}
        title = self.title
        description = _description(
            description=self.description,
            bounding_box=self.bounding_box,
            product_page=self.url
        )
        files = {'enabled': bool(len(self._files))}
        identifiers = _identifiers(url=self.url)

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

_EXAMPLE_ASTROPEDIA_HTML = """
```
<body id="splashy">
  <div class="wrapper">
    <div class="container">
      <div id="wide-image" class="wide-image-wrapper ">
        <div class="downloads">
          <img class="thumb" src="/cache/images/f25336da566e9006b7737a289037c5c5_Ganymede_Geology_100.jpg" />
          <h3>Download</h3>
          <ul>
            <li><a target="_blank" href="https://astropedia.astrogeology.usgs.gov/download/Ganymede/Geology/thumbs/Ganymede_Geology_11520.jpg">Maximum Size</a> (jpg) </li>
            <li><a target="_blank" href="https://astropedia.astrogeology.usgs.gov/download/Ganymede/Geology/thumbs/Ganymede_Geology_1024.jpg">Sample</a> (jpg) 1024px wide</li>
            <li><a target="_blank" href="https://pubs.usgs.gov/sim/3237">Data</a> (zip) 102 MB</li>
          </ul>
        </div>
      </div>
      <div class="content">
        <section class="block metadata">
          <h2 class="title">Global Geologic Map of Ganymede, SIM3237</h2>
          <p> Ganymede is the largest satellite of Jupiter, and its icy surface has been formed through a variety of of impact cratering, tectonic, and possibly cryovolcanic processes. The history of Ganymede can be divided into three distinct
            phases: an early phase dominated by impact cratering and mixing of non-ice materials in the icy crust, a phase in the middle of its history marked by great tectonic upheaval, and a late quiescent phase characterized by a gradual drop in
            heat flow and further impact cratering. Images of Ganymede suitable for geologic mapping were collected during the flybys of Voyager 1 and Voyager 2 (1979), as well as during the Galileo mission in orbit around Jupiter (1995-2003). This
            map represents a synthesis of our understanding of Ganymede geology after the conclusion of the Galileo mission.</p>
          <p> The two fundamental classes of material units on Ganymede are dark materials and light materials. The dark/light distinction is based on sharp relative albedo contrasts at terrain boundaries, rather than on absolute albedo, as several
            other types of surface modification (e.g., crater rays, polar caps) change the absolute albedo within these terrain classes. Dark materials cover 35% of Ganymede's surface, with almost the entire remainder of the surface covered by light
            materials.</p>
          <p> Dark materials are heavily cratered, though not as heavily cratered as the surface of the neighboring satellite Callisto, suggesting that dark materials cannot be a primordial surface. At high resolution, dark materials are dominated by
            the downslope movement of loose dark regolith within impact craters and on the sides of bright ridges and hummocks. These observations suggest that dark materials are covered by a thin lag deposit of dark regolith derived by sublimation
            of a more ice-rich crust below. Dark materials commonly exhibit sets of concentric arcuate structures known as furrows. Furrows may be the remnants of ancient multi-ring impact basins, similar to intact impact basins on Callisto such as
            Valhalla and Asgard.</p>
          <p> Light materials crosscut dark materials and exhibit a lower impact crater density, demonstrating that they were formed later. Light materials are subdivided into an intricate patchwork of crosscutting lineaments called grooves, mixed
            with areas of relatively smooth terrain. At high resolution, most light materials are dominated by extensional faulting. Even light materials that appear to be smooth at low resolution are marked at high resolution by sets of parallel
            lineaments of apparent tectonic origin. There is an open question on the extent to which light terrain is formed by cryovolcanic flooding of dark material with brighter ice, versus tectonic destruction of preexisting surface features and
            exposure of brighter subsurface ice in fault scarps; it is certainly possible that both of these processes play important roles in the formation of light materials. Not all tectonic activity on Ganymede has led to the formation of light
            material and some dark material is cut by extensional faults without exhibiting a major change in albedo, while reticulate material is cut by two sets of tectonic lineaments and is transitional in albedo between adjacent light and dark
            materials.</p>
          <p> The other material units found on Ganymede were created by several types of impact features, ranging from impact craters, to viscously relaxed impact features called palimpsests, to the large impact basin Gilgamesh in the southern
            hemisphere. Additional details on these topics, along with detailed descriptions of the type localities for the material units, may be found in the companion paper to this map (Patterson and others, 2010).</p>
          <p>Suggested Citation:
            Collins, G.C., Patterson, G.W., Head, J.W., Pappalardo, R.T., Prockter, L.M., Lucchitta, B.K., and Kay, J.P., 2013, Global geologic map of Ganymede: U.S. Geological Survey Scientific Investigations Map 3237, pamphlet 4 p., 1 sheet, scale
            1:15,000,000, http://dx.doi.org/10.3133/sim3237</p>
          <p>References:
            Patterson, G.W., Collins, G.C., Head, J.W., and 4 others, 2010, Global geological mapping of Ganymede: Icarus, v. 207, p. 845-867.</p>
          <p> Shoemaker, E.M., Lucchitta, B.K., Wilhelms, D.E., and 2 others, 1982, The geology of Ganymede, in: Satellites of Jupiter (Morrison, D., ed.), Univ. of Arizona Press, p. 435-520.</p>
          <p> Pappalardo, R.T., Collins, G.C., Head, J.W., and 6 others, 2004, Geology of Ganymede, in: Jupiter (Bagenal, F., Dowling, T., McKinnon, W., eds.), Cambridge Univ. Press, p. 363-396.</p>
          <dl>
            <dt>Mimetype</dt>
            <dd>application/zip</dd>
            <dt>Filename</dt>
            <dd><a href="https://astropedia.astrogeology.usgs.gov/download/Ganymede/Geology/Ganymede_SIM3237_Database.zip">Ganymede_SIM3237_Database.zip</a></dd>
            <dt>Publisher</dt>
            <dd>USGS Astrogeology Science Center</dd>
            <dt>Publication Date</dt>
            <dd>11 February 2014</dd>
            <dt>Author</dt>
            <dd>Geoffrey C. Collins, G. Wesley Patterson, James W. Head, Robert T. Pappalardo, Louise M. Prockter, Baerbel K. Lucchitta, Jonathan P. Kay</dd>
            <dt>Originator</dt>
            <dd></dd>
            <dt>Group</dt>
            <dd>PGM, MRCTR</dd>
            <dt>Added to Astropedia</dt>
            <dd>14 February 2014</dd>
            <dt>Modified</dt>
            <dd>5 June 2019</dd>
          </dl>

          <h2>General</h2>
          <dl>
            <dt>Purpose</dt>
            <dd>
              <p>Much has been learned about Ganymede's impact cratering, tectonic, and possibly cryovolcanic processes since the Voyager flybys, primarily during and following the Galileo Mission at Jupiter (December 1995-September 2003). Our
                mapping incorporates this new understanding to assist in map unit definition and provide a global synthesis of Ganymede's geology.</p>
            </dd>
            <dt>Geospatial Data Presentation Form</dt>
            <dd><a href="/search/results?k1=geospatial_data_presentation_form&v1=Geologic+Map">Geologic Map</a>, <a href="/search/results?k1=geospatial_data_presentation_form&v1=Global+Mosaic">Global Mosaic</a></dd><dt>Series Id</dt>
            <dd>3237</dd>
            <dt>Edition</dt>
            <dd>1</dd>
            <dt>Online Linkage</dt>
            <dd><a target="_blank" href="https://pubs.usgs.gov/sim/3237">https://pubs.usgs.gov/sim/3237</a></dd><dt>Native Data Set Environment</dt>
            <dd><a href="http://www.esri.com/software/arcgis/arcgis-for-desktop">ESRI Arcinfo</a></dd><dt>Color</dt>
            <dd>Color</dd>
            <dt>Supplemental Information</dt>
            <dd><a target="_blank" href="http://pubs.usgs.gov/sim/3237/">http://pubs.usgs.gov/sim/3237/</a></dd>
          </dl>

          <h2>Keywords</h2>
          <dl>
            <dt>System</dt>
            <dd><a href="/search?pmi-target=jupiter">Jupiter</a></dd>
            <dt>Target</dt>
            <dd><a href="/search?pmi-target=ganymede">Ganymede</a></dd>
            <dt>Theme</dt>
            <dd><a href="/search/results?k1=theme&v1=Geology">Geology</a>, <a href="/search/results?k1=theme&v1=Geographic+Information+System+(GIS)">Geographic Information System (GIS)</a>, <a href="/search/results?k1=theme&v1=Flyby+missions">Flyby
                missions</a>, <a href="/search/results?k1=theme&v1=Photogeology">Photogeology</a>, <a href="/search/results?k1=theme&v1=Geomorphology">Geomorphology</a>, <a href="/search/results?k1=theme&v1=Structure">Structure</a>, <a
                href="/search/results?k1=theme&v1=Satellites">Satellites</a>, <a href="/search/results?k1=theme&v1=Remote+Sensing">Remote Sensing</a></dd><dt>Mission</dt>
            <dd><a href="/search/results?k1=mission&v1=Voyager">Voyager</a>, <a href="/search/results?k1=mission&v1=Galileo">Galileo</a>
            </dd><dt>Mission Specific</dt>
            <dd>Voyager 1, Voyager 2</dd>
          </dl>

          <h2>Contact and Distribution</h2>
          <dl>
            <dt>Access Constraints</dt>
            <dd>None</dd><dt>Access Instructions</dt>
            <dd>GIS software will be required to use most files in the download. The official USGS SIM map contains report: i, 4 p.; 1 Plate: 58.02 x 41.00 inches; ReadMe; Metadata; Database.</dd><dt>Use Constraints</dt>
            <dd>Please cite authors</dd>
          </dl>

          <h2>Data Status and Quality</h2>
          <dl>
            <dt>Time Period of Content Begin</dt>
            <dd>1 June 2006</dd><dt>Time Period of Content End</dt>
            <dd>11 February 2014</dd><dt>Currentness Reference</dt>
            <dd>Publication date</dd><dt>Progress</dt>
            <dd>Complete</dd><dt>Update Frequency</dt>
            <dd>None planned</dd><dt>Logical Consistency Report</dt>
            <dd>These data are believed to be logically consistent. Line geometry is topologically clean. The final map was generalized and scaled to be commensurate with a 1:15, 000, 000 map scale, although map component compilation was at a larger
              scale. Overall, the geologic map product is only as accurate as the 2005 basemap created by the USGS which contains kilometer errors.

              * Becker, T. et al., 2001. Final Digital Global Maps of Ganymede, Europa, and Callisto, In Lunar and Planetary Science XXXII, Abstract #2009, Lunar and Planetary Institute, Houston.</dd><dt>Completeness Report</dt>
            <dd>
              <p>Completed at the given scale for publication by USGS.</p>
            </dd><dt>Process Description</dt>
            <dd>
              <p>Relative age relationships of mapped units were determined based on crosscutting relationships and differences in crater density. Dark cratered material (dc) is crosscut by grooves to form dark lineated material (dl). Dark materials
                and reticulate material are crosscut by light materials. Light materials are divided into three broad age categories based on crosscutting relationships. The youngest (lg3, ls3, li3) light material units are not crosscut by any other
                light units, while the oldest (lg1, ls1, li1) are crosscut by all adjacent light units. Intermediate age light material units (lg2, ls2, li2) are crosscut by the youngest units, and intermediate units in turn crosscut the oldest
                units. Dark lineated (dl) and reticulate (r) material sometimes share common groove spacing, morphology, and orientation with adjacent old light materials (lg1, ls1, li1), indicating that they may have formed contemporaneously.
                Palimpsests are divided into ancient palimpsests (p1), which are crosscut by light material, young palimpsests (p2), which overlie light material, and undivided palimpsests (pu), which do not come in contact with light material and
                thus crosscutting relationships cannot be used for relative age determination. The p2 palimpsests Epigeous and Zakar overlie all ages of light materials, Teshub overlies undivided light materials (l) and is cut by young light grooved
                material (lg3), and Hathor overlies undivided light material (l) while its secondary craters overlie old light subdued material (ls1) and intermediate light grooved material (lg2). All basin materials (br, bs, bi) overlie all ages of
                light materials. Some degraded crater materials (c1) are crosscut by dark lineated (dl) and light materials, while other degraded crater materials overlie light materials. Partially degraded and fresh crater materials (c2 and c3)
                overlie all other material units.</p>
            </dd><dt>Horizontal Positional Accuracy Value</dt>
            <dd>2000</dd><dt>Horizontal Positional Accuracy Report</dt>
            <dd>Best Effort</dd><dt>Entity and Attribute Overview</dt>
            <dd>Geologic and structural features</dd><dt>Entity and Attribute Detailed Description</dt>
            <dd>Please see USGS publication SIM3227 pamphlet.</dd><dt>Entity and Attribute Linkage</dt>
            <dd>http://pubs.usgs.gov/sim/3237/</dd>
          </dl>

          <h2>Lineage</h2>
          <dl>
            <dt>Source Originator</dt>
            <dd>Astrogeology Science Center</dt><dt>Source Publication Date</dt>
            <dd>1 March 2003</dd><dt>Source Title</dt>
            <dd>Controlled color photomosaic map of Ganymede Jg 15M CMNK</dd><dt>Source Online Linkage</dt>
            <dd><a target="_blank" href="http://pubs.er.usgs.gov/publication/i2762">http://pubs.er.usgs.gov/publication/i2762</a></dd><dt>Type of Source Media</dt>
            <dd>Online</dd><dt>Attribute Accuracy Report</dt>
            <dd>Best Effort</dd>
          </dl>

          <h2>Geospatial Information</h2>
          <dl>
            <dt>Location Description</dt>
            <dd>Global</dd>
            <dt>Minimum Latitude</dt>
            <dd>-90</dd>
            <dt>Maximum Latitude</dt>
            <dd>90</dd>
            <dt>Minimum Longitude</dt>
            <dd>0</dd>
            <dt>Maximum Longitude</dt>
            <dd>360</dd>
            <dt>Direct Spatial Reference Method</dt>
            <dd>Vector</dd>
            <dt>Object Type</dt>
            <dd>Polygon</dd>
            <dt>Quad Name</dt>
            <dd></dd>
            <dt>Radius A</dt>
            <dd>2632345</dd><dt>Radius C</dt>
            <dd>2632345</dd><dt>Control Net</dt>
            <dd>RAND November 1999 control solution</dd><dt>Horizontal Coordinate System Units</dt>
            <dd>Degrees</dd><dt>Map Projection Name</dt>
            <dd>Simple Cylindrical</dd><dt>Latitude Type</dt>
            <dd>Planetocentric</dd><dt>Longitude Direction</dt>
            <dd>Positive East</dd><dt>Longitude Domain</dt>
            <dd>0 to 360</dd>
          </dl>
        </section>
      </div>
      <div class="sidebar">
        <div class="block">
          <h3 class="title">Ancillary Data</h3>
          <ul class="listing">
            <li><a target="_blank" href="https://astropedia.astrogeology.usgs.gov/download/Ganymede/Geology/ancillary/sim3237_pamphlet.pdf">Pamphlet, USGS Scientific Investigations Map 3237</a><span> (pdf) 236 kB</span></li>
            <li><a target="_blank" href="https://astropedia.astrogeology.usgs.gov/download/Ganymede/Geology/ancillary/sim3237_mapsheet.pdf">Map sheet, USGS Scientific Investigations Map 3237</a><span> (pdf) 21 MB</span></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</body>
```
"""
