"""
Toolset to read/parse Astropedia product-page and to publish on InvenioRDM.

"""
import json
import requests

from typing import List
from dataclasses import dataclass, asdict



class InvenioRecords:
    """
    Handle results from GET records
    """
    def __init__(self, records_json):
        self._js = records_json
        self._hits = self._js['hits']['hits']

    def __len__(self):
        return int(self._js['hits']['total'])
    count = __len__

    def __str__(self):
        return json.dumps(self._js, indent=2)

    @property
    def records(self):
        return self._hits

    @property
    def links(self):
        return self._js['links']

    @property
    def aggregations(self):
        return self._js['aggregations']


class InvenioClient:
    """
    Client for Invenio(RDM) API
    """
    _scheme = 'https'
    _hostname = 'localhost' #'127.0.0.1:5000'
    _path_api = '/api'
    _token = None

    def __init__(self, hostname:str, token:str=None):
        self._hostname = hostname
        self._token = token

    def read_records(self) -> InvenioRecords:
        """
        Read all records from server, return InvenioResults object
        """
        path_ext = '/records'
        res = self._get(path_ext)
        js = res.json()
        return InvenioRecords(js)

    def create_draft(self, payload) -> dict:
        """
        Create draft (see publish_draft() for publishing it)
        """
        # Create draft
        path_ext = '/records'
        data_record = payload.create_record_payload()

        resp = self._post(path_ext, json.dumps(data_record))

        try:
            resp.raise_for_status()
        except Exception as err:
            print(repr(err))
            return None

        resp_js = resp.json()

        # Upload files
        draft_id = resp_js['id']

        # 1) initialize file key(s)
        #
        path_ext = f'/records/{draft_id}/draft/files'
        data_files = payload.create_files_payload()

        if data_files:
            resp_files = self._post(path_ext, json.dumps(data_files))
            # print("Declare files:", resp_files.json())

            # 2) push files data
            #
            for obj in data_files:
                key = obj['key']
                # push data
                path_ext = f"/records/{draft_id}/draft/files/{key}/content"
                data = payload.read_file(key)
                resp_file = self._put(path_ext, data)
                # print(f"Pushed file {key}", resp_file.json())
                # commit
                path_ext = f"/records/{draft_id}/draft/files/{key}/commit"
                resp_commit = self._post(path_ext, None)
                # print(f"Commit file {key}", resp_commit.json())
                data = None

        # End) let's read what's in there now
        path_ext = f"/records/{draft_id}/draft"
        res = self._get(path_ext)
        return res.json()

    # def add_files(self, draft_id:str, files:List[str]=None):
    #     """
    #     Upload files to draft 'id'
    #     """
    #     NotImplementedError

    def publish_draft(self, draft_id):
        """
        Publish a previously created draft (see create_record())
        """
        path_ext = f"/records/{draft_id}/draft/actions/publish"
        res = self._post(path_ext)
        js = res.json()
        return js

    def delete_draft(self, draft_id):
        """
        Delete draft
        """
        path_ext = f"/records/{draft_id}/draft"
        res = self._delete(path_ext)
        js = res.json()
        return js

    def _url(self, path_ext=''):
        path = self._path_api + path_ext
        return f"{self._scheme}://{self._hostname}{path}"

    def _headers(self, content_type:str='application/json'):
        hdr = {'Content-Type': content_type}
        if self._token:
            hdr.update({'Authorization': f"Bearer {self._token}"})

        return hdr

    def _get(self, path_ext, params=None):
        base_url = self._url(path_ext)
        return requests.get(base_url, params=params,
                            headers=self._headers(), verify=False)

    def _post(self, path_ext, payload=None):
        base_url = self._url(path_ext)
        return requests.post(base_url, data=payload,
                             headers=self._headers(), verify=False)

    def _put(self, path_ext, payload=None):
        content_type:str='application/octet-stream'
        base_url = self._url(path_ext)
        return requests.put(base_url, data=payload,
                            headers=self._headers(content_type), verify=False)

    def _delete(self, path_ext):
        base_url = self._url(path_ext)
        return requests.delete(base_url)
