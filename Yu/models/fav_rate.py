from peewee import AutoField, IntegerField, ForeignKeyField
from ..database import Model
from .known_users import known_users

class fav_rate(Model):
    ID = AutoField(primary_key=True)
    ID_Inst = ForeignKeyField(known_users, related_name="fav_rate", unique=True)
    rate = IntegerField(default=100)
