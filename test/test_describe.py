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


def setup_function():
    cursor = get_connection().cursor()
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
        ts_tz_default_col as timestamp with time zone default now(),
        CONSTRAINT sample_table_pkey PRIMARY KEY (id)
    );""")
    # Create a role to test permissions
    cursor.execute("CREATE ROLE pjs_pytest_role;")
    cursor.execute("""GRANT ALL
        ON pjs_pytest_testing.sample_table
        TO pjs_pytest_role;""")


def teardown_function():
    cursor = get_connection().cursor()
    cursor.execute("DROP SCHEMA IS EXISTS pjs_pytest_testing CASCADE;")
    cursor.execute("DROP ROLE IF EXISTS pjs_pytest_role;")
    return


def test_describe_missing_params_table():
    with pytest.raises(NameError):
        definition = TableDefinition()


def test_describe_non_existing_table():
    with pytest.raises(NameError):
        definition = TableDefinition('public', 'not_real', get_connection())

def test_describe_get_columns():

def test_describe_extract_columns():

def test_describe_column_to_json():

def test_describe_get_indexes():

def test_describe_extract_indexes():

def test_describe_index_to_json():

def test_describe_get_permissions():

def test_describe_extract_permissions():

def test_describe_permission_to_json():

def test_describe_table():
    definition = TableDefinition('pjs_pytest_testing', 'sample_table', get_connection())
