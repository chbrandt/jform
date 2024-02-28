#!/usr/bin/env python

import os
import json

import validate


def resolve_references(obj, resolver, _id):
    # print(f"Input (obj): {obj}")
    # print(f"Input (id): {_id}")
    if isinstance(obj, list):
        out = [ resolve_references(item, resolver, _id) for item in obj ]
    elif isinstance(obj, dict):
        # _id = obj['$id'] if '$id' in obj else _id
        # print(f"Is dict (obj): {obj}")
        # print(f"Is dict (id): {_id}")
        out = {}
        for k,v in obj.items():
            if k == "$ref":
                if v.startswith('#'):
                    v = _id + v
                else:
                    _id = v.split('#')[0]
                res = resolver.resolve(v)[1]
                out.update(resolve_references(res, resolver, _id))
            else:
                out[k] = resolve_references(v, resolver, _id)
    else:
        out = obj

    return out


def main(filename):
    from copy import deepcopy

    with open(filename) as fp:
        js = json.load(fp)

    schema_id = js['$id'] if '$id' in js else os.path.basename(filename)
    resolver = validate.create_resolver(schema_id)

    res = resolve_references(js, resolver, schema_id)
    return res


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Validate file (json) content against (invenio_draft) schema", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} <filename.json>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]
    assert os.path.exists(filename)

    res = main(filename)
    print(json.dumps(res, indent=2))

    sys.exit(0)
