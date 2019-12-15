import os
import toml

if os.path.isfile("config/config.toml"):
    with open("config/config.toml", mode="r", encoding="utf-8") as cfs:
        config = toml.load(cfs)
