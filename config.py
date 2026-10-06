from json import loads, dumps
from os.path import isfile
from tkinter import X, LEFT
from ttkbootstrap import BooleanVar, Button, Checkbutton, Frame, IntVar, Label, Radiobutton, Scale, Separator, StringVar, Toplevel
from ttkbootstrap.scrolled import ScrolledFrame

if isfile("config.json"):
    with open("config.json", encoding="utf-8") as f:
        _cnf = loads(f.read())
else:
    _cnf = {}
    with open("config.json", "w", encoding="utf-8") as f:
        f.write(dumps(_cnf))

def RegisterKey(key, d_val):
    if key not in _cnf:
        _cnf[key] = d_val
        return d_val
    else:
        return _cnf[key]

def SetValue(key, value):
    _cnf[key] = value

def QueryValue(key):
    return _cnf[key]

def InjectFile():
    with open("config.json", "w", encoding="utf-8") as f:
        f.write(dumps(_cnf))

_pad = RegisterKey("padding", 8)
PAD = dict(padx=_pad, pady=_pad)
del _pad

# Config items. The label of item 'key' is LP(f"config.kname.{key}")
CONFIGITEMS: "list[dict[str, str]]" = [
    {"key": "language",
     "type": "choice",
     "option_ids": ...,
     "option_names": ...
    },

    {"key": "topmost",
     "type": "checkbox"
    },

    {"key": "padding",
     "type": "int_slider",
     "range": (0, 20),
     "step": 4
    }
]

def setupui(scf: ScrolledFrame):
    # This cannot be imported at first.
    from langlib import LP, ALL_LANG
    Label(scf, text=LP("config.prompt")).pack(fill="x", **PAD)

    if CONFIGITEMS[0]["option_ids"] == ...:
        CONFIGITEMS[0]["option_ids"] = list(ALL_LANG.keys())
        CONFIGITEMS[0]["option_names"] = [ALL_LANG[lang].name for lang in ALL_LANG.keys()]
    
    for item in CONFIGITEMS:
        key, typ = item["key"], item["type"]
        lbtext = LP(f"config.kname.{key}")
        frm = Frame(scf)
        if typ == "choice":
            oids = item["option_ids"]
            onames = item["option_names"]
            var = StringVar(value=QueryValue(key))
            Label(frm, text=lbtext).grid(row=0, column=0, **PAD)
            for i, (oid, oname) in enumerate(zip(oids, onames)):
                Radiobutton(frm, text=oname, value=oid, variable=var).grid(row=i, column=1, **PAD, sticky="w")
            var.trace_add("write", lambda *args, k=key, v=var: SetValue(k, v.get()))
        
        elif typ == "checkbox":
            var = BooleanVar(value=QueryValue(key))
            Checkbutton(frm, text=lbtext, variable=var).pack(side=LEFT, **PAD)
            var.trace_add("write", lambda *args, k=key, v=var: SetValue(k, v.get()))
        
        elif typ == "int_slider":
            Label(frm, text=lbtext).pack(side=LEFT, **PAD, anchor="w")
            var = IntVar(value=QueryValue(key))
            Scale(frm, from_=item["range"][0], to=item["range"][1], variable=var, length=100).pack(side=LEFT, **PAD)
            Label(frm, textvariable=var).pack(side=LEFT, **PAD)
            var.trace_add("write", lambda *args, k=key, v=var, minv=item["range"][0], ste=item["step"]:  [v.set((v.get() - minv)//ste * ste + minv), SetValue(k, v.get())])
        
        frm.pack(anchor="w")
        Separator(scf).pack(padx=(PAD["padx"], 400), pady=PAD["pady"], anchor="w", fill=X)
