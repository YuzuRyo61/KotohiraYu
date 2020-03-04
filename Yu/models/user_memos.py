from peewee import AutoField, CharField, TextField
from ..database import Model

class user_memos(Model):
    ID = AutoField(primary_key=True)
    memo_time = CharField(max_length=12, unique=True)
    body = TextField(default="[]")
