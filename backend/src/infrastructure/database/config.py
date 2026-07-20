from src.config import Settings

DATABASE_URL_ENVIRONMENT_VARIABLE = "LIFE_OS_DATABASE_URL"


def get_database_url() -> str:
    return Settings().database_url
