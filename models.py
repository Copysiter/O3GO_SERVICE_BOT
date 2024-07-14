from datetime import datetime
from pony.orm import *


db = Database()


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    ext_id = Required(int, size=64, unique=True)
    username = Optional(str, nullable=True)
    first_name = Optional(str, nullable=True)
    last_name = Optional(str, nullable=True)
    is_active = Required(bool)
    is_superuser = Required(bool)