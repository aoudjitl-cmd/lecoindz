from src.config.settings import settings
import oracledb

def get_connection():
    connection = oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        host=settings.ORACLE_HOST,
        port=settings.ORACLE_PORT,
        service_name=settings.ORACLE_SERVICE,
        protocol="tcps"
    )
    return connection