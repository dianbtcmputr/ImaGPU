from config import *
from utils import *

TOPMOST = RegisterKey("topmost", False)

class ParamItem(Frame):
    TYPE_COLOR = 0
    TYPE_FLOAT = 1
    TYPE_INT = 2
    TYPE_VEC2 = 3
    TYPE_VEC3 = 4
    TYPE_VEC4 = 5
    TYPE_IVEC2 = 6
    TYPE_IVEC3 = 7
    TYPE_IVEC4 = 8

    typeid2str = [LP("typename.color"),
                  LP("typename.float"),
                  LP("typename.int"),
                  LP("typename.vec2"),
                  LP("typename.vec3"),
                  LP("typename.vec4"),
                  LP("typename.ivec2"),
                  LP("typename.ivec3"),
                  LP("typename.ivec4")]
    typeid2code = ["vec4", "float", "int", "vec2", "vec3", "vec4", "ivec2", "ivec3", "ivec4"]

    def __init__(self, typeid: int, varname: str):
        Frame.__init__(self, ig.cstm_frm)
        self.value = None
        self.varname = varname
        ig.param_list.append(self)

        self.typeid = typeid
        self.type_name = ParamItem.typeid2str[typeid]

        bar = Frame(self)
        bar.grid(row=0, column=0, columnspan=8, sticky="ew")
        Label(bar, text=f"{self.varname}（{self.type_name}）").pack(side=LEFT, **PAD)
        Button(bar, text=LP("param.del"), command=self.delete).pack(side=RIGHT, **PAD)

        [   self.setupui_color, self.setupui_float,
            self.setupui_int, self.setupui_vec2,
            self.setupui_vec3, self.setupui_vec4,
            self.setupui_ivec2, self.setupui_ivec3,
            self.setupui_ivec4
        ][typeid]()
        
        Separator(self).grid(row=5, column=0, columnspan=8, sticky="ew", **PAD)

        self.pack(anchor="w", **PAD)

    def delete(self):
        ig.param_list.remove(self)
        self.grid_forget()
        self.value.clear()
        self.destroy()
        ig.update_param_types()

    def setupui_color(self):
        self._setupui_vecn(4, "rgba", 1.0)

    def setupui_float(self):
        self.value = [DoubleVar(value=0.0)]
        Spinbox(self, textvariable=self.value[0], from_=-65535.0,
            to=65535.0, increment=0.1, width=16).grid(row=1, column=0, sticky="ew", **PAD)
        self.grid_columnconfigure(1, weight=1)

    def setupui_int(self):
        self.value = [IntVar(value=0)]
        Spinbox(self, textvariable=self.value[0], from_=-65535,
            to=65535, increment=1, width=16).grid(row=1, column=0, sticky="ew", **PAD)
        self.grid_columnconfigure(1, weight=1)

    def _setupui_vecn(self, n: int, letters="xyzw", absval: float = 1.0):
        self.value = [DoubleVar(value=0.0) for _ in range(n)]
        for i, lett in enumerate(letters[:n]):
            Label(self, text=f"  {lett}:").grid(row=1, column=i * 2, **PAD)
            Spinbox(self, textvariable=self.value[i], from_=-absval,
                to=absval, increment=0.1, width=4).grid(row=1, column=i * 2 + 1, sticky="ew", **PAD)
        for i in range(n):
            self.grid_columnconfigure(i * 2 + 1, weight=1)
    
    def setupui_vec2(self):
        self._setupui_vecn(2)
    
    def setupui_vec3(self):
        self._setupui_vecn(3)
    
    def setupui_vec4(self):
        self._setupui_vecn(4)

    def _setupui_ivecn(self, n: int):
        self.value = [IntVar(value=0) for _ in range(n)]
        for i, lett in enumerate("xyzw"[:n]):
            Label(self, text=f"  {lett}:").grid(row=1, column=i * 2, **PAD)
            Spinbox(self, textvariable=self.value[i], from_=-65535,
                to=65535, increment=1, width=4).grid(row=1, column=i * 2 + 1, sticky="ew", **PAD)
        for i in range(n):
            self.grid_columnconfigure(i * 2 + 1, weight=1)
    
    def setupui_ivec2(self):
        self._setupui_ivecn(2)
    
    def setupui_ivec3(self):
        self._setupui_ivecn(3)
    
    def setupui_ivec4(self):
        self._setupui_ivecn(4)

class ParamTypeDialog(Toplevel):
    def __init__(self):
        Toplevel.__init__(self, ig.tk)
        self.title(LP("param.add"))
        self.resizable(False, False)
        self.transient(ig.tk)
        self.geometry(f"+{ig.tk.winfo_x()+150}+{ig.tk.winfo_y()+150}")
        Label(self, text=LP("param.name")).grid(row=0, column=0, sticky="w", **PAD)
        self.ety = Entry(self)
        self.ety.grid(row=0, column=1, sticky="ew", **PAD)
        Label(self, text=LP("param.type")).grid(row=1, column=0, sticky="w", **PAD)
        self.typev = IntVar(value=0)
        for i, tname in enumerate(ParamItem.typeid2str):
            Radiobutton(self, text=tname, variable=self.typev, value=i).grid(row=i+1, column=1, sticky="ew", **PAD)
        
        bbox = Frame(self)
        bbox.grid(row=10, column=0, columnspan=2, sticky="ew")
        Button(bbox, text=LP("dialog.cancel"), command=self.destroy, width=1).pack(side=LEFT, fill=X, expand=1, **PAD)
        Button(bbox, text=LP("dialog.ok"), command=self.ok, width=1).pack(side=LEFT, fill=X, expand=1, **PAD)

        self.selection = ("", -1)
        self.ety.focus_force()
    
    def ok(self):
        vname = self.ety.get().strip()
        if not vname:
            showerror(LP("dialog.error"), LP("param.error.no_name"))
            return
        res = glsl_name_check(vname)
        if isinstance(res, str):
            showerror(LP("dialog.error"), res)
            return
        elif vname in [x.varname for x in ig.param_list]:
            showerror(LP("dialog.error"), LP("glslname.duplicate", name=LP("glslname.name_univ")))
            return
        self.selection = (vname, self.typev.get())
        self.destroy()

class ImaGPU:
    def __init__(self, master: TWindow):
        self.tk = master
        self.tk.title("ImaGPU")
        self.tk.resizable(False, False)
        if TOPMOST:
            self.tk.attributes("-topmost", True)
        
        self.src_pil = None # 原图 PIL
        self.dst_pil = None # 结果图 PIL
        self.ref_pil = None # 参考图 PIL
        self.src_tex = None # OpenGL 纹理 ID
        self.dst_tex = None
        self.ref_tex = None
        self.img_width = 0
        self.img_height = 0

        self.sizer_pr = None
        self.pixer_pr = None

        self.src_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
        self.dst_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
        self.ref_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
        self.curr_view = self.src_view

        # 显示选择（0=原图，1=结果图）
        self.display_mode = IntVar(value=0)

        self.create_widgets()

        self.pwin = PWindow(resizable=True, style=PWindow.WINDOW_STYLE_BORDERLESS)
        
        self.pwin.event(self.on_draw)
        self.pwin.event(self.on_mouse_drag)
        self.pwin.event(self.on_mouse_scroll)

        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_BORDER = 0x00800000
        WS_THICKFRAME = 0x00040000
        current_style = user32.GetWindowLongW(self.pwin._hwnd, GWL_STYLE)
        new_style = current_style & ~(WS_CAPTION | WS_BORDER | WS_THICKFRAME)
        user32.SetWindowLongW(self.pwin._hwnd, GWL_STYLE, new_style)
        
        GWL_EXSTYLE = -20
        WS_EX_NOACTIVATE = 0x08000000
        current_ex_style = user32.GetWindowLongW(self.pwin._hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self.pwin._hwnd, GWL_EXSTYLE, current_ex_style | WS_EX_NOACTIVATE)

        user32.SetParent(self.pwin._hwnd, self.rightfrm.winfo_id())

        WM_MOUSEACTIVATE = 0x0021
        MA_NOACTIVATE = 3
        
        WNDPROC = WINFUNCTYPE(c_int, c_void_p, c_int, c_void_p, c_void_p)
        
        original_wndproc = user32.GetWindowLongPtrW(self.pwin._hwnd, -4)
        if original_wndproc == 0:
            original_wndproc = user32.GetWindowLongW(self.pwin._hwnd, -4)
        
        def new_wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_MOUSEACTIVATE:
                return MA_NOACTIVATE
            return user32.CallWindowProcW(original_wndproc, hwnd, msg, wparam, lparam)
        
        self.wndproc_callback = WNDPROC(new_wndproc)
        user32.SetWindowLongPtrW(self.pwin._hwnd, -4, cast(self.wndproc_callback, c_void_p).value)

        vaos = (GLuint * 1)()
        glGenVertexArrays(1, vaos)
        glBindVertexArray(vaos[0])

        self.prev_prog = ShaderProgram(
            Shader(PREVIEW_VERT_SOURCE, "vertex"),
            Shader(PREVIEW_FRAG_SOURCE, "fragment")
        )

        bufs = (GLuint * 1)()
        glGenBuffers(1, bufs)
        self.sizer_buf = bufs[0]

    def update_param_types(self):
        param_types = {p.varname: p.typeid2code[p.typeid] for p in self.param_list}
        if hasattr(self, 'sizer_highlighter'):
            self.sizer_highlighter.set_param_types(param_types)
            self.pixer_highlighter.set_param_types(param_types)

    def create_widgets(self):
        self.leftfrm = Frame(self.tk)

        main_f = Frame(self.leftfrm)
        main_f.pack(fill=BOTH, expand=True)

        nb = Notebook(main_f)
        nb.pack(fill=BOTH, expand=True, **PAD)

        # 参数着色器选项卡
        param_f = Frame(nb)
        nb.add(param_f, text=LP("shader.param"))

        self.src_boundary = StringVar(value="Clamp")
        self.ref_boundary = StringVar(value="Clamp")

        bound_f = Frame(param_f)
        bound_f.pack(fill=X)

        Label(bound_f, text=LP("boundary.src")).grid(row=0, column=0, sticky="e", **PAD)
        Radiobutton(bound_f, text=LP("boundary.clamp"), variable=self.src_boundary, value="Clamp").grid(row=0, column=1, **PAD)
        Radiobutton(bound_f, text=LP("boundary.repeat"), variable=self.src_boundary, value="Repeat").grid(row=0, column=2, **PAD)
        Radiobutton(bound_f, text=LP("boundary.mirror"), variable=self.src_boundary, value="Mirror").grid(row=0, column=3, **PAD)

        Label(bound_f, text=LP("boundary.ref")).grid(row=1, column=0, sticky="e", **PAD)
        Radiobutton(bound_f, text=LP("boundary.clamp"), variable=self.ref_boundary, value="Clamp").grid(row=1, column=1, **PAD)
        Radiobutton(bound_f, text=LP("boundary.repeat"), variable=self.ref_boundary, value="Repeat").grid(row=1, column=2, **PAD)
        Radiobutton(bound_f, text=LP("boundary.mirror"), variable=self.ref_boundary, value="Mirror").grid(row=1, column=3, **PAD)

        # bound_f.grid_columnconfigure(1, weight=1)
        # bound_f.grid_columnconfigure(2, weight=1)
        # bound_f.grid_columnconfigure(3, weight=1)

        outer_f = Frame(param_f, borderwidth=2, relief="groove")
        self.cstm_frm = ScrolledFrame(outer_f)
        self.cstm_frm.pack(fill=BOTH, expand=True)
        outer_f.pack(fill=BOTH, expand=True, **PAD)

        self.param_list: "list[ParamItem]" = []

        Button(param_f, text=LP("param.add"), command=self.add_param).pack(side=LEFT, **PAD)

        # Sizer 选项卡
        sizer_frame = Frame(nb)
        nb.add(sizer_frame, text=LP("shader.sizer"))
        self.siz_t_f = Frame(sizer_frame)
        self.sizer_text = Text(self.siz_t_f, width=60, height=25, font=("Consolas", 10))
        self.sizer_highlighter = GLSLHighlighter(self.sizer_text)
        self.sizer_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.sizer_text.insert(END, "ig_OutSize = ig_InSize;")  # 默认
        vbar = Scrollbar(self.siz_t_f, orient=VERTICAL, command=self.sizer_text.yview)
        vbar.pack(side=LEFT, fill=Y)
        self.sizer_text.config(yscrollcommand=vbar.set)
        self.siz_t_f.pack(fill=BOTH, expand=True, **PAD)

        # Pixer 选项卡
        pixer_frame = Frame(nb)
        nb.add(pixer_frame, text=LP("shader.pixer"))
        self.pix_t_f = Frame(pixer_frame)
        self.pixer_text = Text(self.pix_t_f, width=60, height=25, font=("Consolas", 10))
        self.pixer_highlighter = GLSLHighlighter(self.pixer_text)
        self.pixer_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.pixer_text.insert(END, "ig_PixColor = igGetPix(ig_Position);")  # 默认
        vbar = Scrollbar(self.pix_t_f, orient=VERTICAL, command=self.pixer_text.yview)
        vbar.pack(side=LEFT, fill=Y)
        self.pixer_text.config(yscrollcommand=vbar.set)
        self.pix_t_f.pack(fill=BOTH, expand=True, **PAD)

        # 全局设置选项卡
        cnf_frame = Frame(nb)
        nb.add(cnf_frame, text=LP("config.title"))
        self.cnf_scf = ScrolledFrame(cnf_frame)
        setupui(self.cnf_scf)
        self.cnf_scf.pack(fill=BOTH, expand=True, **PAD)

        # 控制栏
        ctrl_f = Frame(main_f)
        ctrl_f.pack(fill=X)

        Button(ctrl_f, text=LP("ctrl.load_src"), command=self.load_image).grid(row=0, column=0, sticky=EW, **PAD)
        Button(ctrl_f, text=LP("ctrl.load_ref"), command=self.load_ref).grid(row=0, column=1, sticky=EW, **PAD)
        self.applybtn = Button(ctrl_f, text=LP("ctrl.apply"), command=self.apply_shader)
        self.applybtn.grid(row=0, column=2, sticky=EW, **PAD)
        self.retbtn = Button(ctrl_f, text=LP("ctrl.confirm_res"), command=self.ret_as_src, state="disabled")
        self.retbtn.grid(row=0, column=3, sticky=EW, **PAD)
        Button(ctrl_f, text=LP("ctrl.export_img"), command=self.export_result).grid(row=0, column=4, sticky=EW, **PAD)

        Button(ctrl_f, text=LP("ctrl.import_shader"), command=self.import_shaders).grid(row=1, column=0, sticky=EW, **PAD)
        Button(ctrl_f, text=LP("ctrl.export_shader"), command=self.export_shaders).grid(row=1, column=1, sticky=EW, **PAD)
        Button(ctrl_f, text=LP("ctrl.reset_view"), command=self.reset_view).grid(row=1, column=2, sticky=EW, **PAD)

        rdbbox = Frame(ctrl_f)
        rdbbox.grid(row=1, column=3, columnspan=3, sticky=EW, **PAD)
        Radiobutton(rdbbox, text=LP("ctrl.show_src"), variable=self.display_mode, value=0).grid(row=0, column=0, sticky=EW, **PAD)
        Radiobutton(rdbbox, text=LP("ctrl.show_ref"), variable=self.display_mode, value=2).grid(row=0, column=1, sticky=EW, **PAD)
        Radiobutton(rdbbox, text=LP("ctrl.show_result"), variable=self.display_mode, value=1).grid(row=0, column=2, sticky=EW, **PAD)
        rdbbox.grid_columnconfigure(0, weight=1, uniform="rd")
        rdbbox.grid_columnconfigure(1, weight=1, uniform="rd")
        rdbbox.grid_columnconfigure(2, weight=1, uniform="rd")

        ctrl_f.grid_columnconfigure(0, weight=1, uniform="ctrl")
        ctrl_f.grid_columnconfigure(1, weight=1, uniform="ctrl")
        ctrl_f.grid_columnconfigure(2, weight=1, uniform="ctrl")
        ctrl_f.grid_columnconfigure(3, weight=1, uniform="ctrl")
        ctrl_f.grid_columnconfigure(4, weight=1, uniform="ctrl")

        self.status = Label(main_f, text=LP("status.ready"), bootstyle="info")
        self.status.pack(fill=X, **PAD)
        
        self.leftfrm.pack(side=LEFT, fill=Y)

        self.rightfrm = Frame(self.tk, width=1000)
        self.rightfrm.pack(side=LEFT, fill=BOTH, expand=True, pady=PAD["pady"], padx=(0, PAD["padx"]))

    def align_windows(self, w=-1, h=-1):
        self.tk.update_idletasks()
        w = w if w > 0 else self.rightfrm.winfo_width()
        h = h if h > 0 else self.rightfrm.winfo_height()
        if w <= 1 or h <= 1:
            print(w, h)

        SWP_NOZORDER        = 0x0004
        SWP_NOMOVE          = 0x0002
        SWP_NOACTIVATE      = 0x0010
        #SWP_ASYNCWINDOWPOS  = 0x4000

        self.pwin._width = w
        self.pwin._height = h
        glViewport(0, 0, w, h)

        user32.SetWindowPos(
            self.pwin._hwnd, 0, 0, 0, w, h,
            SWP_NOZORDER | SWP_NOMOVE | SWP_NOACTIVATE,
        )

    def ret_as_src(self):
        if self.dst_tex is None:
            return

        glBindTexture(GL_TEXTURE_2D, self.dst_tex)
        out_w = GLint()
        out_h = GLint()
        glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, out_w)
        glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT, out_h)
        w, h = out_w.value, out_h.value

        self._del_tex(self.src_tex)
        self.src_tex = self._create_empty_tex(w, h)

        glCopyImageSubData(
            self.dst_tex, GL_TEXTURE_2D, 0, 0, 0, 0,
            self.src_tex, GL_TEXTURE_2D, 0, 0, 0, 0,
            w, h, 1)

        self.src_pil = self._tex_to_pil(self.src_tex, w, h)
        self.img_width, self.img_height = w, h

        self.src_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
        self.dst_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
        self.ref_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}

        self.curr_view = self.src_view
        self.display_mode.set(0)

        self.retbtn.config(state="disabled")
        self.status.config(text=LP("status.confirmed"))

    def load_image(self):
        path = askopenfilename(filetypes=[(LP("filedlg.imagetype"), "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if not path:
            return
        try:
            self.src_pil = Image.open(path).convert("RGBA")
            self.img_width, self.img_height = self.src_pil.size
            self.dst_pil = None
            self._del_tex(self.src_tex)
            self._del_tex(self.dst_tex)
            self.src_tex = self._pil_to_tex(self.src_pil)
            self.dst_tex = self._create_empty_tex(self.img_width, self.img_height)
            # 重置视图
            self.src_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
            self.dst_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
            self.ref_view = {'scale': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}
            self.curr_view = self.src_view
            self.display_mode.set(0)
            self.status.config(text=f"{LP('status.src_loaded')}: {self.img_width}x{self.img_height}")
        except Exception as e:
            showerror(LP("dialog.error"), f"{LP('dialog.error.load_src')}: {e}")

    def load_ref(self):
        path = askopenfilename(filetypes=[(LP("filedlg.imagetype"), "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if not path:
            return
        try:
            self.ref_pil = Image.open(path).convert("RGBA")
            self._del_tex(self.ref_tex)
            self.ref_tex = self._pil_to_tex(self.ref_pil)
            self.status.config(text=f"{LP('status.ref_loaded')}: {self.ref_pil.width}x{self.ref_pil.height}")
            self.display_mode.set(2)
            self.curr_view = self.ref_view
        except Exception as e:
            showerror(LP("dialog.error"), f"{LP('dialog.error.load_ref')}: {e}")

    def _pil_to_tex(self, pil_img: Image.Image):
        img2 = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
        data = img2.tobytes()
        w, h = img2.size
        texs = (GLuint * 1)()
        glGenTextures(1, texs)
        glBindTexture(GL_TEXTURE_2D, texs[0])
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        return texs[0]

    def _create_empty_tex(self, w, h):
        texs = (GLuint * 1)()
        glGenTextures(1, texs)
        glBindTexture(GL_TEXTURE_2D, texs[0])
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, w, h)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        return texs[0]

    def _del_tex(self, tex):
        if tex is not None:
            glDeleteTextures(1, (GLuint * 1)(tex))

    def _tex_to_pil(self, tex, w, h):
        glBindTexture(GL_TEXTURE_2D, tex)
        data = (GLubyte * (w * h * 4))()
        glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return Image.frombytes("RGBA", (w, h), data).transpose(Image.FLIP_TOP_BOTTOM)

    def _try_comp_shader(self, source):
        try:
            return ShaderProgram(Shader(source, "compute"))
        except BaseException as e:
            return str(e)

    def _get_boundary_code(self, mode, coord_var="xy", texname="_inimg"):
        """返回对坐标进行边界处理的代码片段（作用于 ivec2 变量 'xy'，返回 ivec2）"""
        if mode == "Clamp":
            return f"    return imageLoad({texname}, clamp({coord_var}, ivec2(0), ig_InSize - 1));"
        elif mode == "Repeat":
            return f"    return imageLoad({texname}, {coord_var} % ig_InSize);"
        elif mode == "Mirror":
            return f"""
    ivec2 size = ig_InSize;
    ivec2 coord = {coord_var} % (2 * size);
    ivec2 mirror = ivec2(
        coord.x < size.x ? coord.x : 2 * size.x - coord.x - 1,
        coord.y < size.y ? coord.y : 2 * size.y - coord.y - 1
    );
    return imageLoad({texname}, mirror);"""
        else:
            return f"    return imageLoad({texname}, clamp({coord_var}, ivec2(0), ig_InSize - 1));"

    def apply_shader(self):
        if self.src_tex is None:
            showinfo(LP("dialog.info"), LP("dialog.info.load_src"))
            return

        self.applybtn.config(state="disabled")
        sizer_code = self.sizer_text.get("1.0", END).strip()
        pixer_code = self.pixer_text.get("1.0", END).strip()

        src_mode = self.src_boundary.get()
        ref_mode = self.ref_boundary.get()
        src_impl = self._get_boundary_code(src_mode, "xy", "_inimg")
        ref_impl = self._get_boundary_code(ref_mode, "xy", "_refimg")

        param_struct = self.build_param_struct()

        sizer_full = SIZER_TEMPLATE.replace("###", sizer_code).replace("#PARAM_STRUCT#", param_struct)

        pixer_full = PIXER_TEMPLATE.replace("#SRC_BOUNDARY_IMPL#", src_impl)
        pixer_full = pixer_full.replace("#REF_BOUNDARY_IMPL#", ref_impl)
        pixer_full = pixer_full.replace("###", pixer_code).replace("#PARAM_STRUCT#", param_struct)

        self.status.config(text=LP("status.compiling"))
        self.leftfrm.update()

        sizer_err = self._try_comp_shader(sizer_full)
        if isinstance(sizer_err, str):
            ShaderErrorDialog.showerror(tk, LP("status.compile_failed"),  f"{LP('dialog.error.sizer_compiling')}:\n{sizer_err}")
            self.status.config(text=LP("status.compile_failed"))
            self.applybtn.config(state="normal")
            return
        
        pixer_err = self._try_comp_shader(pixer_full)
        if isinstance(pixer_err, str):
            ShaderErrorDialog.showerror(tk, LP("status.compile_failed"),  f"{LP('dialog.error.pixer_compiling')}:\n{pixer_err}")
            self.status.config(text=LP("status.compile_failed"))
            self.applybtn.config(state="normal")
            return

        self.sizer_pr = sizer_err
        self.pixer_pr = pixer_err

        try:
            self.status.config(text=LP("status.processing"))
            self.leftfrm.update()
            self._process()
            self.status.config(text=LP("status.processed"))
            self.retbtn.config(state="normal")
        except Exception as e:
            showerror(LP("dialog.error"), f"{LP('status.process_failed')}:\n{e}。\n{LP('dialog.error.process_failed_desc')}")
            self.status.config(text=LP("status.process_failed"))
            self.retbtn.config(state="disabled")
        
        self.applybtn.config(state="normal")

    def _process(self):
        if self.src_tex is None:
            return

        self.sizer_pr.use()
        self.set_param_uniforms(self.sizer_pr)
        
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.sizer_buf)
        glBufferData(GL_SHADER_STORAGE_BUFFER, 8, None, GL_STATIC_READ)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, self.sizer_buf)
        try:
            self.sizer_pr["ig_InSize"] = (self.img_width, self.img_height)
        except:
            pass

        glDispatchCompute(1, 1, 1)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)

        arr = (GLint * 2)()
        glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, 8, arr)
        out_w, out_h = arr[0], arr[1]

        if out_w <= 0 or out_h <= 0:
            raise ValueError(LP("dialog.error.sizer_output"))

        self._del_tex(self.dst_tex)
        self.dst_tex = self._create_empty_tex(out_w, out_h)

        self.pixer_pr.use()
        self.set_param_uniforms(self.pixer_pr)

        glBindImageTexture(0, self.src_tex, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA8)
        glBindImageTexture(1, self.dst_tex, 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA8)
        if self.ref_tex is not None:
            glBindImageTexture(2, self.ref_tex, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA8)
            dummy = None
        else:
            dummy = self._create_empty_tex(1, 1)
            glBindImageTexture(2, dummy, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA8)

        glDispatchCompute(out_w, out_h, 1)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)

        self.dst_pil = self._tex_to_pil(self.dst_tex, out_w, out_h)
        self.display_mode.set(1)
        self.curr_view = self.dst_view

        self._del_tex(dummy)

    def on_draw(self):
        #self.tk.update()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        tex_to_show = None
        if self.display_mode.get() == 0:
            self.curr_view = self.src_view
            tex_to_show = self.src_tex
            if self.src_pil:
                disp_w, disp_h = self.src_pil.size
            else:
                return
        elif self.display_mode.get() == 1:
            self.curr_view = self.dst_view
            tex_to_show = self.dst_tex
            if self.dst_pil:
                disp_w, disp_h = self.dst_pil.size
            else:
                return
        
        elif self.display_mode.get() == 2:
            self.curr_view = self.ref_view
            tex_to_show = self.ref_tex
            if self.ref_pil:
                disp_w, disp_h = self.ref_pil.size
            else:
                return

        if tex_to_show is None or disp_w <= 0 or disp_h <= 0:
            return

        w, h = self.pwin.width, self.pwin.height
        if w == 0 or h == 0:
            return

        self.prev_prog.use()
        self.prev_prog["winSize"] = (float(w), float(h))
        self.prev_prog["imgSize"] = (float(disp_w), float(disp_h))
        self.prev_prog["imgSize_i"] = (disp_w, disp_h)
        self.prev_prog["scale"] = self.curr_view['scale']
        self.prev_prog["pan"] = (self.curr_view['pan_x'], self.curr_view['pan_y'])
        glBindImageTexture(0, tex_to_show, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA8)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 5)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if button == mouse.LEFT:
            self.curr_view['pan_x'] += dx
            self.curr_view['pan_y'] -= dy
        elif button == mouse.RIGHT:
            self.curr_view['pan_x'] += dx * 3
            self.curr_view['pan_y'] -= dy * 3

    def on_mouse_scroll(self, x, y, _, scroll_y):
        old = self.curr_view['scale']
        if scroll_y > 0:
            new = old * 1.1
        else:
            new = old / 1.1
        if new < 0.5:
            new = 0.5
        ratio = new / old
        self.curr_view['scale'] = new
        self.curr_view['pan_x'] *= ratio
        self.curr_view['pan_y'] *= ratio

    def reset_view(self):
        self.curr_view['scale'] = 1.0
        self.curr_view['pan_x'] = 0.0
        self.curr_view['pan_y'] = 0.0

    def export_result(self):
        if self.dst_pil is None:
            showinfo(LP("dialog.info"), LP("dialog.info.no_result"))
            return
        path = asksaveasfilename(defaultextension=".png",
                                 filetypes=[("PNG", "*.png")])
        if path:
            self.dst_pil.save(path)
            showinfo(LP("dialog.info"), f"{LP('dialog.info.exported_to')} {path}")

    def export_shaders(self):
        sizer_code = self.sizer_text.get("1.0", END).strip()
        pixer_code = self.pixer_text.get("1.0", END).strip()

        params = {}
        for p in self.param_list:
            params[p.varname] = [p.typeid, [x.get() for x in p.value]]

        data = {
            "sizer": sizer_code,
            "pixer": pixer_code,
            "params": params,
            "boundary": [self.src_boundary.get(), self.ref_boundary.get()]
        }
        path = asksaveasfilename(defaultextension=".imgpu",
                                 filetypes=[(LP("filedlg.shaders"), "*.imgpu")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                dump(data, f, indent=2)
            showinfo(LP("dialog.info"), f"{LP('dialog.info.exported_to')} {path}")

    def import_shaders(self):
        path = askopenfilename(filetypes=[(LP("filedlg.shaders"), "*.imgpu")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = load(f)
            if "sizer" not in data or "pixer" not in data or "params" not in data or "boundary" not in data:
                showerror(LP("dialog.error"), LP("dialog.error.invalid_shader_file"))
                return
            
            self.sizer_text.delete("1.0", END)
            self.sizer_text.insert("1.0", data["sizer"])
            self.pixer_text.delete("1.0", END)
            self.pixer_text.insert("1.0", data["pixer"])
            
            [x.delete() for x in self.param_list]

            for pname, p in data["params"].items():
                c = ParamItem(p[0], pname)
                for ind, v in enumerate(c.value):
                    v.set(p[1][ind])

            self.src_boundary.set(data["boundary"][0])
            self.ref_boundary.set(data["boundary"][1])
            self.update_param_types()

            showinfo(LP("dialog.info"), LP("dialog.info.shader_imported"))
        except Exception as e:
            showerror(LP("dialog.error"), f"{LP('dialog.error.shader_import')}: {e}")

    def add_param(self):
        dialog = ParamTypeDialog()
        dialog.wait_window()
        vname, vtype = dialog.selection
        if vname == "":
            return
        ParamItem(vtype, vname)
        self.update_param_types()

    def build_param_struct(self):
        res = "struct _Params { bool _placeholder_; "
        for p in self.param_list:
            res += f"{p.typeid2code[p.typeid]} {p.varname}; "
        res += "};\n"
        return res
    
    def set_param_uniforms(self, prog):
        for p in self.param_list:
            if len(p.value) == 1:
                try:
                    prog[f"ig_Params.{p.varname}"] = p.value[0].get()
                except:
                    pass
            else:
                try:
                    prog[f"ig_Params.{p.varname}"] = [x.get() for x in p.value]
                except:
                    pass

if __name__ == "__main__":
    tk = TWindow()
    ig = ImaGPU(tk)
    tk.protocol("WM_DELETE_WINDOW", tk.quit)
    tk.focus_force()

    def tick():
        ig.pwin.dispatch_events()
        ig.pwin.dispatch_event('on_draw')
        ig.pwin.flip()
        ig.align_windows()
        tk.after(10, tick)

    tick()
    tk.mainloop()
    InjectFile()