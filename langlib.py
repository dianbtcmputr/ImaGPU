from json import loads
from os import listdir
from config import *

CURR_LANG = RegisterKey("language", "en_us")

class LangPack:
    def __init__(self, lang: str):
        self.id_ = lang
        with open(f"langpacks\\{lang}.json", encoding="utf-8") as f:
            data = loads(f.read())
        
        self.avail = True
        if not isinstance(data, dict):
            self.avail = False
        elif self.id_ != data["id"]:
            self.avail = False
        self.name = data["name"]
        self.kvdict = data["data"]
        if not isinstance(self.kvdict, dict):
            self.avail = False
    
    def get(self, key: str, **kw) -> str:
        if key in self.kvdict:
            return self.kvdict[key].format(**kw)
        else:
            return f"<{key}>"

    def __call__(self, key: str, **kw) -> str:
        return self.get(key, **kw)

ALL_LANG: "dict[str, LangPack]" = {}
for lp_id in listdir("langpacks"):
    if lp_id.endswith(".json"):
        id_ = lp_id[:-5]
        lp = LangPack(id_)
        if lp.avail:
            ALL_LANG[id_] = lp

if not ALL_LANG:
    raise ValueError("No available language pack found.")

if CURR_LANG in ALL_LANG:
    LP = ALL_LANG[CURR_LANG]
else:
    SetValue("language", list(ALL_LANG.keys())[0])
    LP = ALL_LANG[QueryValue("language")]
