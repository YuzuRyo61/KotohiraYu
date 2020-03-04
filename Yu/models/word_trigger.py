from datetime import datetime
from peewee import AutoField, CharField, DateTimeField
from ..database import Model
from .known_users import known_users

class word_trigger(Model):
    ID = AutoField(primary_key=True)
    trigger_name = CharField(max_length=32, unique=True)
    date = DateTimeField(default=datetime.now)
