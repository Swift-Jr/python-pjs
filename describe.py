from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import re
from typing import overload


class TableDefinition:
    def __init__(self,
                 schema: str = None,
                 name: str = None,
                 db_conn: connection = None):

        self.primary_key_definition = PrimaryKeyDefinition()
        self.column_definitions = list()
        self.index_definitions = list()
        self.permission_definitions = list()

        self.name = name
        self.namespace = schema
        self.connection = db_conn

        if (self.name is None
                and self.namespace is None
                and self.connection is None):
            return

        if (self.name is None
                or self.namespace is None
                or self.connection is None):
            raise NameError("schema, name and connection are "
                            "required to describe a table")

        if not self.check_table_exists():
            raise NameError("The requested table does not exist: "
                            "{}.{}".format(self.namespace, self.name))

        self.get_column_list()
        self.get_index_list()
        self.get_permission_list()

    def check_table_exists(self) -> bool:
        where_dict = {"table_schema": self.namespace, "table_name": self.name}

        cursor = self.connection.cursor()
        cursor.execute("""
                        SELECT
                            COUNT(*)
                        FROM
                            information_schema.tables
                        WHERE
                            table_schema = %(table_schema)s
                            AND table_name = %(table_name)s
                        """,
                       where_dict)

        result = cursor.fetchone()[0] == 1
        cursor.close()

        return result

    def get_column_list(self) -> list:
        """
        Get a list of dictionaries for the specified
        schema.table in the database connected to.
        """

        where_dict = {"table_schema": self.namespace, "table_name": self.name}

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""SELECT
                            col.column_name,
                            col.is_nullable::TEXT = 'YES' AS is_nullable,
                            col.data_type,
                            col.character_maximum_length,
                            col.is_identity::TEXT = 'YES' AS is_identity,
                            col.column_default,
                            keys.constraint_name,
                            cons.constraint_type::TEXT = 'PRIMARY KEY'::TEXT
                                AS is_primary_key
                        FROM
                            information_schema.columns col
                        LEFT JOIN
                            information_schema.key_column_usage keys
                            ON
                                col.column_name = keys.column_name
                                AND col.table_name = keys.table_name
                                AND col.table_schema  = keys.table_schema
                        LEFT JOIN information_schema.table_constraints cons
                            ON
                                cons.constraint_name = keys.constraint_name
                                AND cons.table_name  = col.table_name
                                AND cons.table_schema = col.table_schema
                        WHERE
                            col.table_schema = %(table_schema)s
                            AND col.table_name = %(table_name)s
                        ORDER BY
                            col.column_name""",
                       where_dict)

        columns = cursor.fetchall()

        cursor.close()

        self.extract_column_definitions(columns)

        return columns

    def extract_column_definitions(self, columns: list) -> list:
        self.column_definitions = list()
        self.primary_key_definition = PrimaryKeyDefinition()

        for column in columns:
            column_definition = ColumnDefinition(
                name=column.get('column_name'),
                type=column.get('data_type'),
                nullable=column.get('is_nullable'),
                max_length=column.get('character_maximum_length'),
                default_value=column.get('column_default'),
                identity=column.get('is_identity')
            )

            self.column_definitions.append(column_definition)

            if column.get('is_primary_key'):
                self.primary_key_definition.add_field(
                    column.get('column_name')
                )
                self.primary_key_definition.set_name(
                    column.get('constraint_name')
                )

        return self.column_definitions

    def get_index_list(self) -> list:
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

        return indexes

    def extract_index_definitions(self, indexes: list) -> list:
        self.index_definitions = list()

        for index in indexes:
            index_str = index.get('indexdef')

            index_definition = IndexDefinition(
                name=index.get('indexname'),
                unique='UNIQUE' in index_str
            )

            if 'btree' in index_str:
                index_definition.set_type('btree')

            fields = re.findall(r'\((.*?)\)', index_str)
            index_definition.set_fields(fields[0].split(', '))

            self.index_definitions.append(index_definition)

        return self.index_definitions

    def get_permission_list(self) -> None:
        """
        Get a list of permissions for the specified
        schema.table in the database connected to.
        """

        where_dict = {"table_schema": self.namespace, "table_name": self.name}

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""SELECT
                            grantee,
                            privilege_type
                        FROM
                            information_schema.role_table_grants
                        WHERE
                            grantee NOT in('postgres', 'PUBLIC')
                            AND table_schema = %(table_schema)s
                            AND table_name = %(table_name)s
                        ORDER BY
                            grantee,
                            privilege_type""",
                       where_dict)

        permissions = cursor.fetchall()

        cursor.close()

        self.extract_permission_definitions(permissions)

        return permissions

    def extract_permission_definitions(self, permissions: list) -> list:
        self.permission_definitions = list()
        users = dict()

        for permission in permissions:
            grantee = permission.get('grantee')

            if grantee not in users.keys():
                users[grantee] = list()

            users[grantee].append(permission.get('privilege_type'))

        for name, grants in users.items():
            permission_definition = PermissionDefinition(
                name,
                grants
            )
            self.permission_definitions.append(permission_definition)

        return self.permission_definitions


class PrimaryKeyDefinition:
    fields = list()

    def __init__(self, field: str = None):
        if field:
            self.add_field(field)

    def set_name(self, name: str):
        self.constraint_name = name

    def add_field(self, name: str):
        self.fields.append(name)

    def to_json(self):
        json = dict()
        json['constraint'] = self.constraint_name
        json['fields'] = self.fields

        return json


class ColumnDefinition:
    @overload
    def __init__(self,
                 name: str,
                 type: str,
                 nullable: bool,
                 max_length: int,
                 default_value: str,
                 identity: bool
                 ):
        ...

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.type = kwargs.get('type', None)
        self.nullable = kwargs.get('nullable', False)
        self.max_length = kwargs.get('max_length', None)
        self.default_value = kwargs.get('default_value', None)

    def to_json(self):
        schema = dict()
        schema['type'] = self.type
        schema['nullable'] = self.nullable
        schema['max_length'] = self.max_length
        schema['default_value'] = self.default_value

        json = dict()
        json[self.name] = schema

        return json


class IndexDefinition:
    @overload
    def __init__(self, name: str, unique: bool, type: str, fields: list):
        ...

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.unique = kwargs.get('unique', False)
        self.type = kwargs.get('type', None)
        self.fields = kwargs.get('fields', list())

    def set_type(self, type: str):
        self.type = type

    def set_fields(self, fields: list):
        self.fields = fields

    def to_json(self):
        schema = dict()
        schema['type'] = self.type
        schema['unique'] = self.unique
        schema['fields'] = self.fields

        json = dict()
        json[self.name] = schema

        return json


class PermissionDefinition:
    def __init__(self, role_or_user: str, grants: list):
        self.name = role_or_user
        self.grants = grants

    def to_json(self):
        json = dict()
        json[self.name] = self.grants

        return json
