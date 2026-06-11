import json
from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import Client, TestCase

from booking.models import Booking, Room, Seat, User, Violation


class StudyRoomApiRegressionTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create(
            account="20230218",
            password="123456",
            name="林同学",
            role="student",
            college="软件工程学院",
            class_name="软件工程 2301",
            phone="13800000000",
        )
        self.other_student = User.objects.create(
            account="20230219",
            password="123456",
            name="王同学",
            role="student",
            college="计算机学院",
            class_name="计科 2302",
            phone="13800000001",
        )
        self.admin = User.objects.create(
            account="admin001",
            password="admin123",
            name="管理员",
            role="admin",
            college="教务管理中心",
            class_name="自习室管理组",
            phone="010-88880000",
        )
        self.room = Room.objects.create(
            id="room-a",
            name="A 区自习室",
            location="图书馆一楼",
            open_hours="07:00-23:00",
            facilities=["插座", "台灯"],
            sort_order=1,
        )
        self.seat_a1 = Seat.objects.create(
            room=self.room,
            seat_no="A01",
            status="free",
            position_note="靠窗第 1 排",
            config="插座 / 台灯",
        )
        self.seat_a2 = Seat.objects.create(
            room=self.room,
            seat_no="A02",
            status="maintenance",
            position_note="靠窗第 1 排",
            config="设备维护中",
        )
        self.seat_a3 = Seat.objects.create(
            room=self.room,
            seat_no="A03",
            status="booked",
            position_note="中区第 1 排",
            config="插座 / 台灯",
        )

    def request_json(self, method, path, payload=None, **extra):
        data = None if payload is None else json.dumps(payload)
        response = getattr(self.client, method)(
            path,
            data=data,
            content_type="application/json",
            **extra,
        )
        body = json.loads(response.content.decode("utf-8") or "{}")
        return response, body

    def request_raw_json(self, method, path, raw_body):
        response = getattr(self.client, method)(
            path,
            data=raw_body,
            content_type="application/json",
        )
        body = json.loads(response.content.decode("utf-8") or "{}")
        return response, body

    def create_booking(self, seat=None, user=None, start=None, end=None, status="pending"):
        start = start or datetime(2026, 6, 12, 10, 0, 0)
        end = end or datetime(2026, 6, 12, 12, 0, 0)
        return Booking.objects.create(
            user=user or self.student,
            room=self.room,
            seat=seat or self.seat_a1,
            start_time=start,
            end_time=end,
            status=status,
        )

    def test_health_and_cors_preflight(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")

        response = self.client.options("/api/health")
        self.assertEqual(response.status_code, 204)
        self.assertIn("OPTIONS", response["Access-Control-Allow-Methods"])

    def test_login_success_password_error_and_role_mismatch(self):
        response, body = self.request_json(
            "post",
            "/api/auth/login",
            {"account": "20230218", "password": "123456", "role": "student"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["user"]["role"], "student")

        response, _ = self.request_json(
            "post",
            "/api/auth/login",
            {"account": "20230218", "password": "wrong", "role": "student"},
        )
        self.assertEqual(response.status_code, 401)

        response, _ = self.request_json(
            "post",
            "/api/auth/login",
            {"account": "20230218", "password": "123456", "role": "admin"},
        )
        self.assertEqual(response.status_code, 401)

        response, body = self.request_json(
            "post",
            "/api/auth/login",
            {"account": "admin001", "password": "admin123", "role": "admin"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["user"]["role"], "admin")

    def test_register_success_missing_fields_and_duplicate_account(self):
        payload = {
            "account": "20239999",
            "password": "123456",
            "name": "新同学",
            "college": "软件工程学院",
            "className": "软件工程 2303",
            "phone": "13900000000",
        }
        response, body = self.request_json("post", "/api/auth/register", payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["user"]["role"], "student")

        response, _ = self.request_json("post", "/api/auth/register", {**payload, "account": "20239998", "phone": ""})
        self.assertEqual(response.status_code, 400)

        response, _ = self.request_json("post", "/api/auth/register", payload)
        self.assertEqual(response.status_code, 409)

        response, body = self.request_raw_json("post", "/api/auth/login", "{bad json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("JSON", body["message"])

    def test_rooms_and_seats_statuses(self):
        self.create_booking(seat=self.seat_a1, status="checked_in")
        pending_seat = Seat.objects.create(
            room=self.room,
            seat_no="A04",
            status="free",
            position_note="中区第 1 排",
            config="插座 / 台灯",
        )
        self.create_booking(seat=pending_seat, status="pending")

        response, body = self.request_json("get", "/api/rooms")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["rooms"][0]["seats"]["maintenance"], 1)
        self.assertEqual(body["rooms"][0]["seats"]["used"], 1)

        response, body = self.request_json(
            "get",
            "/api/rooms/room-a/seats?startTime=2026-06-12T10:30:00&endTime=2026-06-12T11:00:00",
        )
        self.assertEqual(response.status_code, 200)
        status_by_seat = {seat["id"]: seat["status"] for seat in body["seats"]}
        self.assertEqual(status_by_seat["A01"], "used")
        self.assertEqual(status_by_seat["A02"], "maintenance")
        self.assertEqual(status_by_seat["A04"], "booked")

        response, body = self.request_json("get", "/api/rooms/not-found/seats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["seats"], [])

    def test_create_booking_success_conflicts_and_boundaries(self):
        base = self.create_booking()

        adjacent = {
            "userId": self.other_student.id,
            "roomId": self.room.id,
            "seatNo": self.seat_a1.seat_no,
            "startTime": "2026-06-12T12:00:00",
            "endTime": "2026-06-12T13:00:00",
        }
        response, body = self.request_json("post", "/api/bookings", adjacent)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["status"], "待签到")

        overlapping = {**adjacent, "startTime": "2026-06-12T11:00:00", "endTime": "2026-06-12T13:00:00"}
        response, _ = self.request_json("post", "/api/bookings", overlapping)
        self.assertEqual(response.status_code, 409)

        containing = {**adjacent, "startTime": "2026-06-12T09:00:00", "endTime": "2026-06-12T13:00:00"}
        response, _ = self.request_json("post", "/api/bookings", containing)
        self.assertEqual(response.status_code, 409)

        maintenance = {
            **adjacent,
            "seatNo": self.seat_a2.seat_no,
            "startTime": "2026-06-13T10:00:00",
            "endTime": "2026-06-13T12:00:00",
        }
        response, _ = self.request_json("post", "/api/bookings", maintenance)
        self.assertEqual(response.status_code, 409)

        missing_seat = {
            **adjacent,
            "seatNo": "Z99",
            "startTime": "2026-06-13T10:00:00",
            "endTime": "2026-06-13T12:00:00",
        }
        response, _ = self.request_json("post", "/api/bookings", missing_seat)
        self.assertEqual(response.status_code, 404)

        missing_user = {
            **adjacent,
            "userId": 999999,
            "startTime": "2026-06-15T10:00:00",
            "endTime": "2026-06-15T12:00:00",
        }
        response, _ = self.request_json("post", "/api/bookings", missing_user)
        self.assertEqual(response.status_code, 404)

        missing_room = {
            **adjacent,
            "roomId": "missing-room",
            "startTime": "2026-06-15T10:00:00",
            "endTime": "2026-06-15T12:00:00",
        }
        response, _ = self.request_json("post", "/api/bookings", missing_room)
        self.assertEqual(response.status_code, 404)

        invalid_time = {**adjacent, "startTime": "2026-06-14T10:00:00", "endTime": "2026-06-14T10:00:00"}
        response, _ = self.request_json("post", "/api/bookings", invalid_time)
        self.assertEqual(response.status_code, 400)

        response, body = self.request_json("get", f"/api/bookings/{self.student.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(base.id, [row["id"] for row in body["bookings"]])

    def test_booking_status_updates_and_violation_boundaries(self):
        now = datetime.now().replace(microsecond=0)
        cases = [
            ("checked_in", now - timedelta(minutes=6), -2, "轻微迟到"),
            ("checked_in", now - timedelta(minutes=16), -5, "迟到签到"),
            ("checked_in", now - timedelta(minutes=31), -8, "严重迟到"),
            ("canceled", now + timedelta(minutes=32), None, None),
            ("canceled", now + timedelta(minutes=30), -3, "临近取消"),
            ("canceled", now + timedelta(minutes=10), -5, "取消超时"),
            ("canceled", now - timedelta(minutes=1), -8, "开始后取消"),
        ]
        for index, (status, start, score, violation_type) in enumerate(cases):
            booking = self.create_booking(
                seat=self.seat_a1,
                start=start,
                end=start + timedelta(hours=2),
                status="pending",
            )
            response, body = self.request_json("patch", f"/api/bookings/{booking.id}/status", {"status": status})
            self.assertEqual(response.status_code, 200, index)
            if score is None:
                self.assertIsNone(body["violation"], index)
            else:
                self.assertEqual(body["violation"]["scoreChange"], score, index)
                self.assertTrue(Violation.objects.filter(user=self.student, type=violation_type).exists())

        booking = self.create_booking()
        response, _ = self.request_json("patch", f"/api/bookings/{booking.id}/status", {"status": "unknown"})
        self.assertEqual(response.status_code, 400)

        response, _ = self.request_json("patch", "/api/bookings/999999/status", {"status": "checked_in"})
        self.assertEqual(response.status_code, 404)

    def test_violation_query_appeal_and_admin_processing(self):
        violation = Violation.objects.create(
            user=self.student,
            type="迟到签到",
            reason="预约开始后 16 分钟签到",
            status="未申诉",
            happened_at=datetime(2026, 6, 10, 10, 16, 0),
        )
        other_violation = Violation.objects.create(
            user=self.other_student,
            type="爽约",
            reason="预约后未按时签到",
            status="未申诉",
            happened_at=datetime(2026, 6, 10, 11, 0, 0),
        )

        response, body = self.request_json("get", f"/api/violations/{self.student.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["violations"][0]["scoreChange"], -5)

        response, _ = self.request_json("patch", f"/api/violations/{violation.id}/appeal", {"userId": self.student.id, "reason": ""})
        self.assertEqual(response.status_code, 400)

        response, _ = self.request_json(
            "patch",
            f"/api/violations/{other_violation.id}/appeal",
            {"userId": self.student.id, "reason": "不是我的记录"},
        )
        self.assertEqual(response.status_code, 404)

        response, body = self.request_json(
            "patch",
            f"/api/violations/{violation.id}/appeal",
            {"userId": self.student.id, "reason": "当时网络异常"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "申诉待处理")

        response, body = self.request_json("get", "/api/admin/violations")
        self.assertEqual(response.status_code, 200)
        self.assertIn(violation.id, [row["id"] for row in body["violations"]])

        response, body = self.request_json("patch", f"/api/admin/violations/{violation.id}/status", {"action": "revoke"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "违规已撤回")

        response, _ = self.request_json("patch", "/api/admin/violations/999999/status", {"action": "reject"})
        self.assertEqual(response.status_code, 404)

        response, body = self.request_json("get", "/api/admin/users")
        self.assertEqual(response.status_code, 200)
        student_row = next(row for row in body["users"] if row["id"] == self.student.id)
        self.assertEqual(student_row["credit"], 100)

    def test_admin_user_room_and_seat_management(self):
        self.create_booking()

        response, body = self.request_json("get", "/api/admin/stats")
        self.assertEqual(response.status_code, 200)
        self.assertIn("todayBookings", body)
        self.assertIn("checkRate", body)

        response, body = self.request_json("get", "/api/admin/bookings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(body["bookings"]), 1)

        response, _ = self.request_json(
            "patch",
            f"/api/admin/users/{self.student.id}",
            {"name": "林同学改", "college": "软件工程学院", "className": "软件工程 2301", "phone": "13811111111"},
        )
        self.assertEqual(response.status_code, 200)

        response, _ = self.request_json("delete", f"/api/admin/users/{self.student.id}")
        self.assertEqual(response.status_code, 409)

        room_payload = {
            "id": "new-room-1",
            "name": "新增自习室",
            "location": "图书馆三楼",
            "hours": "08:00-22:00",
            "facilities": "插座, 台灯",
        }
        response, body = self.request_json("post", "/api/admin/rooms", room_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["room"]["seats"]["free"], 48)
        self.assertEqual(Seat.objects.filter(room_id="new-room-1").count(), 48)

        response, _ = self.request_json("post", "/api/admin/rooms", {**room_payload, "id": "中文 空格 !"})
        self.assertEqual(response.status_code, 400)

        response, _ = self.request_json("post", "/api/admin/rooms", room_payload)
        self.assertEqual(response.status_code, 409)

        response, body = self.request_json(
            "patch",
            "/api/admin/rooms/new-room-1",
            {"name": "新增自习室改", "location": "图书馆四楼", "hours": "08:30-22:30", "facilities": ["白板"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["room"]["facilities"], ["白板"])

        response, _ = self.request_json("delete", f"/api/admin/rooms/{self.room.id}")
        self.assertEqual(response.status_code, 409)

        response, body = self.request_json("patch", f"/api/admin/seats/{self.seat_a1.id}/status", {"status": "maintenance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "maintenance")
        self.seat_a1.refresh_from_db()
        self.assertEqual(self.seat_a1.status, "maintenance")

        response, _ = self.request_json("patch", f"/api/admin/seats/{self.seat_a1.id}/status", {"status": "broken"})
        self.assertEqual(response.status_code, 400)

        response, _ = self.request_json("patch", "/api/admin/seats/999999/status", {"status": "free"})
        self.assertEqual(response.status_code, 404)

    def test_seed_demo_command_creates_representative_data(self):
        User.objects.all().delete()
        Room.objects.all().delete()

        call_command("seed_demo", verbosity=0)

        self.assertEqual(User.objects.filter(role="student").count(), 3)
        self.assertEqual(User.objects.filter(role="admin").count(), 2)
        self.assertGreaterEqual(Room.objects.count(), 2)
        self.assertEqual(Seat.objects.count(), Room.objects.count() * 48)
        self.assertTrue(Booking.objects.filter(status="pending").exists())
        self.assertTrue(Violation.objects.filter(status="申诉待处理").exists())
