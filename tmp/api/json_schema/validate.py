#!/usr/bin/env python

import os
import json
import jsonschema

from pathlib import Path 

_curdir = os.path.dirname(os.path.abspath(__file__))

def read_json(filename):
    """
    Return JSON object from (JSON) filename.
    """
    fpath = Path(filename)

    try:
        with open(fpath) as f:
            js = json.load(f)
    except Exception as err:
        print(f"Error loading '{fpath}': {err}")
        return None

    return js
    

def read_schemas(basedir, pattern='*.schema.json'):
    """
    Return a dictionary with all schemas from 'basedir' matching 'pattern'
    """
    from glob import glob

    schemas = {}
    for fn in glob(os.path.join(basedir, pattern)):
        js = read_json(fn)
        if js is not None:
            # If schema has no "$id" key, add one: filename.
            #
            _fn = os.path.basename(fn)
            if "$id" not in js:
                js["$id"] = _fn # +"#"
            schemas[js["$id"]] = js

    return schemas


schema_store = read_schemas(_curdir)


def create_resolver(schema):
    from jsonschema import RefResolver

    # If we had a simple schmea we could use jsonschema's 'validate' function
    # (as we did as first):
    # > import jsonschema
    # > res = jsonschema.validate(data, schema)
    #
    # But since the schema tree got a bit more complex,
    # > https://json-schema.org/understanding-json-schema/structuring.html,
    # we now have to creack open the components a little bit.
    #
    # One of the steps taken was to create a very simple "base" schema.
    # The "base" schema has two purposes: (1) to be used as the base
    # schema for jsonschema's RefResolver object, and (2) to define the
    # version of json-schema (currently draft-07) we're using in one single place.

    # Since we have "refs" in our schemas, we need a resolver to link them
    # resolver = RefResolver.from_schema(schema_store['base.schema.json'], store=schema_store)
    resolver = RefResolver.from_schema(schema_store[schema], store=schema_store)
    return resolver


# def validate(payload, schema='invenio_draft.schema.json'):
def validate(payload, schema):
    # from jsonschema import Draft7Validator as Validator
    from jsonschema.validators import validator_for

    resolver = create_resolver(schema)

    # Get the correct (or best) validator for our schema's version
    Validator = validator_for(schema_store['base.schema.json'])

    # assert Validator.check_schema(schema), str(schema)

    # Put them all together to define the validator/schema set to use
    validator = Validator(schema_store[schema], resolver=resolver)

    res = validator.validate(payload)
    # jsonschema.validate(data, schema_store[schema])
    return res


def check_schema(schema, Validator=None):
    from jsonschema.validators import validator_for

    if not Validator:
        Validator = validator_for(schema)

    return Validator.check_schema(schema)


def test_validate():
    d = {'title': 'MapX from Ball', 'creators':[{'person_or_org': {'name': 'Acne', 'type': 'organizational'}}], 'publication_date': 2022, 'resource_type': 'dataset'}
    return validate(d)


def main(filename, schema):
    import json
    with open(filename) as fp:
        js = json.load(fp)
    res = validate(js, schema)
    print('Looks good.')
    return res


if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Validate file (json) against schema')
    
    parser.add_argument('--schema', default='invenio_draft.schema.json')
    parser.add_argument('jsonfile', type=str, help="JSON file to validate")

    args = parser.parse_args()

    filename = args.jsonfile
    schema = args.schema
    assert os.path.exists(filename)
    main(filename, schema)
    sys.exit(0)
