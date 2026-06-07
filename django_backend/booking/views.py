import json
import re
from datetime import datetime

from django.db import transaction
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import Booking, Room, Seat, User, Violation


BOOKING_STATUS_CN = {
    "pending": "待签到",
    "checked_in": "已签到",
    "completed": "已签退",
    "canceled": "已取消",
}
BOOKING_STATUS_API = {value: key for key, value in BOOKING_STATUS_CN.items()}
SEAT_STATUS_CN = {
    "free": "空闲",
    "used": "已占用",
    "booked": "已预约",
    "maintenance": "维修",
}
APPEAL_DELIMITER = "\n申诉理由："
VIOLATION_SCORE_BY_TYPE = {
    "爽约": -12,
    "开始后取消": -8,
    "严重迟到": -8,
    "占座超时": -6,
    "取消超时": -5,
    "迟到签到": -5,
    "临近取消": -3,
    "轻微迟到": -2,
}


def api_response(payload, status=200):
    response = JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def read_json(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def public_user(user):
    return {
        "id": user.id,
        "account": user.account,
        "name": user.name,
        "role": user.role,
        "college": user.college,
        "className": user.class_name,
        "phone": user.phone,
    }


def user_credit_state(score):
    if score >= 70:
        return "正常"
    if score >= 60:
        return "预警"
    if score >= 40:
        return "限制"
    return "冻结"


def violation_score(violation):
    if violation.status == "违规已撤回":
        return 0
    return VIOLATION_SCORE_BY_TYPE.get(violation.type, 0)


def split_appeal_reason(violation):
    reason = violation.reason or ""
    base_reason, *appeal_parts = reason.split(APPEAL_DELIMITER)
    return {
        "id": violation.id,
        "date": violation.happened_at.strftime("%Y-%m-%d"),
        "type": violation.type,
        "reason": base_reason,
        "status": violation.status,
        "scoreChange": violation_score(violation),
        "appealReason": APPEAL_DELIMITER.join(appeal_parts).strip(),
    }


def parse_booking_datetime(value, fallback):
    if not value:
        return fallback
    parsed = parse_datetime(str(value).replace(" ", "T"))
    if parsed:
        return parsed.replace(tzinfo=None)
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")


def get_credit_violation(status, minutes_late, minutes_before):
    if status == "checked_in":
        if minutes_late > 30:
            return {"type": "严重迟到", "reason": f"预约开始后 {minutes_late} 分钟签到", "scoreChange": -8}
        if minutes_late > 15:
            return {"type": "迟到签到", "reason": f"预约开始后 {minutes_late} 分钟签到", "scoreChange": -5}
        if minutes_late > 5:
            return {"type": "轻微迟到", "reason": f"预约开始后 {minutes_late} 分钟签到", "scoreChange": -2}

    if status == "canceled":
        if minutes_before < 0:
            return {"type": "开始后取消", "reason": "预约开始后取消预约", "scoreChange": -8}
        if minutes_before <= 10:
            return {"type": "取消超时", "reason": f"开始前 {minutes_before} 分钟取消预约", "scoreChange": -5}
        if minutes_before <= 30:
            return {"type": "临近取消", "reason": f"开始前 {minutes_before} 分钟取消预约", "scoreChange": -3}
    return None


@csrf_exempt
def health(request):
    if request.method == "OPTIONS":
        return api_response({}, status=204)
    return api_response({"ok": True})


@csrf_exempt
def login(request):
    if request.method != "POST":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    query = User.objects.filter(account=body.get("account"), password=body.get("password"))
    if body.get("role"):
        query = query.filter(role=body.get("role"))
    user = query.first()
    if not user:
        return api_response({"message": "账号、密码或身份不正确"}, status=401)
    return api_response({"user": public_user(user)})


@csrf_exempt
def register(request):
    if request.method != "POST":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    email = body.get("email") or body.get("phone")
    required = [body.get("account"), body.get("name"), email, body.get("college"), body.get("className"), body.get("password")]
    if not all(required):
        return api_response({"message": "注册信息不能为空"}, status=400)
    if User.objects.filter(account=body.get("account")).exists():
        return api_response({"message": "该学号已注册，请直接登录"}, status=409)
    user = User.objects.create(
        account=body["account"],
        password=body["password"],
        name=body["name"],
        role="student",
        college=body["college"],
        class_name=body["className"],
        phone=email,
    )
    return api_response({"user": public_user(user)}, status=201)


def rooms(request):
    if request.method != "GET":
        return api_response({"message": "方法不支持"}, status=405)
    rows = Room.objects.annotate(
        free=Count("seats", filter=Q(seats__status="free")),
        used=Count("seats", filter=Q(seats__status__in=["used", "booked"])),
        maintenance=Count("seats", filter=Q(seats__status="maintenance")),
    )
    return api_response(
        {
            "rooms": [
                {
                    "id": room.id,
                    "name": room.name,
                    "location": room.location,
                    "hours": room.open_hours,
                    "facilities": room.facilities or [],
                    "seats": {
                        "free": room.free,
                        "used": room.used,
                        "maintenance": room.maintenance,
                    },
                }
                for room in rows
            ]
        }
    )


def room_seats(request, room_id):
    if request.method != "GET":
        return api_response({"message": "方法不支持"}, status=405)
    seats = Seat.objects.filter(room_id=room_id).order_by("seat_no")
    return api_response(
        {
            "seats": [
                {
                    "id": seat.seat_no,
                    "status": seat.status,
                    "positionNote": seat.position_note,
                    "config": seat.config,
                }
                for seat in seats
            ]
        }
    )


@csrf_exempt
def create_booking(request):
    if request.method != "POST":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    try:
        with transaction.atomic():
            seat = Seat.objects.select_for_update().get(room_id=body.get("roomId"), seat_no=body.get("seatNo"))
            if seat.status != "free":
                return api_response({"message": "该座位当前不可预约"}, status=409)
            start_time = parse_booking_datetime(body.get("startTime"), datetime(2026, 6, 4, 19, 0, 0))
            end_time = parse_booking_datetime(body.get("endTime"), datetime(2026, 6, 4, 21, 0, 0))
            seat.status = "booked"
            seat.save(update_fields=["status"])
            booking = Booking.objects.create(
                user_id=body.get("userId"),
                room_id=body.get("roomId"),
                seat=seat,
                start_time=start_time,
                end_time=end_time,
                status="pending",
            )
    except Seat.DoesNotExist:
        return api_response({"message": "座位不存在"}, status=404)
    return api_response({"id": booking.id, "status": "待签到"}, status=201)


def user_bookings(request, user_id):
    if request.method != "GET":
        return api_response({"message": "方法不支持"}, status=405)
    bookings = Booking.objects.select_related("room", "seat").filter(user_id=user_id)
    return api_response(
        {
            "bookings": [
                {
                    "id": booking.id,
                    "date": booking.start_time.strftime("%Y-%m-%d"),
                    "room": booking.room.name,
                    "seat": booking.seat.seat_no,
                    "time": f"{booking.start_time:%H:%M}-{booking.end_time:%H:%M}",
                    "status": BOOKING_STATUS_CN.get(booking.status, booking.status),
                }
                for booking in bookings
            ]
        }
    )


@csrf_exempt
def booking_status(request, booking_id):
    if request.method != "PATCH":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    status = BOOKING_STATUS_API.get(body.get("status"), body.get("status"))
    allowed = {"pending", "checked_in", "completed", "canceled"}
    if status not in allowed:
        return api_response({"message": "预约状态不正确"}, status=400)

    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().select_related("seat").get(id=booking_id)
            now = datetime.now()
            minutes_late = int((now - booking.start_time).total_seconds() // 60)
            minutes_before = int((booking.start_time - now).total_seconds() // 60)
            violation = get_credit_violation(status, minutes_late, minutes_before)
            booking.status = status
            booking.save(update_fields=["status"])
            booking.seat.status = "free" if status in {"completed", "canceled"} else "booked"
            booking.seat.save(update_fields=["status"])
            if violation:
                Violation.objects.create(
                    user=booking.user,
                    type=violation["type"],
                    reason=violation["reason"],
                    status="未申诉",
                    happened_at=now,
                )
    except Booking.DoesNotExist:
        return api_response({"message": "预约记录不存在"}, status=404)

    return api_response({"status": BOOKING_STATUS_CN.get(status, status), "violation": violation})


def user_violations(request, user_id):
    if request.method != "GET":
        return api_response({"message": "方法不支持"}, status=405)
    rows = Violation.objects.filter(user_id=user_id)
    return api_response({"violations": [split_appeal_reason(row) for row in rows]})


@csrf_exempt
def appeal_violation(request, violation_id):
    if request.method != "PATCH":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    appeal_reason = str(body.get("reason") or "").strip()
    if not appeal_reason:
        return api_response({"message": "请填写申诉理由"}, status=400)
    violation = Violation.objects.filter(id=violation_id, user_id=body.get("userId")).first()
    if not violation:
        return api_response({"message": "违规记录不存在"}, status=404)
    if violation.status == "违规已撤回":
        return api_response({"message": "该违规已撤回，无需申诉"}, status=409)
    if violation.status == "申诉待处理":
        return api_response({"status": "申诉待处理", "message": "申诉已提交，请等待管理员审核"})
    clean_reason = (violation.reason or "").split(APPEAL_DELIMITER)[0]
    violation.reason = f"{clean_reason}{APPEAL_DELIMITER}{appeal_reason}"
    violation.status = "申诉待处理"
    violation.save(update_fields=["reason", "status"])
    return api_response({"status": "申诉待处理", "message": "申诉已提交，请等待管理员审核"})


def admin_stats(request):
    today = datetime.now().date()
    total_bookings = Booking.objects.count()
    checked_bookings = Booking.objects.filter(status__in=["checked_in", "completed"]).count()
    check_rate = round(checked_bookings / total_bookings * 100) if total_bookings else 0
    return api_response(
        {
            "todayBookings": Booking.objects.filter(start_time__date=today).count(),
            "checkRate": check_rate,
            "freeSeats": Seat.objects.filter(status="free").count(),
            "pendingViolations": Violation.objects.filter(status="申诉待处理").count(),
        }
    )


def admin_bookings(request):
    rows = Booking.objects.select_related("user", "room", "seat").order_by("-created_at", "-start_time")
    return api_response(
        {
            "bookings": [
                {
                    "id": row.id,
                    "account": row.user.account,
                    "user": row.user.name,
                    "date": row.start_time.strftime("%Y-%m-%d"),
                    "room": row.room.name,
                    "seat": row.seat.seat_no,
                    "time": f"{row.start_time:%H:%M}-{row.end_time:%H:%M}",
                    "status": BOOKING_STATUS_CN.get(row.status, row.status),
                    "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for row in rows
            ]
        }
    )


def admin_users(request):
    users = User.objects.filter(role="student").annotate(bookings_count=Count("bookings")).order_by("-id")
    payload = []
    for user in users:
        score_delta = sum(violation_score(row) for row in user.violations.all())
        credit = max(0, 100 + score_delta)
        payload.append(
            {
                "id": user.id,
                "account": user.account,
                "name": user.name,
                "college": user.college,
                "className": user.class_name,
                "phone": user.phone,
                "bookings": user.bookings_count,
                "credit": credit,
                "status": user_credit_state(credit),
            }
        )
    return api_response({"users": payload})


@csrf_exempt
def admin_user_detail(request, user_id):
    user = User.objects.filter(id=user_id, role="student").first()
    if not user:
        return api_response({"message": "学生账号不存在"}, status=404)
    if request.method == "PATCH":
        body = read_json(request)
        if not all([body.get("name"), body.get("college"), body.get("className"), body.get("phone")]):
            return api_response({"message": "学生姓名、学院、班级和联系方式不能为空"}, status=400)
        user.name = body["name"]
        user.college = body["college"]
        user.class_name = body["className"]
        user.phone = body["phone"]
        if body.get("password"):
            user.password = body["password"]
        user.save()
        return api_response({"user": public_user(user)})
    if request.method == "DELETE":
        if Booking.objects.filter(user=user).exists() or Violation.objects.filter(user=user).exists():
            return api_response({"message": "该学生已有预约或违规记录，不能直接删除"}, status=409)
        deleted = {"id": user.id, "account": user.account, "name": user.name}
        user.delete()
        return api_response(deleted)
    return api_response({"message": "方法不支持"}, status=405)


def admin_violations(request):
    rows = Violation.objects.select_related("user").filter(status="申诉待处理")
    return api_response(
        {
            "violations": [
                {
                    **split_appeal_reason(row),
                    "account": row.user.account,
                    "user": row.user.name,
                }
                for row in rows
            ]
        }
    )


def admin_seats(request):
    room_id = request.GET.get("roomId")
    seats = Seat.objects.select_related("room")
    if room_id:
        seats = seats.filter(room_id=room_id)
    return api_response(
        {
            "seats": [
                {
                    "id": seat.id,
                    "roomId": seat.room_id,
                    "room": seat.room.name,
                    "seatNo": seat.seat_no,
                    "status": seat.status,
                    "positionNote": seat.position_note,
                    "config": seat.config,
                }
                for seat in seats
            ]
        }
    )


@csrf_exempt
def admin_seat_status(request, seat_id):
    if request.method != "PATCH":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    if body.get("status") not in SEAT_STATUS_CN:
        return api_response({"message": "座位状态不正确"}, status=400)
    Seat.objects.filter(id=seat_id).update(status=body["status"])
    return api_response({"status": body["status"]})


@csrf_exempt
def admin_rooms(request):
    if request.method != "POST":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    room_id = str(body.get("id") or "").strip()
    if not all([room_id, body.get("name"), body.get("location"), body.get("hours")]):
        return api_response({"message": "自习室编号、名称、位置和开放时间不能为空"}, status=400)
    if not re.match(r"^[a-zA-Z0-9_-]+$", room_id):
        return api_response({"message": "自习室编号只能包含字母、数字、下划线和短横线"}, status=400)
    if Room.objects.filter(id=room_id).exists():
        return api_response({"message": "该自习室编号已存在"}, status=409)

    facilities = parse_facilities(body.get("facilities"))
    sort_order = (Room.objects.aggregate(value=Max("sort_order"))["value"] or 0) + 1
    with transaction.atomic():
        room = Room.objects.create(
            id=room_id,
            name=body["name"],
            location=body["location"],
            open_hours=body["hours"],
            facilities=facilities,
            sort_order=sort_order,
        )
        Seat.objects.bulk_create(make_default_seats(room))
    return api_response(
        {
            "room": {
                "id": room.id,
                "name": room.name,
                "location": room.location,
                "hours": room.open_hours,
                "facilities": facilities,
                "seats": {"free": 48, "used": 0, "maintenance": 0},
            }
        },
        status=201,
    )


@csrf_exempt
def admin_room_detail(request, room_id):
    room = Room.objects.filter(id=room_id).first()
    if not room:
        return api_response({"message": "自习室不存在"}, status=404)
    if request.method == "DELETE":
        if Booking.objects.filter(room=room).exists():
            return api_response({"message": "该自习室已有预约记录，不能直接删除"}, status=409)
        deleted = {"id": room.id, "name": room.name}
        room.delete()
        return api_response(deleted)
    if request.method == "PATCH":
        body = read_json(request)
        if not all([body.get("name"), body.get("location"), body.get("hours")]):
            return api_response({"message": "自习室名称、位置和开放时间不能为空"}, status=400)
        room.name = body["name"]
        room.location = body["location"]
        room.open_hours = body["hours"]
        room.facilities = parse_facilities(body.get("facilities"))
        room.save()
        return api_response(
            {
                "room": {
                    "id": room.id,
                    "name": room.name,
                    "location": room.location,
                    "hours": room.open_hours,
                    "facilities": room.facilities,
                }
            }
        )
    return api_response({"message": "方法不支持"}, status=405)


@csrf_exempt
def admin_violation_status(request, violation_id):
    if request.method != "PATCH":
        return api_response({"message": "方法不支持"}, status=405)
    body = read_json(request)
    status_by_action = {
        "reject": "申诉已驳回",
        "revoke": "违规已撤回",
    }
    status = status_by_action.get(body.get("action"), body.get("status") or "申诉已驳回")
    if status not in {"申诉已驳回", "违规已撤回", "申诉待处理"}:
        return api_response({"message": "违规处理状态不正确"}, status=400)
    Violation.objects.filter(id=violation_id).update(status=status)
    message = "管理员已撤回本次违规，相关扣分已取消" if status == "违规已撤回" else "管理员已驳回本次申诉，违规扣分维持不变"
    return api_response({"status": status, "message": message})


def parse_facilities(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in re.split(r"[，,\s]+", str(value or "")) if item.strip()]


def make_default_seats(room):
    seats = []
    for index in range(48):
        row = chr(ord("A") + index // 8)
        seat_no = f"{row}{index % 8 + 1:02d}"
        position_note = f"{row} 排 {index % 8 + 1} 号"
        seats.append(Seat(room=room, seat_no=seat_no, status="free", position_note=position_note, config="插座 / 台灯"))
    return seats
