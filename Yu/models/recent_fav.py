from peewee import AutoField, IntegerField, ForeignKeyField, CharField
from ..database import Model
from .known_users import known_users

class recent_fav(Model):
    ID = AutoField(primary_key=True)
    ID_Inst = ForeignKeyField(known_users, related_name="recent_fav", unique=True)
    tootID = CharField(max_length=32, null=True)
