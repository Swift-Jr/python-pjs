# Todo:
# * Write up the migration generator based on the change list

from jsonspec import JsonSpec
from describe import TableDefinition


def compare_dict(a: dict, b: dict) -> dict:
    """Compare 2 dictionaries to find added, removed and modified keys

    Parameters
    ----------
        a : dict
            The first dictonary to compare
        b  : dict
            The first dictonary to compare

    Returns
    ----------
        tuple
            added_indexes, removed_indexes, modified_indexes
    """
    def get_keys(keys, dict):
        newdict = dict()
        for k in keys:
            newdict[key] = dict[key]
        return newdict

    from_keys = frozenset(a.keys())
    to_keys = frozenset(b.keys())

    added = to_keys - from_keys
    removed = from_keys - to_keys
    exists_in_both = from_keys.intersection(to_keys)
    modified = list()

    for key in exists_in_both:
        if a[key] != b[key]:
            modified.append(key)

    return get_keys(added, b), get_keys(removed, a), modified


def CompareSchemas(from_schema, to_schema) -> PjsSchemaComparison:
    from_spec = JsonSpec(text=from_schema)
    to_spec = JsonSpec(text=to_schema)

    return CompareSpecifications(from_spec, to_spec)


def CompareSpecifications(from_spec, to_spec) -> PjsSchemaComparison:
    from_definition = from_spec.TableDefinition
    to_definition = to_spec.TableDefinition

    result = PjsSchemaComparison()
    result.from_definition = from_definition
    result.to_definition = to_definition

    # name
    if from_definition.name != to_definition.name:
        result.modified_name(to_definition.name)

    if from_spec.get_columns() != to_spec.get_columns():

        from_columns = from_spec.get_columns()
        to_columns = to_spec.get_columns()

        added_columns, removed_columns, modified_columns = compare_dict(from_columns, to_columns)
        result.added_columns(added_columns)
        result.removed_columns(removed_columns)
        result.modified_columns(modified_columns)

    if from_spec.get_primary_key() != to_spec.get_primary_key():
        result.modified_primary_key(to_spec.get_primary_key())

    if from_spec.get_indexes() != to_spec.get_indexes():

        from_indexes = from_spec.get_indexes()
        to_indexes = to_spec.get_indexes()

        added_indexes, removed_indexes, modified_indexes = compare_dict(from_indexes, to_indexes)
        result.added_indexes(added_indexes)
        result.removed_indexes(removed_indexes)
        result.modified_indexes(modified_indexes)

    if from_spec.get_permissions() != to_spec.get_permissions():

        from_permissions = from_spec.get_permissions()
        to_permissions = to_spec.get_permissions()

        added_permissions, removed_permissions, modified_permissions = compare_dict(from_permissions, to_permissions)
        result.added_permissions(added_permissions)
        result.removed_permissions(removed_permissions)
        result.modified_permissions(modified_permissions)

    return result


def CompareSchemaToTable(from_schema, to_table: TableDefinition):
    return CompareSchemas(from_schema, to_table.to_json())


def CompareTableToSchema(from_table: TableDefinition, to_schema):
    return CompareSchemas(from_table.to_json(), to_schema)


class PjsSchemaComparison:
    def modified_name(self, modified_name):
        self.modified_name = modified_name

    def added_columns(self, added_columns):
        self.added_columns = added_columns

    def removed_columns(self, removed_columns):
        self.removed_columns = removed_columns

    def modified_columns(self, modified_columns):
        self.modified_columns = modified_columns

    def modified_primary_key(self, modified_primary_key):
        self.modified_primary_key = modified_primary_key

    def added_indexes(self, added_indexes):
        self.added_indexes = added_indexes

    def removed_indexes(self, removed_indexes):
        self.removed_indexes = removed_indexes

    def modified_indexes(self, modified_indexes):
        self.modified_indexes = modified_indexes

    def added_permissions(self, added_permissions):
        self.added_permissions = added_permissions

    def removed_permissions(self, removed_permissions):
        self.removed_permissions = removed_permissions

    def modified_permissions(self, modified_permissions):
        self.modified_permissions = modified_permissions

    def generate_migration(self):
        self.migration_statements = dict()

        self.migration_statements.append(self.generate_migration_for_name())
        self.migration_statements.append(self.generate_migration_for_new_columns())
        self.migration_statements.append(self.generate_migration_for_dropped_columns())
        self.migration_statements.append(self.generate_migration_for_modified_columns())
        self.migration_statements.append(self.generate_migration_for_new_keys())
        self.migration_statements.append(self.generate_migration_for_dropped_keys())
        self.migration_statements.append(self.generate_migration_for_modified_keys())
        self.migration_statements.append(self.generate_migration_for_new_indexes())
        self.migration_statements.append(self.generate_migration_for_dropped_indsexes())
        self.migration_statements.append(self.generate_migration_for_modified_indexes())
        self.migration_statements.append(self.generate_migration_for_new_permissions())
        self.migration_statements.append(self.generate_migration_for_dropped_permissions())
        self.migration_statements.append(self.generate_migration_for_modified_permissions())

        return self.migration_statements

    def migrate(self, db_conn: connection = None):

        self.generate_migration()

        cursor = db_conn.cursor()

        for migration in self.migration_statements:
            if migration is not None:
                cursor.execute(migration)

        cursor.close()

    def generate_migration_for_name(self) -> dict:
        if not self.modified_name:
            return None

        return 'ALTER TABLE {old_name} RENAME TO {new_name};'.format(
            old_name=self.from_definition.name,
            new_name=self.to_definition.name)

    def generate_migration_for_new_columns(self) -> dict:
        if not self.added_columns:
            return None

        migration = self._generate_alter()

        for column_definition in self.added_columns:
            migration += 'ADD COLUMN {name} {type}'.format(
                name=column_definition.name,
                TYPE=column_definition.type)

            if column_definition.max_length:
                migration += '({length})'.format(
                    length=column_definition.max_length)

            #if column_definition.primary:
            #    migration += ' PRIMARY KEY'

            if column_definition.identity:
                migration += ' GENERATED BY DEFAULT'

            if not column_definition.nullable:
                migration += ' NOT NULL'

            if column_definition.default_value:
                migration += ' DEFAULT {default}'.format(
                    default=column_definition.default_value
                )
            migration += ','

        return migration[:-1] + ';'

    def generate_migration_for_removed_columns(self) -> dict:
        if not self.added_columns:
            return None

        migration = self._generate_alter()

        for column_definition in self.removed_columns:
            migration += 'DROP COLUMN IF EXISTS {name}'.format(
                name=column_definition.name
            )
            migration += ','

        return migration[:-1] + ';'

    def generate_migration_for_modified_columns(self) -> dict:
        if not self.added_columns:
            return None

        migration = self._generate_alter()

        for column_definition in self.removed_columns:
            migration += 'ALTER COLUMN {name} TYPE {type}'.format(
                name=column_definition.name,
                type=column_definition.type
            )

            if column_definition.max_length:
                migration += '({length})'.format(
                    length=column_definition.max_length)

            migration += ' USING {name}::{type}'

            if column_definition.identity:
                migration += ', ALTER COLUMN {name} ADD GENERATED BY DEFAULT'.format(
                    name=column_definition.name,
                )
            else:
                migration += ', ALTER COLUMN {name} DROP IDENTITY IF EXISTS'.format(
                    name=column_definition.name,
                )

            if not column_definition.nullable:
                migration += ', ALTER COLUMN {name} ADD NOT NULL'.format(
                    name=column_definition.name,
                )
            else:
                migration += ', ALTER COLUMN {name} DROP NOT NULL'.format(
                    name=column_definition.name,
                )

            if column_definition.default_value:
                migration += ', ALTER COLUMN {name} SET DEFAULT {default}'.format(
                    name=column_definition.name,
                    default=column_definition.default_value
                )
            else:
                migration += ', ALTER COLUMN {name} DROP DEFAULT {default}'.format(
                    name=column_definition.name,
                    default=column_definition.default_value
                )

        return migration + ';'

    def _generate_alter(self):
        return 'ALTER TABLE {name} '.format(name=self.to_definition.name)
