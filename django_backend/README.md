# Django 后端

这是校园自习室预约系统的主后端实现。前端仍然请求 `/api/...`，由 Vite 代理到 Django 服务。

## 启动

在项目根目录双击：

```text
start-django-api.cmd
```

或手动执行：

```bash
cd django_backend
python manage.py runserver 127.0.0.1:3001
```

## 数据库

Django 会读取项目根目录 `.env`。连接 MySQL 时配置：

```text
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=SchoolStudyroomReservation
```

如果不设置 `DB_ENGINE=mysql`，默认使用 `django_backend/db.sqlite3`。

## Django Admin

如果只使用 Vue 前端和 `/api/...` 接口，不需要执行 Django 迁移命令。需要使用 Django 自带后台时，可以执行：

```bash
cd django_backend
python manage.py migrate --fake-initial
python manage.py createsuperuser
```

启动后访问：

```text
http://127.0.0.1:3001/admin/
```

## 已兼容接口

- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/rooms`
- `GET /api/rooms/<room_id>/seats`
- `POST /api/bookings`
- `GET /api/bookings/<user_id>`
- `PATCH /api/bookings/<booking_id>/status`
- `GET /api/violations/<user_id>`
- `PATCH /api/violations/<violation_id>/appeal`
- `GET /api/admin/stats`
- `GET /api/admin/bookings`
- `GET /api/admin/users`
- `PATCH /api/admin/users/<user_id>`
- `DELETE /api/admin/users/<user_id>`
- `GET /api/admin/violations`
- `PATCH /api/admin/violations/<violation_id>/status`
- `GET /api/admin/seats`
- `PATCH /api/admin/seats/<seat_id>/status`
- `POST /api/admin/rooms`
- `PATCH /api/admin/rooms/<room_id>`
- `DELETE /api/admin/rooms/<room_id>`

## 当前规则

- 同一座位允许在同一天的不同时段被不同用户预约。
- 只有所选时间段与已有 `pending` 或 `checked_in` 预约重叠时，才禁止预约。
- 维修座位全时段不可预约。
- 违规记录只有学生提交申诉后才进入管理员违规处理列表。
