from src.config.settings import settings
import oracledb

def get_connection():
    dsn = f"(description=(address=(protocol=tcps)(host={settings.ORACLE_HOST})(port={settings.ORACLE_PORT}))(connect_data=(service_name={settings.ORACLE_SERVICE})))"

    connection = oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=dsn
    )

    return connection