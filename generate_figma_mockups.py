from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUT = Path("figma_mockups")
OUT.mkdir(exist_ok=True)

C = {
    "bg": "#F3F8F8",
    "panel": "#FFFFFF",
    "text": "#17343A",
    "muted": "#6B7C80",
    "line": "#DDE8E8",
    "primary": "#137C7A",
    "dark": "#0F2F35",
    "cyan": "#E7F6F5",
    "green": "#E8F7EF",
    "red": "#FDECEC",
    "yellow": "#FFF5D9",
    "purple": "#F0EDFF",
    "gray": "#ECEFF1",
    "danger": "#DC4C4C",
}

FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]
FONT_PATH = next((p for p in FONT_PATHS if Path(p).exists()), FONT_PATHS[-1])


def font(size, bold=False):
    return ImageFont.truetype(FONT_PATH, size)


def rounded(draw, xy, fill, radius=10, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, s, size=16, fill=None, anchor=None, align="left", box=None):
    fill = fill or C["text"]
    f = font(size)
    if box:
        x, y, w, h = box
        lines = s.split("\n")
        line_h = int(size * 1.35)
        start_y = y + max(0, (h - line_h * len(lines)) // 2)
        for i, line in enumerate(lines):
            if align == "center":
                bbox = draw.textbbox((0, 0), line, font=f)
                tx = x + (w - (bbox[2] - bbox[0])) / 2
            elif align == "right":
                bbox = draw.textbbox((0, 0), line, font=f)
                tx = x + w - (bbox[2] - bbox[0])
            else:
                tx = x
            draw.text((tx, start_y + i * line_h), line, font=f, fill=fill)
        return
    draw.text(xy, s, font=f, fill=fill, anchor=anchor)


def chip(draw, x, y, w, label, fg=None, bg=None):
    rounded(draw, (x, y, x + w, y + 26), bg or C["cyan"], 13)
    text(draw, (x, y), label, 13, fg or C["primary"], box=(x, y, w, 26), align="center")


def button(draw, x, y, w, h, label, kind="primary"):
    fill = C["primary"] if kind == "primary" else C["panel"]
    outline = None if kind == "primary" else C["line"]
    rounded(draw, (x, y, x + w, y + h), fill, 8, outline)
    text(draw, (x, y), label, 15, "#FFFFFF" if kind == "primary" else C["text"], box=(x, y, w, h), align="center")


def card(draw, x, y, w, h, r=10):
    rounded(draw, (x + 2, y + 8, x + w + 2, y + h + 8), "#D9E8E8", r)
    rounded(draw, (x, y, x + w, y + h), C["panel"], r)


def input_box(draw, x, y, w, label):
    text(draw, (x, y), label, 14, C["text"])
    rounded(draw, (x, y + 28, x + w, y + 72), C["panel"], 8, C["line"])
    text(draw, (x + 14, y + 39), "请输入" + label, 13, "#A9B8BB")


def sidebar(draw, active):
    draw.rectangle((0, 0, 248, 1024), fill=C["dark"])
    text(draw, (28, 32), "校园自习室预约系统", 21, "#FFFFFF")
    nav = [("home", "主页"), ("rooms", "自习室"), ("seat", "座位详情"), ("booking", "我的预约"), ("violations", "违规记录"), ("admin", "管理员")]
    for i, (key, label) in enumerate(nav):
        y = 128 + i * 56
        if key == active:
            rounded(draw, (16, y, 232, y + 40), C["primary"], 8)
        text(draw, (42, y + 10), label, 16, "#FFFFFF" if key == active else "#D8E7E8")
    text(draw, (28, 936), "学生 20230218", 14, "#D8E7E8")


def topbar(draw, title, subtitle):
    draw.rectangle((248, 0, 1440, 84), fill=C["panel"])
    draw.line((248, 84, 1440, 84), fill=C["line"], width=1)
    text(draw, (284, 18), title, 25, C["text"])
    text(draw, (284, 52), subtitle, 14, C["muted"])
    rounded(draw, (930, 22, 1180, 62), C["bg"], 8, C["line"])
    text(draw, (948, 34), "搜索自习室 / 座位", 13, "#A9B8BB")
    chip(draw, 1260, 26, 64, "在线")


def desktop_canvas(active, title, subtitle):
    img = Image.new("RGB", (1440, 1024), C["bg"])
    d = ImageDraw.Draw(img)
    sidebar(d, active)
    topbar(d, title, subtitle)
    return img, d


def mobile_canvas(title):
    img = Image.new("RGB", (390, 844), C["bg"])
    d = ImageDraw.Draw(img)
    draw = d
    draw.rectangle((0, 0, 390, 72), fill=C["panel"])
    draw.line((0, 72, 390, 72), fill=C["line"])
    text(draw, (24, 23), title, 21, C["text"])
    draw.rectangle((0, 768, 390, 844), fill=C["panel"])
    for i, label in enumerate(["首页", "自习室", "预约", "违规"]):
        text(draw, (i * 97.5, 790), label, 13, C["muted"], box=(i * 97.5, 790, 97.5, 26), align="center")
    return img, d


def seats(draw, x, y, cols, rows, size, gap):
    states = ["空", "占", "空", "约", "修", "空", "占", "空", "空", "占", "空", "空", "约", "占", "空", "空", "修", "空", "占", "空"]
    bg = {"空": C["green"], "占": C["red"], "约": C["cyan"], "修": C["gray"]}
    fg = {"空": C["primary"], "占": C["danger"], "约": C["primary"], "修": C["muted"]}
    for i in range(cols * rows):
        s = states[i % len(states)]
        xx = x + (i % cols) * (size + gap)
        yy = y + (i // cols) * (size + gap)
        rounded(draw, (xx, yy, xx + size, yy + size), bg[s], 8, C["line"])
        text(draw, (xx, yy), s, 14, fg[s], box=(xx, yy, size, size), align="center")


def auth(kind, mobile=False):
    if mobile:
        img = Image.new("RGB", (390, 844), C["bg"])
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 390, 220), fill=C["dark"])
        text(d, (28, 58), "校园自习室\n预约系统", 32, "#FFFFFF")
        card(d, 22, 176, 346, 420 if kind == "login" else 590)
        text(d, (46, 204), "用户登录" if kind == "login" else "用户注册", 24)
        labels = ["学号", "密码"] if kind == "login" else ["学号", "姓名", "手机号", "密码"]
        for i, label in enumerate(labels):
            input_box(d, 46, 262 + i * 88, 298, label)
        button(d, 46, 462 if kind == "login" else 628, 298, 46, "登录" if kind == "login" else "注册账号")
        return img
    img = Image.new("RGB", (1440, 1024), C["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 620, 1024), fill=C["dark"])
    text(d, (72, 310), "校园自习室\n预约系统", 44, "#FFFFFF")
    text(d, (76, 462), "在线选座、预约管理、签到签退与违规记录一体化", 18, "#BFE4E1")
    x, y, w, h = (800, 210, 420, 500) if kind == "login" else (720, 158, 560, 650)
    card(d, x, y, w, h)
    text(d, (x + 36, y + 34), "用户登录" if kind == "login" else "用户注册", 30)
    labels = ["学号", "密码"] if kind == "login" else ["学号", "姓名", "手机号", "学院/班级", "密码", "确认密码"]
    for i, label in enumerate(labels):
        input_box(d, x + 36 + (i % 2) * 264, y + 110 + (i // 2) * 100, 236 if kind != "login" else 348, label)
    button(d, x + 36, y + (338 if kind == "login" else 456), 348 if kind == "login" else 236, 48, "登录" if kind == "login" else "注册账号")
    if kind != "login":
        button(d, x + 300, y + 456, 236, 48, "返回登录", "ghost")
    return img


def desktop_page(kind, title):
    subtitles = {
        "home": "系统功能入口与今日学习状态",
        "rooms": "展示自习室和座位状态",
        "seat": "座位信息和预约按钮",
        "booking": "预约记录、签到签退、取消",
        "violations": "违规信息展示",
        "admin": "管理功能页面",
    }
    img, d = desktop_canvas(kind, title, subtitles[kind])
    if kind == "home":
        text(d, (284, 120), "下午好，林同学", 29)
        for i, (a, b) in enumerate([("可预约座位", "126"), ("今日预约", "1"), ("累计学习", "38h"), ("违规次数", "0")]):
            x = 284 + i * 254
            card(d, x, 214, 224, 128)
            text(d, (x + 22, 232), a, 14, C["muted"])
            text(d, (x + 22, 262), b, 36)
        for i, (a, b) in enumerate([("自习室预约", "查看空闲教室和座位"), ("我的预约", "签到、签退、取消预约"), ("违规记录", "查看迟到、爽约等记录"), ("管理员后台", "进入管理功能页面")]):
            x, y = 284 + (i % 2) * 420, 402 + (i // 2) * 180
            card(d, x, y, 380, 146)
            text(d, (x + 28, y + 24), a, 23)
            text(d, (x + 28, y + 64), b, 15, C["muted"])
            button(d, x + 270, y + 98, 80, 34, "进入")
    elif kind == "rooms":
        card(d, 284, 132, 1080, 620)
        for i, h in enumerate(["自习室", "位置", "开放时间", "座位状态", "操作"]):
            text(d, ([308, 554, 714, 894, 1204][i], 154), h, 15, C["muted"])
        rows = [("明德楼 301", "三楼东侧", "08:00-22:00", "空闲 24 / 已占 36 / 维修 2"), ("明德楼 302", "三楼西侧", "08:00-22:00", "空闲 18 / 已占 42 / 维修 0"), ("图书馆 A 区", "二楼南侧", "07:30-23:00", "空闲 46 / 已占 88 / 维修 4"), ("图书馆 B 区", "四楼北侧", "07:30-23:00", "空闲 12 / 已占 96 / 维修 1"), ("实验楼 501", "五楼", "09:00-21:30", "空闲 20 / 已占 28 / 维修 0")]
        for i, r in enumerate(rows):
            y = 202 + i * 96
            d.line((284, y, 1364, y), fill=C["line"])
            text(d, (308, y + 24), r[0], 18)
            text(d, (554, y + 24), r[1], 14, C["muted"])
            text(d, (714, y + 24), r[2], 14, C["muted"])
            chip(d, 894, y + 22, 250, r[3])
            button(d, 1204, y + 18, 92, 36, "查看座位")
    elif kind == "seat":
        card(d, 284, 124, 760, 700)
        text(d, (312, 148), "明德楼 301 座位平面图", 23)
        rounded(d, (568, 198, 748, 232), C["bg"], 8, C["line"])
        text(d, (568, 198), "讲台 / 白板", 14, C["muted"], box=(568, 198, 180, 34), align="center")
        seats(d, 356, 274, 8, 6, 56, 24)
        card(d, 1080, 124, 320, 430)
        text(d, (1108, 150), "座位 A03", 27)
        chip(d, 1278, 156, 82, "可预约", C["primary"], C["green"])
        for i, s in enumerate(["自习室：明德楼 301", "位置：靠窗第 1 排", "配置：插座 / 台灯", "时段：19:00-21:00"]):
            text(d, (1108, 220 + i * 58), s, 16, C["muted"])
        button(d, 1108, 468, 264, 48, "立即预约")
    elif kind == "booking":
        card(d, 284, 124, 500, 220)
        text(d, (312, 148), "当前预约", 23)
        chip(d, 672, 152, 78, "待签到", "#B7791F", C["yellow"])
        for i, s in enumerate(["明德楼 301 · A03", "今日 19:00-21:00", "靠窗 / 插座"]):
            text(d, (312, 200 + i * 38), s, 16, C["muted"])
        button(d, 580, 284, 76, 36, "签到")
        button(d, 672, 284, 76, 36, "取消", "ghost")
        card(d, 284, 390, 1080, 420)
        text(d, (308, 414), "预约记录", 23)
        for i, s in enumerate(["2026-06-04  明德楼301/A03  待签到", "2026-06-03  图书馆A区/C12  已签退", "2026-06-02  明德楼302/B08  已取消", "2026-05-31  实验楼501/E02  已签退"]):
            y = 464 + i * 72
            d.line((308, y, 1340, y), fill=C["line"])
            text(d, (308, y + 18), s, 16)
    elif kind == "violations":
        card(d, 284, 124, 340, 230)
        text(d, (312, 148), "预约信用状态", 23)
        text(d, (312, 196), "98", 56, C["primary"])
        text(d, (312, 304), "当前状态良好，可正常预约", 16, C["muted"])
        card(d, 668, 124, 696, 560)
        text(d, (692, 148), "违规信息", 23)
        for i, s in enumerate(["迟到签到：预约开始后 22 分钟签到", "取消超时：开始前 10 分钟取消预约", "爽约：预约后未签到"]):
            y = 206 + i * 120
            d.line((692, y, 1340, y), fill=C["line"])
            text(d, (692, y + 24), s, 17)
            chip(d, 1216, y + 20, 74, "已处理", C["primary"], C["green"])
    elif kind == "admin":
        for i, (a, b) in enumerate([("今日预约", "328"), ("签到率", "87%"), ("空闲座位", "126"), ("违规待处理", "3")]):
            x = 284 + i * 254
            card(d, x, 124, 224, 130)
            text(d, (x + 24, 144), a, 14, C["muted"])
            text(d, (x + 24, 176), b, 36)
        for i, m in enumerate(["自习室管理", "座位管理", "预约管理", "用户管理", "违规处理", "数据报表"]):
            x, y = 284 + (i % 3) * 356, 320 + (i // 3) * 178
            card(d, x, y, 320, 140)
            text(d, (x + 28, y + 28), m, 21)
            text(d, (x + 28, y + 68), "查看、编辑与维护相关数据", 14, C["muted"])
            button(d, x + 224, y + 96, 72, 34, "管理")
    return img


def mobile_page(kind, title):
    img, d = mobile_canvas(title)
    if kind == "home":
        text(d, (24, 94), "下午好，林同学", 24)
        for i, label in enumerate(["自习室预约", "我的预约", "违规记录", "管理员后台"]):
            x, y = 24 + (i % 2) * 178, 176 + (i // 2) * 134
            card(d, x, y, 154, 108)
            text(d, (x + 16, y + 34), label, 17)
    elif kind == "rooms":
        for i, r in enumerate(["明德楼 301 空闲24", "明德楼 302 空闲18", "图书馆 A 区 空闲46", "实验楼 501 空闲20"]):
            y = 98 + i * 128
            card(d, 24, y, 342, 104)
            text(d, (42, y + 20), r, 18)
            text(d, (42, y + 54), "08:00-22:00 · 点击查看座位", 13, C["muted"])
            button(d, 276, y + 58, 70, 30, "座位")
    elif kind == "seat":
        card(d, 24, 96, 342, 390)
        text(d, (42, 116), "明德楼 301 座位图", 20)
        seats(d, 52, 166, 5, 5, 42, 18)
        card(d, 24, 516, 342, 160)
        text(d, (44, 536), "座位 A03", 23)
        chip(d, 268, 540, 74, "可预约", C["primary"], C["green"])
        text(d, (44, 578), "靠窗第 1 排 · 插座 / 台灯\n可预约时段 19:00-21:00", 14, C["muted"])
        button(d, 222, 624, 112, 38, "立即预约")
    elif kind == "booking":
        card(d, 24, 96, 342, 170)
        text(d, (44, 116), "当前预约", 21)
        text(d, (44, 156), "明德楼 301 · A03\n今日 19:00-21:00", 15, C["muted"])
        button(d, 200, 216, 64, 32, "签到")
        button(d, 276, 216, 64, 32, "取消", "ghost")
        for i, r in enumerate(["图书馆 A区 已签退", "明德楼302 已取消", "实验楼501 已签退"]):
            y = 292 + i * 104
            card(d, 24, y, 342, 82)
            text(d, (42, y + 24), r, 16)
    elif kind == "violations":
        card(d, 24, 96, 342, 142)
        text(d, (44, 116), "预约信用状态", 20)
        text(d, (44, 152), "98", 42, C["primary"])
        for i, r in enumerate(["迟到签到 · 已处理", "取消超时 · 已处理", "爽约 · 已处理"]):
            y = 268 + i * 112
            card(d, 24, y, 342, 90)
            text(d, (42, y + 24), r, 17)
    elif kind == "admin":
        for i, (a, b) in enumerate([("今日预约", "328"), ("签到率", "87%"), ("待处理", "3")]):
            x = 24 + i * 118
            card(d, x, 96, 106, 92)
            text(d, (x + 12, 110), a, 12, C["muted"])
            text(d, (x + 12, 136), b, 27)
        for i, m in enumerate(["自习室管理", "座位管理", "预约管理", "用户管理", "违规处理", "数据报表"]):
            y = 220 + i * 82
            card(d, 24, y, 342, 64)
            text(d, (42, y + 18), m, 18)
            button(d, 280, y + 16, 64, 32, "管理")
    return img


screens = [
    ("login", "登录界面"),
    ("register", "注册界面"),
    ("home", "主页界面"),
    ("rooms", "自习室列表界面"),
    ("seat", "座位详情界面"),
    ("booking", "我的预约界面"),
    ("violations", "违规记录界面"),
    ("admin", "管理员后台界面"),
]

for key, title in screens:
    if key in {"login", "register"}:
        auth(key).save(OUT / f"desktop_{key}_{title}.png")
        auth(key, mobile=True).save(OUT / f"mobile_{key}_{title}.png")
    else:
        desktop_page(key, title).save(OUT / f"desktop_{key}_{title}.png")
        mobile_page(key, title).save(OUT / f"mobile_{key}_{title}.png")

print(f"generated {len(list(OUT.glob('*.png')))} png files in {OUT.resolve()}")
