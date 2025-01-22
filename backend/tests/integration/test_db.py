import psycopg2
import pytest

from settings import settings


@pytest.fixture
def db_connection():
    """Fixture that creates and tears down a database connection"""
    conn = psycopg2.connect(settings.connection_string)
    yield conn
    conn.close()


@pytest.fixture
def db_cursor(db_connection):
    """Fixture that creates and tears down a database cursor"""
    cur = db_connection.cursor()
    yield cur
    cur.close()


@pytest.fixture
def vector_table(db_connection, db_cursor):
    """Fixture that sets up and tears down a test vector table"""
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS test_vectors (
            id serial PRIMARY KEY,
            embedding vector(3)
        )
    """
    )
    db_connection.commit()
    yield
    db_cursor.execute("DROP TABLE IF EXISTS test_vectors")
    db_connection.commit()


@pytest.mark.integration
def test_postgres_connection_is_healthy(db_cursor):
    """Test PostgreSQL connection using settings"""
    # WHEN we attempt to execute a simple query
    db_cursor.execute("SELECT 1")
    result = db_cursor.fetchone()

    # THEN the connection is successful and returns expected result
    assert result[0] == 1


@pytest.mark.integration
def test_pg_vector_extension_enabled(db_cursor):
    """Test that pgvector extension is properly initialized"""
    # WHEN we check installed extensions
    db_cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    result = db_cursor.fetchone()

    # THEN the vector extension should be installed
    assert result is not None
    assert result[0] == "vector"


@pytest.mark.integration
def test_pg_vector_table_creation(db_cursor):
    """Test creating a table with vector type"""
    # WHEN we create a test table with vector type
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS test_vectors (
            id serial PRIMARY KEY,
            embedding vector(3)
        )
    """
    )

    # THEN we can check the table columns are created with the correct data type
    db_cursor.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'test_vectors'"
    )
    result = db_cursor.fetchall()
    assert len(result) == 2
    assert result[0][0] == "id"
    assert result[0][1] == "integer"
    assert result[1][0] == "embedding"
    assert result[1][1] == "USER-DEFINED"


@pytest.mark.integration
def test_pg_vector_single_insert(db_connection, db_cursor, vector_table):
    """Test inserting and retrieving a single vector"""
    # WHEN we insert a vector
    db_cursor.execute("INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]')")
    db_connection.commit()

    # THEN we can retrieve the vector
    db_cursor.execute("SELECT embedding FROM test_vectors LIMIT 1")
    result = db_cursor.fetchone()
    assert result is not None


@pytest.mark.integration
def test_pg_vector_similarity_search(db_connection, db_cursor, vector_table):
    """Test vector similarity search functionality"""
    # GIVEN multiple vectors in the database
    db_cursor.execute(
        "INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]'), ('[7,8,9]'), ('[10,11,12]'), ('[13,14,15]')"
    )
    db_connection.commit()

    # WHEN we perform a similarity search
    db_cursor.execute(
        "SELECT * FROM test_vectors ORDER BY embedding <-> '[1,2,3]' LIMIT 3"
    )
    result = db_cursor.fetchall()

    # THEN we get the closest 3 vectors
    assert len(result) == 3
