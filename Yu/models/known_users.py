from datetime import datetime
from peewee import AutoField, IntegerField, CharField, DateTimeField
from ..database import Model

class known_users(Model):
    ID = AutoField()
    ID_Inst = IntegerField(unique=True, index=True)
    acct = CharField(max_length=32, unique=True)
    known_at = DateTimeField(default=datetime.now)
