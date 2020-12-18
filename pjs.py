# flake8: noqa
---
# https://github.com/CodeDrome/postgresql-python/blob/master/postgresqlschemareader.py
# https://www.dataquest.io/blog/postgres-internals/
#
# DONE: use pg_catalog to generate a definition from the existing table

# GIVEN we have a json definition in a file
# AND we have a table in the database that matches the schema
# WHEN we compare the json schema with the TableDefinition
# THEN expect no changes to result


# Generate a schema from the definition
# compare 2 json schemas
# loop through the fields, indexs of each
# when a difference occurs register a drop or alter
# generate an alter using the new spec
# generate drops usinfg the old spec
#
# migrate by using the generate to create json schemas for each existing table

# this is what we want to load/validate our JSON files in
# tablespec = JsonSpecificafion(file.json)
#
# Consider SchemaDefinition - could contain default roles for all tables, etc
class JsonSpecificafion:
    def validate_spec:
    def load_specification(table):
        return JsonSpecificafion
    def fields
    def tablename

class SchemaTable:
    def load_table_schema:

class SchemaField:
    def generate_drop:

    def generate_alter:

class MigrationAlter:

class MigrationDrop:

class PjsComparisonResult:
    newTable
    removedTable
    newFields
    removedFields
    changedFields
    newIndexs
    missingIndexs
    newPermission
    missingPermission

class pyjsondb:
    def compare(JsonSpecificafion, JsonSpecificafion):

    def compare_fields(spec, existing):
        for field in spec:
            if not existing[field]:
                removeField(field)

            hash1 = md5(stringify(field))
            hash2 = md5(stringify(existing[field]))

            if hash1 is not hash2:
                changedField(field)



    def migrate():
        for field in comparison.removedFields:
            sql.ex(DROP field.name)

        for field in comparison.changedFields:
            sql.ex(ALTER TABLE DROP COLUMN field.name)
            sql.ex(generateAlter(field))

    def generateAlter(field):
        return ALTER TABLE ADD COLUMN field.name

    def load_table_to_jsonSpec
