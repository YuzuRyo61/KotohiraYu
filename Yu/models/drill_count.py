from peewee import AutoField, IntegerField, ForeignKeyField, CharField
from ..database import Model
from .known_users import known_users

class drill_count(Model):
    ID = AutoField(primary_key=True)
    ID_Inst = ForeignKeyField(known_users, related_name="drill_count", unique=True)
    tootCount = CharField(max_length=32)
