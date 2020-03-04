from .config import config
from peewee import Model as PeeWeeModel, MySQLDatabase, PostgresqlDatabase

if str(config['database']['mode']).lower() == "mysql":
    DATABASE =  MySQLDatabase(
                    str(config['database']['name']), 
                    user=str(config['database']['user']),
                    password=str(config['database']['pass']),
                    host=str(config['database']['host']),
                    port=int(config['database']['port'])
                )
elif str(config['database']['mode']).lower() == "postgresql":
    DATABASE =  PostgresqlDatabase(
                    str(config['database']['name']), 
                    user=str(config['database']['user']),
                    password=str(config['database']['pass']),
                    host=str(config['database']['host']),
                    port=int(config['database']['port'])
                )
else:
    raise Exception(f"This database engine mode is not supported!: {str(config['database']['mode'])}")

class Model(PeeWeeModel):
    class Meta:
        database = DATABASE
