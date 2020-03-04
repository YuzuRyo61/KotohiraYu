# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class known_users(peewee.Model):
    ID = AutoField(primary_key=True)
    ID_Inst = IntegerField(unique=True)
    acct = CharField(max_length=32, unique=True)
    known_at = DateTimeField(default=datetime.datetime.now)
    class Meta:
        table_name = "known_users"


@snapshot.append
class fav_rate(peewee.Model):
    ID = AutoField(primary_key=True)
    ID_Inst = snapshot.ForeignKeyField(backref='fav_rate', index=True, model='known_users', unique=True)
    rate = IntegerField(default=100)
    class Meta:
        table_name = "fav_rate"


@snapshot.append
class nickname(peewee.Model):
    ID = AutoField(primary_key=True)
    ID_Inst = snapshot.ForeignKeyField(backref='nickname', index=True, model='known_users', unique=True)
    nickname = CharField(max_length=32)
    class Meta:
        table_name = "nickname"


@snapshot.append
class recent_fav(peewee.Model):
    ID = AutoField(primary_key=True)
    ID_Inst = snapshot.ForeignKeyField(backref='recent_fav', index=True, model='known_users', unique=True)
    tootID = CharField(max_length=32, null=True)
    class Meta:
        table_name = "recent_fav"


@snapshot.append
class updated_users(peewee.Model):
    ID = AutoField(primary_key=True)
    ID_Inst = snapshot.ForeignKeyField(backref='updated_users', index=True, model='known_users', unique=True)
    date = DateTimeField(default=datetime.datetime.now)
    class Meta:
        table_name = "updated_users"


@snapshot.append
class user_memos(peewee.Model):
    ID = AutoField(primary_key=True)
    memo_time = CharField(max_length=12, unique=True)
    body = TextField(default='[]')
    class Meta:
        table_name = "user_memos"


@snapshot.append
class word_trigger(peewee.Model):
    ID = AutoField(primary_key=True)
    trigger_name = CharField(max_length=32, unique=True)
    date = DateTimeField(default=datetime.datetime.now)
    class Meta:
        table_name = "word_trigger"


