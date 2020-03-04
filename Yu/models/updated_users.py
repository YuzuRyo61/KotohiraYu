from datetime import datetime
from peewee import AutoField, ForeignKeyField, CharField, DateTimeField
from ..database import Model
from .known_users import known_users

class updated_users(Model):
    ID = AutoField(primary_key=True)
    ID_Inst = ForeignKeyField(known_users, related_name="updated_users", unique=True)
    date = DateTimeField(default=datetime.now)
