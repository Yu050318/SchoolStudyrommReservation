# Django 后端方案

这是对现有校园自习室预约系统的 Django 后端优化版本，保持现有 Vue 前端接口路径不变：

- 前端仍然请求 `/api/...`
- 数据表沿用 `database/schema.sql` 中的 `users / rooms / seats / bookings / violations`
- Django Admin 可用于后台数据维护
- 当前 Node 后端仍保留，不影响原有功能

## 本地启动

```bash
cd django_backend
python manage.py runserver 127.0.0.1:3001
```

然后继续使用原来的前端：

```bash
npm run dev
```

## 连接 MySQL

安装依赖：

```bash
pip install -r django_backend/requirements.txt
```

在项目根目录 `.env` 中加入：

```text
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=SchoolStudyroomReservation
```

如果不设置 `DB_ENGINE=mysql`，Django 默认使用 `django_backend/db.sqlite3`，方便做代码自检和开发实验。

当前项目根目录 `.env` 已配置为连接原来的 MySQL 数据库：

```text
DB_ENGINE=mysql
DB_NAME=SchoolStudyroomReservation
```

Django 模型已按当前原库实际表结构适配。信用分不依赖额外字段，而是根据 `violations.type` 动态计算。

## Django Admin

如果只使用 Vue 前端和 `/api/...` 接口，不需要执行 Django 迁移命令。

首次使用 Django 自带后台时，可以创建管理员账号：

```bash
cd django_backend
python manage.py migrate --fake-initial
python manage.py createsuperuser
```

启动后访问：

```text
http://127.0.0.1:3001/admin/
```

## 已兼容的 API

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
