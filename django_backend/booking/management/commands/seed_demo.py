from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from booking.models import Booking, Room, Seat, User, Violation


ROOMS = [
    {
        "id": "taishan-branch",
        "name": "泰山区图书馆分馆",
        "location": "泰山区图书馆分馆二楼",
        "open_hours": "07:30-22:30",
        "facilities": ["插座", "台灯", "靠窗区", "饮水点"],
    },
    {
        "id": "main-library-1f",
        "name": "总图书馆一楼",
        "location": "总图书馆一楼东侧",
        "open_hours": "07:00-23:00",
        "facilities": ["插座", "大桌区", "自助借还"],
    },
    {
        "id": "main-library-2f",
        "name": "总图书馆二楼",
        "location": "总图书馆二楼南侧",
        "open_hours": "07:00-23:00",
        "facilities": ["插座", "阅读灯", "安静区"],
    },
    {
        "id": "main-library-3f",
        "name": "总图书馆三楼",
        "location": "总图书馆三楼北侧",
        "open_hours": "07:00-23:00",
        "facilities": ["插座", "考研专区", "储物柜"],
    },
    {
        "id": "main-library-4f",
        "name": "总图书馆四楼",
        "location": "总图书馆四楼西侧",
        "open_hours": "07:30-22:00",
        "facilities": ["阅读区", "空调", "静音区"],
    },
]


USERS = [
    ("20230218", "123456", "林同学", "student", "软件工程学院", "软件工程 2301", "13800000000"),
    ("20230219", "123456", "王同学", "student", "计算机科学与技术学院", "计科 2302", "13800000001"),
    ("20230220", "123456", "陈同学", "student", "信息管理学院", "信管 2301", "13800000002"),
    ("admin001", "admin123", "管理员", "admin", "教务管理中心", "自习室管理组", "010-88880000"),
    ("admin002", "admin123", "值班管理员", "admin", "图书馆管理中心", "自习室值班组", "010-88880001"),
]


BASE_STATUSES = [
    "free",
    "used",
    "booked",
    "free",
    "maintenance",
    "free",
    "used",
    "free",
    "free",
    "used",
    "free",
    "free",
    "booked",
    "used",
    "free",
    "free",
    "maintenance",
    "free",
    "used",
    "free",
    "free",
    "used",
    "booked",
    "free",
    "maintenance",
    "free",
    "free",
    "used",
    "free",
    "free",
    "booked",
    "free",
    "free",
    "used",
    "free",
    "free",
    "free",
    "used",
    "maintenance",
    "free",
    "free",
    "used",
    "free",
    "free",
    "free",
    "booked",
    "used",
    "free",
]


class Command(BaseCommand):
    help = "Seed demo data for the campus study room booking project."

    def handle(self, *args, **options):
        with transaction.atomic():
            if User.objects.exists() or Room.objects.exists():
                self.stdout.write(self.style.WARNING("Demo data already exists; skipped."))
                return

            self.create_users()
            self.create_rooms_and_seats()
            self.create_bookings()
            self.create_violations()

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def create_users(self):
        User.objects.bulk_create(
            [
                User(
                    account=account,
                    password=password,
                    name=name,
                    role=role,
                    college=college,
                    class_name=class_name,
                    phone=phone,
                )
                for account, password, name, role, college, class_name, phone in USERS
            ]
        )

    def create_rooms_and_seats(self):
        for index, room_data in enumerate(ROOMS, start=1):
            room = Room.objects.create(sort_order=index, **room_data)
            Seat.objects.bulk_create(self.make_seats(room, index))

    def make_seats(self, room, room_index):
        seats = []
        for index, base_status in enumerate(BASE_STATUSES):
            row = chr(ord("A") + index // 8)
            seat_no = f"{row}{index % 8 + 1:02d}"
            status = self.adjust_status(room_index, seat_no, base_status)
            area = "靠窗" if index % 8 < 4 else "中区"
            seats.append(
                Seat(
                    room=room,
                    seat_no=seat_no,
                    status=status,
                    position_note=f"{area}第 {index // 8 + 1} 排",
                    config="插座 / 台灯" if status != "maintenance" else "设备维护中",
                )
            )
        return seats

    def adjust_status(self, room_index, seat_no, status):
        if room_index == 2 and seat_no in {"A01", "A02", "B01", "B02"}:
            return "maintenance"
        if room_index == 3 and status == "booked":
            return "free"
        if room_index == 4 and seat_no in {"A05", "B05", "C05", "D05"}:
            return "maintenance"
        if room_index == 5 and status == "booked":
            return "used"
        return status

    def create_bookings(self):
        rows = [
            ("20230218", "taishan-branch", "A03", "2026-06-05 19:00:00", "2026-06-05 21:00:00", "pending"),
            ("20230219", "main-library-2f", "C04", "2026-06-04 14:00:00", "2026-06-04 17:00:00", "completed"),
            ("20230220", "main-library-1f", "B08", "2026-06-03 09:00:00", "2026-06-03 11:00:00", "canceled"),
            ("20230218", "main-library-3f", "F06", "2026-06-02 18:30:00", "2026-06-02 21:30:00", "checked_in"),
        ]
        for account, room_id, seat_no, start, end, status in rows:
            user = User.objects.get(account=account)
            seat = Seat.objects.get(room_id=room_id, seat_no=seat_no)
            Booking.objects.create(
                user=user,
                room_id=room_id,
                seat=seat,
                start_time=datetime.strptime(start, "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime(end, "%Y-%m-%d %H:%M:%S"),
                status=status,
            )

    def create_violations(self):
        rows = [
            ("20230218", "迟到签到", "预约开始后 22 分钟签到", "已处理", "2026-05-18 19:22:00"),
            ("20230218", "取消超时", "开始前 10 分钟取消预约", "已处理", "2026-04-26 13:50:00"),
            ("20230219", "爽约", "预约后未按时签到", "已处理", "2026-03-12 09:30:00"),
            ("20230220", "占座超时", "签退后物品未及时带离", "申诉待处理", "2026-06-03 21:20:00"),
        ]
        for account, violation_type, reason, status, happened_at in rows:
            Violation.objects.create(
                user=User.objects.get(account=account),
                type=violation_type,
                reason=reason,
                status=status,
                happened_at=datetime.strptime(happened_at, "%Y-%m-%d %H:%M:%S"),
            )
