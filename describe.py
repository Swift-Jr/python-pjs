from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import re


class TableDefinition:
    def __init__(self, schema: str, name: str, connection: connection):
        self.primary_key_definition = PrimaryKeyDefinition()
        self.column_definitions = list()
        self.index_definitions = list()

        self.name = name
        self.namespace = schema
        self.connection = connection

        if (self.name is not None
                and self.namespace is not None
                and self.connection is not None):
            self.get_column_definition()
            self.get_index_definition()
        else:
            raise NameError("schema, name and connection are "
                            "required to describe a table")

    def get_column_definition(self) -> None:
        """
        Get a list of dictionaries for the specified
        schema.table in the database connected to.
        """

        where_dict = {"table_schema": self.namespace, "table_name": self.name}

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""SELECT
                           column_name,
                           is_nullable,
                           data_type,
                           character_maximum_length,
                           is_identity
                       FROM
                            information_schema.columns
                       WHERE
                            table_schema = %(table_schema)s
                            AND table_name = %(table_name)s""",
                       where_dict)

        columns = cursor.fetchall()

        cursor.close()

        self.extract_column_definitions(columns)

    def extract_column_definitions(self, columns: list) -> None:
        for column in columns:
            column_definition = ColumnDefinition(
                column.get('column_name'),
                column.get('data_type'),
                column.get('is_nullable').upper() == 'YES',
                column.get('character_maximum_length')
            )

            self.column_definitions.push(column_definition)

            if column.get('is_identity').upper() == 'YES':
                self.primary_key_definition.add_field(
                    column.get('column_name')
                )

    def get_index_definition(self) -> None:
        """
        Get a list of indexes for the specified
        schema.table in the database connected to.
        """

        where_dict = {"table_schema": self.namespace, "table_name": self.name}

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""SELECT
                           indexname,
                           indexdef
                       FROM
                            pg_indexes
                       WHERE
                            schemaname = %(table_schema)s
                            AND tablename = %(table_name)s""",
                       where_dict)

        indexes = cursor.fetchall()

        cursor.close()

        self.extract_index_definitions(indexes)

    def extract_index_definitions(self, indexes: list) -> None:
        object = dict()

        for index in indexes:
            index_str = index.get('indexdef');

            index_definition = IndexDefinition(
                index.get('indexname'),
                'UNIQUE' in index_str
            )

            if 'btree' in index_str:
                index_definition.type = 'btree'

            fields = re.findall(r'\((.*?)\)', index_str)
            index_definition.fields = fields.split(', ')

            self.index_definitions.push(index_definition)


class PrimaryKeyDefinition:
    fields = list()

    def __init__(self, field):
        self.add_field(field)

    def add_field(self, name):
        self.fields.push(field)

    def to_json(self):
        json = dict()
        json['fields'] = ','.join(self.fields)

        return json


class ColumnDefinition:
    def __init__(self, name, type, nullable, max_length):
        self.name = name
        self.type = type
        self.nullable = nullable
        self.max_length = max_length

    def to_json(self):
        schema = dict()
        schema['type'] = self.type
        schema['nullable'] = self.nullable
        schema['max_length'] = self.max_length

        json = dict()
        json[self.name] = schema

        return json


class IndexDefinition:
    def __init__(self, name: str, unique: bool, type: str, fields: list):
        self.name = name
        self.unique = unique
        self.type = type
        self.fields = fields

    def to_json(self):
        schema = dict()
        schema['type'] = self.type
        schema['unique'] = self.nullable
        schema['fields'] = ','.join(self.fields)

        json = dict()
        json[self.name] = schema

        return json


class PermissionDefinition:
    def __init__(self):
        return
