import json

from jsonschema import validate

from describe import (TableDefinition,
                      ColumnDefinition,
                      IndexDefinition,
                      PermissionDefinition,
                      PrimaryKeyDefinition)


def validate_schema(schema: str):
    validate(schema, PJS_SCHEMA)
    return True


def load_file(path: str, as_json: bool = True) -> str:
    handle = open(path)

    if as_json:
        text = json.load(handle)
    else:
        text = handle.read()

    handle.close()

    return text


PJS_SCHEMA = load_file('pjs.schema')


class JsonSpec:
    def __init__(self,
                 filepath: str = None,
                 text: str = None):

        self.is_valid = False
        self.TableDefinition = None
        self.specification = None

        if filepath is not None:
            json_specification = load_file(filepath)

        if text is not None:
            json_specification = json.loads(text)

        if json_specification is not None:
            validate_schema(json_specification)
            self.is_valid = True

        if self.is_valid:
            self.specification = json_specification
            self.load_schema(json_specification)

    def load_schema(self, json_spec: str) -> TableDefinition:
        definition = TableDefinition()

        definition.name = json_spec.get('name')

        for field_name, field_spec in self.get_columns():
            definition.column_definitions \
                .append(self.load_field(field_name, field_spec))

        for index_name, index_spec in self.get_indexes():
            definition.index_definitions \
                .append(self.load_index(index_name, index_spec))

        for perm_name, perm_spec in self.get_permissions():
            definition.permission_definitions \
                .append(self.load_permission(perm_name, perm_spec))

        definition.primary_key_definition \
            = self.load_primarykey(self.get_primary_key(), definition)

        self.TableDefinition = definition

        return self.TableDefinition

    def load_field(self, name, spec) -> ColumnDefinition:
        return ColumnDefinition(name=name, **spec)

    def load_index(self, name, spec) -> IndexDefinition:
        return IndexDefinition(name=name, **spec)

    def load_permission(self, name, grants) -> PermissionDefinition:
        return PermissionDefinition(role_or_user=name, grants=grants)

    def load_primarykey(self, spec, table) -> PrimaryKeyDefinition:
        key = PrimaryKeyDefinition(table_definition=table)
        for field in spec.get('fields'):
            key.add_field(field)
        return key

    def get_columns(self):
        return self.specification.get('schema').items()

    def get_indexes(self):
        return self.specification.get('indexes').items()

    def get_permissions(self):
        return self.specification.get('permissions').items()

    def get_primary_key(self):
        return self.specification.get('primary_key')
