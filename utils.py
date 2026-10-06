from re import DOTALL, MULTILINE, escape, finditer, compile
from ctypes import WINFUNCTYPE, c_int, c_void_p, cast, windll
from tkinter import BOTH, END, EW, LEFT, SINGLE, VERTICAL, X, Y, Listbox, RIGHT
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror, showinfo
from tkinter.simpledialog import askstring
from ttkbootstrap import (
    Combobox, DoubleVar, Entry, Scrollbar, Separator,
    Spinbox, Text, Toplevel, Window as TWindow,
    StringVar, Frame, Button, Label, Notebook,
    Radiobutton, IntVar, Menu)
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from pyglet.window import Window as PWindow, mouse
from pyglet.gl import *
from pyglet import app
from pyglet.graphics.shader import Shader, ShaderProgram
from PIL import Image
from json import dump, load
from strlib import *
from langlib import LP
from config import PAD

user32 = windll.user32

user32.GetWindowLongPtrW.argtypes = [c_void_p, c_int]
user32.GetWindowLongPtrW.restype = c_void_p
user32.SetWindowLongPtrW.argtypes = [c_void_p, c_int, c_void_p]
user32.SetWindowLongPtrW.restype = c_void_p
user32.CallWindowProcW.argtypes = [c_void_p, c_void_p, c_int, c_void_p, c_void_p]
user32.CallWindowProcW.restype = c_int

HL_COLORS = {"gl_types": "#007800",
             "gl_qualifiers": "#0051b3",
             "gl_flow": "#752c92",
             "functions": "#bebe00", # glsl 以及 imagpu 函数
             "variables": "#147eff",  # 各种变量，包括用户自定义和 imagpu 内置变量
             "comments": "#626262",
             "numbers": "#499D49",
}

class ShaderErrorDialog(Toplevel):
    def __init__(self, master: TWindow, title: str, message: str):
        Toplevel.__init__(self, master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.geometry(f"+{master.winfo_x()+50}+{master.winfo_y()+50}")
        frm = Frame(self)
        frm.pack(fill=BOTH, expand=True, **PAD)

        txt = Text(frm)
        txt.insert("end", message)
        txt.pack(side=LEFT, fill=BOTH, expand=True)
        txt.config(state="disabled")
        vbar = Scrollbar(frm, orient=VERTICAL, command=txt.yview)
        vbar.pack(side=LEFT, fill=Y)
        txt.config(yscrollcommand=vbar.set)
        Button(self, text=LP("dialog.ok"), command=self.destroy, width=10).pack(anchor="e", **PAD)
        self.update()
    
    @staticmethod
    def showerror(master, title: str, message: str):
        ShaderErrorDialog(master, title, message).wait_window()

class RenameDialog(Toplevel):
    def __init__(self, master: TWindow, ori_name: str, x: int, y: int):
        Toplevel.__init__(self, master)
        self.vname = ori_name
        self.error = None
        self.overrideredirect(True)
        self.geometry(f'+{x}+{y}')
        self.ety = Entry(self, width=10)
        self.ety.insert(0, ori_name)
        self.ety.pack()
        self.ety.focus_set()
        self.ety.bind('<Return>', lambda e: self.ok())
        self.bind("<FocusOut>", lambda e: self.destroy())
    
    def ok(self):
        nname = self.ety.get().strip()
        if not nname:
            self.destroy() # 直接返回原名称
        res = glsl_name_check(nname)
        if isinstance(res, str):
            self.error = res
            return
        self.vname = nname
        self.destroy()

class GLSLHighlighter:
    def __init__(self, text: Text):
        self.text = text
        self._setup_tags()
        self._var_cache = {}      # 缓存 {变量名: 类型}
        self._after_id = None     # 防抖定时器
        self._tooltip = None      # tooltip 窗口
        self._tip_after_id = None # 隐藏 tooltip 的定时器
        self.param_types = {}     # 参数着色器的参数

        self.text.bind('<FocusIn>', self._schedule_hl)
        self.text.bind('<Motion>', self._on_motion)
        self.text.bind('<Leave>', self._hide_tooltip)
        # self.text.bind('<KeyRelease>', self._on_key_rel)
        self.text.bind('<KeyRelease>', self._schedule_hl)
        self.text.bind('<F2>', self._on_rename)

        self._compl_win = None
        self._compl_lb = None
        self._compl_candd = []
        self._compl_prfx = ""
        self._compl_start = ""
        self._compl_mode = None
        self._compl_after_id = None

    def _is_in_comment(self, index):
        if not hasattr(self, '_comment_regions'):
            return False

        line, col = index.split('.')
        line = int(line)
        col = int(col)

        prev_text = self.text.get(f'1.0', f'{line}.0')
        pos = len(prev_text) + col
        for s, e in self._comment_regions:
            if s <= pos < e:
                return True
        return False

    def _on_rename(self, event):
        cursor = self.text.index('insert')
        start, end, word = self._get_word_span(cursor)
        if not word:
            return

        if self._is_in_comment(cursor):
            return

        if word not in self._var_cache:
            return
        if word in imgpu_vars:
            return

        line, col = cursor.split('.')
        line = int(line)
        line_text = self.text.get(f'{line}.0', f'{line}.end')
        
        if start >= 10 and line_text[start-10:start] == "ig_Params.":
            return
        
        word_start_index = f'{line}.{start}'
        bbox = self.text.bbox(word_start_index)
        if bbox:
            x, y, width, height = bbox
            root_x = self.text.winfo_rootx() + x
            root_y = self.text.winfo_rooty() + y
        else:
            root_x = self.text.winfo_rootx() + 10
            root_y = self.text.winfo_rooty() + 10
        
        dialog = RenameDialog(self.text, word, root_x, root_y - 40)
        dialog.wait_window()
        new_name = dialog.vname
        error = dialog.error
        if error:
            showerror(LP("dialog.error"), error)
            return

        code = self.text.get('1.0', END)
        pattern = compile(r'\b' + escape(word) + r'\b')
        comment_regions = []
        for m in finditer(r'/\*.*?\*/', code, DOTALL):
            comment_regions.append((m.start(), m.end()))
        for m in finditer(r'//.*?$', code, MULTILINE):
            comment_regions.append((m.start(), m.end()))

        def is_in_comment_pos(pos):
            return any(s <= pos < e for s, e in comment_regions)

        replacements = []
        for m in pattern.finditer(code):
            pos = m.start()
            if not is_in_comment_pos(pos):
                replacements.append((m.start(), m.end()))

        for s, e in reversed(replacements):
            self.text.delete(f'1.0+{s}c', f'1.0+{e}c')
            self.text.insert(f'1.0+{s}c', new_name)

        old_type = self._var_cache.pop(word)
        self._var_cache[new_name] = old_type

        self.highlight()

    def set_param_types(self, param_types: dict):
        """由 ImaGPU 调用，更新参数类型并重新高亮"""
        self.param_types = param_types.copy()
        self.highlight()

    def _setup_tags(self):
        for tag, color in HL_COLORS.items():
            self.text.tag_delete(tag)
            self.text.tag_config(tag, foreground=color)

    def _schedule_hl(self, event=None):
        if self._after_id:
            self.text.after_cancel(self._after_id)
        self._after_id = self.text.after(30, self.highlight)

    def highlight(self):
        self._comment_regions = []
        self._after_id = None
        
        for tag in HL_COLORS.keys():
            self.text.tag_remove(tag, '1.0', END)
        self._var_cache.clear()
        self._var_cache.update({'ig_InSize': 'ivec2', 'ig_OutSize': 'ivec2',
                                'ig_Position': 'ivec2', 'ig_PixColor': 'vec4'})

        code = self.text.get('1.0', END)
        if not code.strip():
            return

        comment_regions = []
        # 多行注释
        for m in finditer(r'/\*.*?\*/', code, DOTALL):
            comment_regions.append((m.start(), m.end()))
        # 单行注释
        for m in finditer(r'//.*?$', code, MULTILINE):
            comment_regions.append((m.start(), m.end()))

        def is_in_comment(pos):
            return any(s <= pos < e for s, e in comment_regions)

        # ---- 2. 解析用户自定义变量声明（仅限 gl_types） ----
        type_pattern = '|'.join(escape(t) for t in gl_types)
        decl_re = compile(r'\b(' + type_pattern + r')\s+([a-zA-Z_][a-zA-Z0-9_]*)\b')
        for m in decl_re.finditer(code):
            var_start, var_end = m.span(2)
            if not is_in_comment(var_start):
                var_name = m.group(2)
                var_type = m.group(1)
                self._var_cache[var_name] = var_type
        
        # 解析参数着色器的参数
        param_match_pattern = r'ig_Params\.([a-zA-Z_][a-zA-Z0-9_]*)'
        for m in finditer(param_match_pattern, code):
            if not is_in_comment(m.start()):
                member_name = m.group(1)
                if member_name in self.param_types:
                    # 将成员名加入 _var_cache，键为完整的 "ig_Params.xxx"
                    full_name = f"ig_Params.{member_name}"
                    self._var_cache[full_name] = self.param_types[member_name]

        # ---- 3. 应用高亮标签（注释之外的区域） ----
        def build_pattern(words):
            return r'(?<![.])\b(' + '|'.join(escape(w) for w in words) + r')\b'

        # 3.1 关键字（类型、限定符、流程控制）
        self._apply_pattern(build_pattern(gl_types), 'gl_types', is_in_comment, code)
        self._apply_pattern(build_pattern(gl_qualifiers), 'gl_qualifiers', is_in_comment, code)
        self._apply_pattern(build_pattern(gl_flow), 'gl_flow', is_in_comment, code)

        # 3.2 函数（内置函数 + ImaGPU 自定义函数）
        funcs = gl_builtins | imgpu_func
        self._apply_pattern(build_pattern(funcs), 'functions', is_in_comment, code)

        # 3.3 变量（内置变量 + 缓存的用户自定义变量）
        vars_set = imgpu_vars | set(self._var_cache.keys())
        self._apply_pattern(build_pattern(vars_set), 'variables', is_in_comment, code)

        for m in finditer(r'ig_Params\.[a-zA-Z_][a-zA-Z0-9_]*', code):
            start, end = m.span()
            full = m.group()
            member = full.split('.')[-1]
            if not is_in_comment(start) and member in self.param_types:
                self.text.tag_add('variables', f'1.0+{start}c', f'1.0+{end}c')
        
        # 3.4 数字
        self._apply_pattern(r'\b\d+\.\d+([eE][+-]?\d+)?\b|\b\d+[eE][+-]?\d+\b|\b\d+\.\d+\b|\b\d+\b', 'numbers', is_in_comment, code)
        
        # 3.5 注释
        for s, e in comment_regions:
            self.text.tag_add('comments', f'1.0+{s}c', f'1.0+{e}c')
        
        self._comment_regions = comment_regions

    def _apply_pattern(self, pattern, tag, is_in_comment, code):
        for m in finditer(pattern, code):
            start, end = m.span()
            if not is_in_comment(start):
                self.text.tag_add(tag, f'1.0+{start}c', f'1.0+{end}c')

    # ---------- 鼠标悬停显示类型 ----------
    def _on_motion(self, event):
        index = self.text.index(f'@{event.x},{event.y}')
        char = self.text.get(index, f'{index}+1c')
        if not char or not (char.isalnum() or char == '_'):
            self._hide_tooltip()
            return

        start, end, word = self._get_word_span(index)
        if not word:
            self._hide_tooltip()
            return

        line, col = index.split('.')
        line = int(line)
        line_text = self.text.get(f'{line}.0', f'{line}.end')
        
        if start >= 10 and line_text[start-10:start] == "ig_Params." and word in self.param_types:
            self._show_tooltip(event.x_root, event.y_root, f"ig_Params.{word}\n    {LP('tooltip.type')}: {self.param_types[word]}")
            return

        if word in self._var_cache:
            self._show_tooltip(event.x_root, event.y_root, f"{word}\n    {LP('tooltip.type')}: {self._var_cache[word]}")
        elif word in (imgpu_func | gl_builtins):
            self._show_tooltip(event.x_root, event.y_root, LP(f"funchelp.{word}"))
        else:
            self._hide_tooltip()

    def _get_word_span(self, index):
        line, col = index.split('.')
        line = int(line)
        col = int(col)
        line_text = self.text.get(f'{line}.0', f'{line}.end')
        if col > len(line_text):
            return None, None, None

        # 向左扩展单词边界
        start = col
        while start > 0 and (line_text[start-1].isalnum() or line_text[start-1] == '_'):
            start -= 1
        # 向右扩展
        end = col
        while end < len(line_text) and (line_text[end].isalnum() or line_text[end] == '_'):
            end += 1

        if start < end:
            return start, end, line_text[start:end]
        return None, None, None
    
    def _get_word_at_index(self, index):
        line, col = index.split('.')
        line = int(line)
        col = int(col)
        line_text = self.text.get(f'{line}.0', f'{line}.end')
        if col > len(line_text):
            return None
        
        start = col
        while start > 0 and (line_text[start-1].isalnum() or line_text[start-1] == '_'):
            start -= 1
        end = col
        while end < len(line_text) and (line_text[end].isalnum() or line_text[end] == '_'):
            end += 1
        if start < end:
            return line_text[start:end]
        return None

    def _show_tooltip(self, x, y, text):
        if self._tooltip is None:
            self._tooltip = Toplevel(self.text)
            #self._tooltip.transient(self.text)
            self._tooltip.attributes('-topmost', True)
            self._tooltip.overrideredirect(True)
            self._tooltip.geometry(f'+{x}+{y+20}')
            label = Label(self._tooltip, text=text, background='#ffffe0',
                          relief='solid', borderwidth=1, font=('Consolas', 10))
            label.pack()
        else:
            self._tooltip.geometry(f'+{x}+{y+20}')
            self._tooltip.children['!label'].config(text=text)
        self._tooltip.deiconify()
        
        if self._tip_after_id:
            self.text.after_cancel(self._tip_after_id)

    def _hide_tooltip(self, event=None):
        if self._tooltip:
            self._tooltip.withdraw()
        if self._tip_after_id:
            self.text.after_cancel(self._tip_after_id)
