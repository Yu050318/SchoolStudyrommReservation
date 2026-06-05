# 校园自习室预约系统 Vue3 + MySQL

基于设计稿实现的校园自习室预约系统，前端使用 Vue3 + Vite，后端使用 Node.js API 连接 MySQL。包含登录、注册、主页、自习室列表、座位详情、我的预约、违规记录、管理员后台 8 个界面。

## 1. 安装依赖

```bash
npm.cmd install
```

如果 npm 官方源很慢，可以使用国内镜像：

```bash
npm.cmd install --registry=https://registry.npmmirror.com
```

## 2. 准备数据库

可以选择免费的云 MySQL，也可以用本地 MySQL。

推荐免费云数据库：
- Aiven for MySQL：适合直接拿到 MySQL 连接信息。
- TiDB Cloud Serverless：MySQL 协议兼容，适合课程项目和演示。

本地 MySQL 操作方式：

```bash
mysql -u root -p < database/schema.sql
```

然后复制 `.env.example` 为 `.env`，按你的数据库填写：

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=study_room_booking
DB_SSL=false
```

如果使用云数据库，可以填写云厂商提供的连接串：

```text
DATABASE_URL=mysql://用户名:密码@主机:端口/数据库名
DB_SSL=true
```

## 3. 启动后端 API

```bash
npm.cmd run server
```

后端默认地址：

```text
http://127.0.0.1:3001
```

也可以双击 `start-api.cmd`。

## 4. 启动前端

另开一个终端：

```bash
npm.cmd run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

前端会通过 Vite 代理访问 `/api`。如果后端或数据库没有启动，页面仍会进入演示模式，但会提示“数据库未连接”。

## 默认账号

```text
学生账号：
20230218 / 123456
20230219 / 123456
20230220 / 123456

管理员账号：
admin001 / admin123
admin002 / admin123
```

## 已实现

- 桌面端：左侧导航 + 顶部栏 + 内容工作区。
- 移动端：响应式布局 + 底部导航。
- 自习室搜索、列表筛选展示、座位状态图。
- 登录、注册、自习室、座位、预约、违规、管理员统计 API。
- 空闲座位选择、立即预约、签到、签退、取消，并同步数据库。
- 违规记录与管理员后台统计。
- 操作成功提示、空搜索结果提示、座位状态统计。
