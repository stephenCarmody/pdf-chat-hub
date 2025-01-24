import logging
from typing import Tuple

import psycopg

from settings import settings

logger = logging.getLogger(__name__)


def test_db_connection() -> Tuple[bool, str]:
    """
    Test the database connection and wake up RDS instance if needed.
    """
    try:
        with psycopg.connect(settings.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result and result[0] == 1:
                    return True, "Database connection initialized"
                return False, "Database connection test failed"
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False, str(e)


def trigger_db_wakeup() -> None:
    """
    Trigger a database connection to wake up RDS instance if needed.
    Non-blocking - doesn't wait for connection to be established.
    """
    try:
        psycopg.connect(settings.connection_string).close()
    except Exception as e:
        logger.error(f"Failed to trigger database wakeup: {str(e)}")
