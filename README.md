# 校园自习室预约系统

基于 Vue 3 + Vite + Django + MySQL 的校园自习室预约系统，包含学生端预约、签到签退、违规申诉，以及管理员后台的自习室、座位、预约、用户、违规和数据报表管理。

## 启动方式

以后统一使用 Django 后端。日常开发只需要启动两个脚本：

```text
start-django-api.cmd
start-dev.cmd
```

`start-django-api.cmd` 启动后端接口：

```text
http://127.0.0.1:3001/api
```

`start-dev.cmd` 启动前端页面：

```text
http://127.0.0.1:5173
```

前端会通过 Vite 代理访问 `/api`，所以后端必须先启动或保持运行。

## 安装依赖

前端依赖：

```bash
npm.cmd install
```

Django 后端依赖：

```bash
pip install -r django_backend/requirements.txt
```

## 数据库

项目使用根目录 `.env` 配置数据库连接。连接 MySQL 时建议配置：

```text
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=SchoolStudyroomReservation
```

初始化 MySQL 数据库可执行：

```bash
mysql -u root -p < database/schema.sql
```

如果不配置 `DB_ENGINE=mysql`，Django 会使用 `django_backend/db.sqlite3` 作为本地开发数据库。

## 默认账号

学生账号：

```text
20230218 / 123456
20230219 / 123456
20230220 / 123456
```

管理员账号：

```text
admin001 / admin123
admin002 / admin123
```

## 后端约定

后续后端功能统一维护在 `django_backend/booking` 中。`server/index.js` 是早期 Node 版本实现，当前不再作为默认启动方式。

当前 Django 后端已兼容前端所需的 `/api/...` 接口，包括登录注册、自习室和座位查询、按时间段预约、预约状态更新、违规申诉、管理员后台管理等。
