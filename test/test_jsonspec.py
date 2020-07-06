import jsonspec

from describe import (TableDefinition,
                      ColumnDefinition,
                      IndexDefinition,
                      PermissionDefinition,
                      PrimaryKeyDefinition)

from test.helpers import load_sample_json


def test_pjs_schema_is_valid():
    assert type(jsonspec.PJS_SCHEMA) is dict, \
        'The rule schema loaded is valid json'


def test_validate_a_valid_schema():
    valid_schema = load_sample_json('valid_schema.json')

    assert type(valid_schema) is dict, \
        'The target schema loaded is valid json'

    assert jsonspec.validate_schema(valid_schema), \
        'The target schema loaded is valid to the pjs schema'


def test_load_file():
    file = 'test/sample_json/valid_schema.json'
    valid_schema = jsonspec.load_file(file)

    assert type(valid_schema) is dict, \
        'The schema loaded is valid json'


def test_jsonspec_loads_a_tabledefinition():
    spec = jsonspec.JsonSpec(filepath='test/sample_json/valid_schema.json')

    assert spec.is_valid
    assert type(spec) is jsonspec.JsonSpec
    assert type(spec.TableDefinition) is TableDefinition

    assert len(spec.TableDefinition.column_definitions) == 2

    expected_column = ColumnDefinition(name="minimum", type="string")
    assert spec.TableDefinition.column_definitions[0].to_json() \
        == expected_column.to_json()

    assert len(spec.TableDefinition.index_definitions) == 2

    expected_index = IndexDefinition(name="simple_index", fields=["field"])
    assert spec.TableDefinition.index_definitions[0].to_json() \
        == expected_index.to_json()

    assert len(spec.TableDefinition.permission_definitions) == 2

    expected_permission = PermissionDefinition(
        role_or_user="role",
        grants=["ALL"])
    assert spec.TableDefinition.permission_definitions[0].to_json() \
        == expected_permission.to_json()

    assert type(spec.TableDefinition.primary_key_definition) \
        is PrimaryKeyDefinition

    expected_key = PrimaryKeyDefinition(table_definition=spec.TableDefinition)
    expected_key.add_field("field1").add_field("field2")
    assert spec.TableDefinition.primary_key_definition.to_json(spec) \
        == expected_key.to_json()
