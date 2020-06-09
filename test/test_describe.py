import os
import psycopg2
import pytest
import sys

from describe import TableDefinition, ColumnDefinition, PrimaryKeyDefinition


@pytest.fixture(scope="module")
def setup_db(request):
    def drop_db():
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("DROP SCHEMA IF EXISTS pjs_pytest_testing CASCADE;")
        cursor.execute("DROP ROLE IF EXISTS pjs_pytest_role;")
        db.commit()
        return

    db = get_connection()
    cursor = db.cursor()
    # Create a schema to use
    cursor.execute("CREATE SCHEMA pjs_pytest_testing;")
    # Create a sample table that can have additional types to test
    cursor.execute("""CREATE TABLE pjs_pytest_testing.sample_table (
        id bigint not null,
        int_col int,
        int_nn_col int not null,
        text_col text,
        text_nn_col text not null,
        ts_col timestamp,
        ts_tz_col timestamp with time zone,
        ts_tz_default_col timestamp with time zone default now(),
        CONSTRAINT sample_table_pkey PRIMARY KEY (id)
    );""")
    # Create a role to test permissions
    cursor.execute("CREATE ROLE pjs_pytest_role;")
    cursor.execute("""GRANT ALL
        ON pjs_pytest_testing.sample_table
        TO pjs_pytest_role;""")
    db.commit()

    request.addfinalizer(drop_db)


def get_connection():
    try:
        connection = psycopg2.connect(user=os.environ["DB_USER"],
                                      password=os.environ["DB_PASS"],
                                      host=os.environ["DB_HOST"],
                                      port=os.environ["DB_PORT"],
                                      database=os.environ["DB_NAME"])
        return connection
    except Exception as e:
        sys.exit(e)


def prepare_table_definiton() -> TableDefinition:
    table_def = TableDefinition()
    table_def.name = 'sample_table'
    table_def.namespace = 'pjs_pytest_testing'
    table_def.connection = get_connection()

    return table_def


def test_describe_missing_params_table():
    with pytest.raises(NameError):
        TableDefinition('missing_params')


def test_describe_non_existing_table():
    with pytest.raises(NameError):
        TableDefinition('public', 'not_real', get_connection())


@pytest.mark.usefixtures("setup_db")
class TestDefinition:
    def test_describe_table_exists(self):
        object = TableDefinition()
        object.name = 'not_real'
        object.namespace = 'not_real'
        object.connection = get_connection()
        assert object.check_table_exists() is False,\
            "The table should not exist"

        object = prepare_table_definiton()
        assert object.check_table_exists() is True,\
            "The table should exist"

    def test_describe_column_definition(self):
        object = ColumnDefinition(
            name='column_name',
            type='column_type',
            nullable=True,
            max_length=128,
            default_value="now()"
        )

        actual_json = object.to_json()
        expected_json = dict(
            column_name=dict(
                type="column_type",
                nullable=True,
                max_length=128,
                default_value="now()"
            )
        )

        assert actual_json == expected_json,\
            "The column definition should match the expected"

    def test_describe_primary_key_definition(self):
        object = PrimaryKeyDefinition('field')
        object.add_field('second_field')
        object.set_name('primary_key_name')

        actual_json = object.to_json()

        expected_json = dict(
            fields=['field', 'second_field'],
            constraint='primary_key_name'
        )

        assert actual_json == expected_json,\
            "The primary key definition should match the expected"

    def test_describe_get_columns(self):
        object = prepare_table_definiton()
        columns = object.get_column_definition()

        assert isinstance(columns, list)

        assert len(columns) == 8,\
            "There should be 8 columns defined on the table"

        id_column = dict(
            column_name="id",
            is_nullable=False,
            data_type="bigint",
            character_maximum_length=None,
            is_identity=False,
            column_default=None,
            constraint_name='sample_table_pkey',
            is_primary_key=True
        )
        assert columns[0] == id_column,\
            "The first column should be the id column"

    def test_describe_extract_columns(self):
        object = prepare_table_definiton()
        columns = object.get_column_definition()
        column_defs = object.extract_column_definitions(columns)

        assert isinstance(column_defs, list)
        assert isinstance(column_defs[0], ColumnDefinition)

        assert len(column_defs) == 8,\
            "There should be 8 column definitions"

        id_column = ColumnDefinition(
            name='id',
            type='bigint',
            nullable=False,
            max_length=None,
            default_value=None,
            identity=False
        )
        assert column_defs[0].to_json() == id_column.to_json(),\
            "The first column definition should be the id column"

    def test_describe_extract_primary_key(self):
        object = prepare_table_definiton()
        columns = object.get_column_definition()
        object.extract_column_definitions(columns)
        primary_key_def = object.primary_key_definition

        assert isinstance(primary_key_def, PrimaryKeyDefinition)

        primary_key_expected_def = PrimaryKeyDefinition('id')
        primary_key_expected_def.set_name('sample_table_pkey')

        assert primary_key_def.to_json() == primary_key_expected_def.to_json(),\
            "The primary key should be the id column"

# def test_describe_column_to_json():
#
# def test_describe_get_indexes():
#
# def test_describe_extract_indexes():
#
# def test_describe_index_to_json():
#
# def test_describe_get_permissions():
#
# def test_describe_extract_permissions():
#
# def test_describe_permission_to_json():

# def test_describe_table():
#     definition = TableDefinition('pjs_pytest_testing', 'sample_table', get_connection())
