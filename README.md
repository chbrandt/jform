# JForm

JSON-schema to widgets (gui) manager.

You give a schema like this one:
```json
{
  "type": "string"
}
```
and get a prompt like this one:
![string-schema widget](assets/string_schema_widget.jpg)

You use like this:
```python
from jform import JForm

form = JForm(schema=schema)

display(form)
# an ipywidget displays a string field ("string"), type 'something'

print(form)
# 'something'

print(form.value)
# 'something'
```

Or:
```python
schema = dict(
  type = 'object',
  properties = {
    'Field': { 'type': 'string' }
  }
)

form = JForm(schema=schema)

print(form)
# { 'Field': '' }

display(form)
# an ipywidget displays a string field "Field", type 'something'

print(form)
# { 'Field': 'something' }
```

Or:
```python
schema = dict(
  type = 'array',
  items = { 'type': 'string' }
)

form = JForm(schema=schema)

print(form)
# []

display(form)
# an ipywidget displays a button to add (+) a string field, 
# add one with 'something' and another one with 'else'

print(form)
# ['something','else']
```

/.\



