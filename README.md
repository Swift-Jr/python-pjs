[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/) [![Generic badge](https://img.shields.io/badge/status-ALPHA-<COLOR>.svg)](https://shields.io/) [![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/Swift-Jr/python-pjs/blob/master/LICENSE)

# python-pjs
A Python library for managing pSQL database schema using JSON Schema, known as pj's __p__ython __j__son __s__chema.

This library is design to be used with tools like Apache Airflow, to automate the management of managed database schema.

## Why build pjs?
Manually managing database schema can be problematic, especially when multiple teams are working within the same data warehouse environment.
* You become reliant on ensuring everyone uses the same process for migration
* You need a (usually) paid tool to compare your develop and target schema
* Migrations have to be created in order, otherwise they fail
* Reviewing migration PR's can be complex to spot the actual change

pjs solves this by:
* Giving you a clear and declarative representation of a database schema
* Simple tooling for automating the migrations at runtime instead of setup
* Easily setup with any existing pgSQL database

This project takes inspiration from [table-schema by frictionlessdata](https://specs.frictionlessdata.io/table-schema/#descriptor) - a json schema representation for tabular data, but didn't extend that to support pgSQL.

## How?
python-pjs gives you a clear and declarative way of describing a pgSQL table, and a set of tooling that allows you to compare and migrate the JSON schema to a database schema.

Begin by describing your schema with JSON, for example:
```json
{
    "sample_table": {
        "schema": {
            "field": {
                "type": "bigint",
                "nullable": false,
                "max_length": 100,
                "default_value": "now()"
            }
        },
        "primary_key": {
            "fields": ["id"],
            "constraint": "pkey"
        },
        "indexes": {
            "index_name": {
                "type": "btree",
                "unique": true,
                "fields": ["field1", "field2"]
            }
        },
        "permissions": {
            "user_or_role": ["ALL"]
        }
    }
}
```

You can easily reverse engineer an existing database schema too:
```python
from pypjs import TableDefinition

db = psycopg2.connect()
definition = TableDefinition(schema, table, db)
print definition.to_json()
```

You can then compare your schema, to get a migration breakdown:
```python
from pypjs import CompareSchema

db = psycopg2.connect()
migrations = CompareSchema(my_json_schema, db)
migrations.run()
```
---

# Documentation
## TableDescribe
Generate definitions for a table

### Usage
db_conn = psycopg2.connect()
definition = TableDefinition(schema, name, db_conn)

### Parameters
schema : str - The DB schema the table lives in

name : str - The name of the table to describe

db_conn : connection - A psycopg2.connection object

### Attributes
schema : str
    The DB schema the table lives in

name : str
    The name of the table to describe
primary_key_definition : PrimaryKeyDefinition
    The tables primary key definition

column_definitions : list
    A list of ColumnDefinition's for the table

index_definitions : list
    A list of IndexDefinition's for the table

permission_definitions : list
    A list of PermissionDefinition's for the table

### Methods
#### to_json(set_defaults=False) -> json
Returns the json schema for the table. If __set_defaults = true__ then outputs default values for all valid attributes.
## ColumnDefinition
A structured component that describes a table column
### Methods
#### to_json(set_defaults=False) -> json
Returns the json schema for the table. If __set_defaults = true__ then outputs default values for all valid attributes.

## JsonSpec
Used to validate and load pjs schema files. Once loaded you can unpack a TableDescribe definition.

### Usage
```python
# Validate a schema
try:
    validate_schema({'your':'schema'})
except jsonschema.ValidationError:
    # Yikes, time to investigate

# Or load and validate
spec = JsonSpec(filepath="my_table.json")
dumps(spec.TableDefinition.to_json())
```

---
# Developing for this project
This project uses docker-compose to build and run linting and tests. After pulling the project, you can run the following commands:

__flake8 linting__ docker-compose run lint

__pytests__  docker-compose run tests

If you'd like to contribute, please open a branch and create a PR.
