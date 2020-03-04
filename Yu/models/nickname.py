from peewee import AutoField, IntegerField, ForeignKeyField, CharField
from ..database import Model
from .known_users import known_users

class nickname(Model):
    ID = AutoField(primary_key=True)
    ID_Inst = ForeignKeyField(known_users, related_name="nickname", unique=True)
    nickname = CharField(max_length=32)
