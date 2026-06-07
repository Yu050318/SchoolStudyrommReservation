from django.db import models


class User(models.Model):
    ROLE_CHOICES = [
        ("student", "学生"),
        ("admin", "管理员"),
    ]

    account = models.CharField(max_length=32, unique=True, verbose_name="账号")
    password = models.CharField(max_length=100, verbose_name="密码")
    name = models.CharField(max_length=40, verbose_name="姓名")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="student", verbose_name="角色")
    college = models.CharField(max_length=80, verbose_name="学院")
    class_name = models.CharField(max_length=80, verbose_name="班级")
    phone = models.CharField(max_length=30, blank=True, default="", verbose_name="联系方式")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.name} ({self.account})"


class Room(models.Model):
    id = models.CharField(max_length=40, primary_key=True, verbose_name="自习室编号")
    name = models.CharField(max_length=80, verbose_name="自习室名称")
    location = models.CharField(max_length=120, verbose_name="位置")
    open_hours = models.CharField(max_length=40, verbose_name="开放时间")
    facilities = models.JSONField(default=list, verbose_name="设施")
    sort_order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "rooms"
        ordering = ["sort_order", "id"]
        verbose_name = "自习室"
        verbose_name_plural = "自习室"

    def __str__(self):
        return self.name


class Seat(models.Model):
    STATUS_CHOICES = [
        ("free", "空闲"),
        ("used", "已占用"),
        ("booked", "已预约"),
        ("maintenance", "维修"),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column="room_id", related_name="seats")
    seat_no = models.CharField(max_length=12, verbose_name="座位号")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="free", verbose_name="状态")
    position_note = models.CharField(max_length=80, verbose_name="位置说明")
    config = models.CharField(max_length=120, verbose_name="配置")

    class Meta:
        db_table = "seats"
        constraints = [
            models.UniqueConstraint(fields=["room", "seat_no"], name="uniq_room_seat"),
        ]
        ordering = ["room__sort_order", "seat_no"]
        verbose_name = "座位"
        verbose_name_plural = "座位"

    def __str__(self):
        return f"{self.room_id} {self.seat_no}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "待签到"),
        ("checked_in", "已签到"),
        ("completed", "已签退"),
        ("canceled", "已取消"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column="room_id", related_name="bookings")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, db_column="seat_id", related_name="bookings")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "bookings"
        ordering = ["-start_time"]
        verbose_name = "预约"
        verbose_name_plural = "预约"

    def __str__(self):
        return f"{self.user.account} {self.room_id} {self.seat.seat_no}"


class Violation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="violations")
    type = models.CharField(max_length=40, verbose_name="违规类型")
    reason = models.CharField(max_length=200, verbose_name="原因")
    status = models.CharField(max_length=20, default="已处理", verbose_name="状态")
    happened_at = models.DateTimeField(verbose_name="发生时间")

    class Meta:
        db_table = "violations"
        ordering = ["-happened_at"]
        verbose_name = "违规记录"
        verbose_name_plural = "违规记录"

    def __str__(self):
        return f"{self.user.account} {self.type}"
