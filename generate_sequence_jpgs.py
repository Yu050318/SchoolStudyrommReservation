from PIL import Image, ImageDraw, ImageFont
import os
import textwrap


OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = r"C:\Windows\Fonts\Noto Sans SC (TrueType).otf"
FONT_BOLD = r"C:\Windows\Fonts\Noto Sans SC Bold (TrueType).otf"


def font(size, bold=False):
    path = FONT_BOLD if bold and os.path.exists(FONT_BOLD) else FONT
    return ImageFont.truetype(path, size)


TITLE = font(34, True)
HEAD = font(21, True)
TEXT = font(18)
SMALL = font(15)
COND = font(16, True)


def wrap_cn(text, width):
    rows = []
    line = ""
    for ch in text:
        line += ch
        if len(line) >= width:
            rows.append(line)
            line = ""
    if line:
        rows.append(line)
    return rows


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def arrow(draw, x1, y, x2, label, color="#2563eb"):
    draw.line((x1, y, x2, y), fill=color, width=3)
    if x2 >= x1:
        pts = [(x2, y), (x2 - 12, y - 7), (x2 - 12, y + 7)]
    else:
        pts = [(x2, y), (x2 + 12, y - 7), (x2 + 12, y + 7)]
    draw.polygon(pts, fill=color)
    max_chars = max(8, int(abs(x2 - x1) / 18))
    lines = wrap_cn(label, max_chars)
    label_w = max(text_size(draw, ln, TEXT)[0] for ln in lines)
    label_h = len(lines) * 24
    lx = (x1 + x2) / 2 - label_w / 2
    ly = y - label_h - 8
    draw.rounded_rectangle((lx - 8, ly - 5, lx + label_w + 8, ly + label_h + 3), radius=8, fill="#ffffff", outline="#dbeafe")
    for i, ln in enumerate(lines):
        draw.text((lx, ly + i * 24), ln, fill="#1e3a8a", font=TEXT)


def self_call(draw, x, y, label):
    w = 100
    draw.line((x, y, x + w, y), fill="#2563eb", width=3)
    draw.line((x + w, y, x + w, y + 34), fill="#2563eb", width=3)
    draw.line((x + w, y + 34, x + 8, y + 34), fill="#2563eb", width=3)
    draw.polygon([(x + 8, y + 34), (x + 20, y + 27), (x + 20, y + 41)], fill="#2563eb")
    lines = wrap_cn(label, 13)
    lx = x + 10
    ly = y - len(lines) * 24 - 8
    for i, ln in enumerate(lines):
        draw.text((lx, ly + i * 24), ln, fill="#1e3a8a", font=TEXT)


def render_sequence(filename, title, participants, events):
    margin_x = 72
    top = 92
    header_y = 138
    row_gap = 86
    width = max(1180, margin_x * 2 + (len(participants) - 1) * 210 + 180)
    height = 260 + len(events) * row_gap
    img = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(img)

    draw.text((margin_x, 36), title, fill="#0f172a", font=TITLE)
    draw.line((margin_x, 82, width - margin_x, 82), fill="#cbd5e1", width=2)

    step = (width - margin_x * 2) / (len(participants) - 1) if len(participants) > 1 else 0
    xs = {p: margin_x + i * step for i, p in enumerate(participants)}

    for p in participants:
        x = xs[p]
        label_w, _ = text_size(draw, p, HEAD)
        box_w = max(124, label_w + 34)
        draw.rounded_rectangle((x - box_w / 2, header_y - 28, x + box_w / 2, header_y + 28), radius=12, fill="#e0f2fe", outline="#38bdf8", width=2)
        draw.text((x - label_w / 2, header_y - 15), p, fill="#075985", font=HEAD)
        draw.line((x, header_y + 36, x, height - 60), fill="#94a3b8", width=2)

    y = header_y + 86
    open_frames = []
    frame_left = margin_x - 34
    frame_right = width - margin_x + 34

    for ev in events:
        kind = ev[0]
        if kind == "group_start":
            label = ev[1]
            open_frames.append((y - 48, label))
            draw.rounded_rectangle((frame_left, y - 54, frame_right, y + row_gap - 18), radius=10, outline="#f59e0b", width=2)
            draw.rectangle((frame_left, y - 54, frame_left + 96, y - 25), fill="#fef3c7", outline="#f59e0b")
            draw.text((frame_left + 12, y - 51), label, fill="#92400e", font=COND)
            y += row_gap
            continue
        if kind == "group_mid":
            label = ev[1]
            draw.line((frame_left, y - 45, frame_right, y - 45), fill="#f59e0b", width=2)
            draw.rectangle((frame_left, y - 45, frame_left + 96, y - 16), fill="#fef3c7", outline="#f59e0b")
            draw.text((frame_left + 12, y - 42), label, fill="#92400e", font=COND)
            y += 34
            continue
        if kind == "group_end":
            y += 20
            continue
        if kind == "note":
            text = ev[1]
            lines = wrap_cn(text, 42)
            h = max(44, len(lines) * 23 + 20)
            draw.rounded_rectangle((margin_x, y - 32, width - margin_x, y - 32 + h), radius=10, fill="#ecfeff", outline="#67e8f9")
            for i, ln in enumerate(lines):
                draw.text((margin_x + 18, y - 22 + i * 23), ln, fill="#155e75", font=TEXT)
            y += h + 22
            continue

        sender, receiver, msg = ev
        if sender == receiver:
            self_call(draw, xs[sender], y, msg)
        else:
            arrow(draw, xs[sender], y, xs[receiver], msg)
        y += row_gap

    img.save(os.path.join(OUT_DIR, filename), quality=95)


diagrams = [
    (
        "顺序图_01_登录注册进入系统.jpg",
        "登录 / 注册进入系统顺序图",
        ["用户", "登录界面", "注册界面", "系统主页", "管理员后台"],
        [
            ("用户", "登录界面", "打开系统"),
            ("group_start", "alt 普通学生登录"),
            ("用户", "登录界面", "输入学号和密码，点击登录"),
            ("登录界面", "系统主页", 'enterApp("home", "student")'),
            ("group_mid", "else 注册账号"),
            ("用户", "登录界面", "点击“立即注册”"),
            ("登录界面", "注册界面", 'authMode = "register"'),
            ("用户", "注册界面", "填写信息，点击注册账号"),
            ("注册界面", "系统主页", 'enterApp("home", "student")'),
            ("group_mid", "else 管理员登录"),
            ("用户", "登录界面", "点击“以管理员身份登录”"),
            ("登录界面", "管理员后台", 'enterApp("admin", "admin")'),
            ("group_end",),
        ],
    ),
    (
        "顺序图_02_学生端主要界面跳转.jpg",
        "学生端主要界面跳转顺序图",
        ["学生", "主页", "自习室列表", "座位详情", "我的预约", "违规记录"],
        [
            ("学生", "主页", "登录成功后进入"),
            ("学生", "自习室列表", "点击“开始预约”或“自习室预约”"),
            ("自习室列表", "座位详情", "点击某自习室的“查看座位”"),
            ("座位详情", "我的预约", "选择空闲座位后点击“立即预约”"),
            ("学生", "主页", "点击侧边栏/底部导航“主页”"),
            ("学生", "我的预约", "点击“我的预约”"),
            ("学生", "违规记录", "点击“违规记录”"),
            ("学生", "自习室列表", "点击“自习室”"),
            ("学生", "座位详情", "点击“座位详情”"),
        ],
    ),
    (
        "顺序图_03_座位预约业务跳转.jpg",
        "座位预约业务跳转顺序图",
        ["学生", "自习室列表界面", "座位详情界面", "我的预约界面"],
        [
            ("学生", "自习室列表界面", "搜索或筛选自习室"),
            ("学生", "自习室列表界面", "点击“查看座位”"),
            ("自习室列表界面", "座位详情界面", "openRoom(roomId)"),
            ("学生", "座位详情界面", "点击空闲座位"),
            ("座位详情界面", "座位详情界面", "selectSeat(seat)"),
            ("学生", "座位详情界面", "点击“立即预约”"),
            ("座位详情界面", "我的预约界面", "reserveSeat()"),
            ("我的预约界面", "我的预约界面", "显示当前预约，状态为“待签到”"),
            ("学生", "我的预约界面", "点击签到/签退/取消"),
            ("我的预约界面", "我的预约界面", "updateBookingStatus(status)"),
        ],
    ),
    (
        "顺序图_04_账号切换退出跳转.jpg",
        "账号切换 / 退出跳转顺序图",
        ["用户", "当前业务界面", "个人菜单", "登录界面"],
        [
            ("用户", "当前业务界面", "点击头像/个人信息"),
            ("当前业务界面", "个人菜单", "展开菜单"),
            ("group_start", "alt 切换账号"),
            ("用户", "个人菜单", "点击“切换账号”"),
            ("个人菜单", "登录界面", "switchAccount()"),
            ("group_mid", "else 退出账号"),
            ("用户", "个人菜单", "点击“退出账号”"),
            ("个人菜单", "登录界面", "logout()"),
            ("group_mid", "else 侧边栏安全退出"),
            ("用户", "当前业务界面", "点击“安全退出”"),
            ("当前业务界面", "登录界面", "logout()"),
            ("group_end",),
        ],
    ),
    (
        "顺序图_05_管理员端跳转.jpg",
        "管理员端跳转顺序图",
        ["管理员", "登录界面", "管理员后台"],
        [
            ("管理员", "登录界面", "点击“以管理员身份登录”"),
            ("登录界面", "管理员后台", 'enterApp("admin", "admin")'),
            ("管理员", "管理员后台", "查看今日预约、签到率、空闲座位、违规待处理"),
            ("管理员", "管理员后台", "查看自习室管理、座位管理、预约管理、用户管理、违规处理、数据报表模块"),
            ("管理员", "管理员后台", "点击侧边栏导航"),
            ("管理员后台", "管理员后台", "goPage(page)，管理员始终停留在 admin 页面"),
            ("管理员", "管理员后台", "点击退出"),
            ("管理员后台", "登录界面", "logout()"),
        ],
    ),
]


for args in diagrams:
    render_sequence(*args)

print("已生成 JPG 顺序图：")
for name, *_ in diagrams:
    print(os.path.join(OUT_DIR, name))
