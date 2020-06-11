from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import re
from typing import overload


class TableDefinition:
    """Generate definitions for a table

    Usage
    ---------
    db_conn = psycopg2.connect()
    definition = TableDefinition(schema, name, db_conn)

    Parameters
    ----------
    schema : str
        The DB schema the table lives in
    name : str
        The name of the table to describe
    db_conn : connection
        A psycopg2.connection object

    Attributes
    ----------
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

    """

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
                            c.column_name,
                            c.is_nullable::TEXT = 'YES' AS is_nullable,
                            CASE
                                WHEN c.domain_name is not null
                                    THEN domain_name
                                WHEN c.data_type='character varying'
                                    THEN 'varchar('||
                                        c.character_maximum_length||')'
                                WHEN c.data_type='integer'
                                    THEN 'int'
                                WHEN c.data_type='numeric'
                                    THEN 'numeric('||c.numeric_precision||'
                                                    ,'||c.numeric_scale||')'
                                WHEN c.data_type='timestamp without time zone'
                                    THEN 'timestamp'
                                ELSE c.data_type
                            end as data_type,
                            c.character_maximum_length,
                            c.is_identity::TEXT = 'YES' AS is_identity,
                            c.column_default,
                            keys.constraint_name,
                            cons.constraint_type::TEXT = 'PRIMARY KEY'::TEXT
                                AS is_primary_key
                        FROM
                            information_schema.columns c
                        LEFT JOIN
                            information_schema.key_column_usage keys
                            ON
                                c.column_name = keys.column_name
                                AND c.table_name = keys.table_name
                                AND c.table_schema  = keys.table_schema
                        LEFT JOIN information_schema.table_constraints cons
                            ON
                                cons.constraint_name = keys.constraint_name
                                AND cons.table_name  = c.table_name
                                AND cons.table_schema = c.table_schema
                        WHERE
                            c.table_schema = %(table_schema)s
                            AND c.table_name = %(table_name)s
                        ORDER BY
                            c.column_name""",
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
                identity=column.get('is_identity'),
                primary=column.get('is_primary_key')
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

    def to_json(self, set_defaults: bool = False):
        column_schema = dict()
        for column in self.column_definitions:
            for name, jdef in column.to_json(set_defaults).items():
                column_schema[name] = jdef

        index_schema = dict()
        for index in self.index_definitions:
            for name, jdef in index.to_json(set_defaults).items():
                if name != self.primary_key_definition.constraint_name:
                    index_schema[name] = jdef

        permission_schema = dict()
        for permission in self.permission_definitions:
            for name, jdef in permission.to_json().items():
                permission_schema[name] = jdef

        json = dict()
        json[self.name] = dict(
            schema=column_schema,
            primary_key=self.primary_key_definition.to_json(),
            indexes=index_schema,
            permissions=permission_schema
        )

        return json


class PrimaryKeyDefinition:
    def __init__(self, field: str = None):
        self.fields = list()
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
                 identity: bool = False,
                 nullable: bool = False,
                 max_length: int = None,
                 default_value: str = None,
                 primary: bool = False):
        ...

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        if self.name is None or self.type is None:
            raise NameError('Name and type are mandatory requirements for a '
                            'ColumnDefinition')

        self.identity = kwargs.get('nullable', False)
        self.nullable = kwargs.get('nullable', False)
        self.max_length = kwargs.get('max_length', None)
        self.default_value = kwargs.get('default_value', None)
        self.primary = kwargs.get('primary', False)

    def set_primary(self):
        self.primary = True

    def to_json(self, set_defaults: bool = False):
        schema = dict()
        schema['type'] = self.type
        if (not self.nullable and not self.primary) or set_defaults:
            schema['nullable'] = self.nullable
        if self.max_length or set_defaults:
            schema['max_length'] = self.max_length
        if self.default_value or set_defaults:
            schema['default_value'] = self.default_value

        json = dict()
        json[self.name] = schema

        return json


class IndexDefinition:
    @overload
    def __init__(self,
                 name: str,
                 fields: list = list(),
                 unique: bool = True,
                 type: str = 'btree'):
        ...

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        if self.name is None:
            raise NameError('Name is mandatory requirements for '
                            'an IndexDefinition')

        self.fields = kwargs.get('fields', list())
        self.unique = kwargs.get('unique', False)
        self.type = kwargs.get('type', None)

    def set_type(self, type: str):
        self.type = type

    def set_fields(self, fields: list):
        self.fields = fields

    def to_json(self, set_defaults: bool = False):
        schema = dict()
        if self.type or set_defaults:
            if self.type:
                schema['type'] = self.type
            else:
                schema['type'] = 'btree'
        if self.unique or set_defaults:
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
        if len(self.grants) == 7:
            json[self.name] = ['ALL']
        else:
            json[self.name] = self.grants

        return json
