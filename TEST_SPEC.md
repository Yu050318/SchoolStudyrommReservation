# 校园自习室预约系统测试规格说明书

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 文档名称 | 校园自习室预约系统测试规格说明书 |
| 适用系统 | 校园自习室预约系统 |
| 测试对象 | Vue 前端、Django 后端、数据库模型、核心业务流程 |
| 编写目的 | 为 Codex 或测试人员提供可执行、可回归的系统测试规格 |
| 当前主后端 | Django |
| 非主路径说明 | `server/index.js` 为早期 Node API 实现，不作为本规格主要测试对象 |

## 2. 系统概述

校园自习室预约系统用于支持学生注册登录、自习室浏览、座位预约、签到签退、取消预约、违规记录查询与申诉，以及管理员对自习室、座位、预约、用户、违规和运营数据的管理。

系统主要模块如下：

| 模块 | 实现位置 | 说明 |
|---|---|---|
| 前端页面 | `src/App.vue` | 登录、注册、学生端页面、管理员端页面 |
| 前端 API 工具 | `src/api.js` | 请求封装、状态文案转换 |
| Django API | `django_backend/booking/views.py` | 主后端接口与业务逻辑 |
| Django 模型 | `django_backend/booking/models.py` | 用户、房间、座位、预约、违规模型 |
| API 路由 | `django_backend/booking/urls.py` | `/api/...` 路由定义 |
| 数据库结构 | `database/schema.sql` | MySQL 建表与演示数据 |
| 演示数据命令 | `django_backend/booking/management/commands/seed_demo.py` | Django 演示数据初始化 |

## 3. 测试目标

本测试规格用于验证以下系统能力：

| 分类 | 测试目标 |
|---|---|
| 核心功能 | 验证注册、登录、自习室查询、座位查询、预约、签到、签退、取消、违规、申诉、管理员管理流程 |
| 辅助功能 | 验证 API 请求封装、状态转换、Vite 代理、localStorage 缓存、CORS |
| 边界行为 | 验证空值、缺失字段、时间边界、重复数据、非法状态、超长输入、极端数量 |
| 异常处理 | 验证非法输入、权限不足、资源不存在、网络失败、数据库异常、并发冲突 |
| 稳定性 | 验证核心业务规则在多次执行、状态切换、数据刷新后的结果一致性 |

## 4. 测试范围

### 4.1 范围内

#### 4.1.1 后端接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/health` | GET | 健康检查 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/rooms` | GET | 自习室列表 |
| `/api/rooms/<room_id>/seats` | GET | 房间座位列表 |
| `/api/bookings` | POST | 创建预约 |
| `/api/bookings/<user_id>` | GET | 用户预约列表 |
| `/api/bookings/<booking_id>/status` | PATCH | 用户更新预约状态 |
| `/api/violations/<user_id>` | GET | 用户违规记录 |
| `/api/violations/<violation_id>/appeal` | PATCH | 用户提交申诉 |
| `/api/admin/stats` | GET | 管理员统计 |
| `/api/admin/bookings` | GET | 管理员预约列表 |
| `/api/admin/bookings/<booking_id>/status` | PATCH | 管理员更新预约状态 |
| `/api/admin/users` | GET | 管理员用户列表 |
| `/api/admin/users/<user_id>` | PATCH/DELETE | 编辑或删除学生 |
| `/api/admin/violations` | GET | 待处理违规申诉 |
| `/api/admin/violations/<violation_id>/status` | PATCH | 处理违规申诉 |
| `/api/admin/seats` | GET | 管理员座位列表 |
| `/api/admin/seats/<seat_id>/status` | PATCH | 更新座位状态 |
| `/api/admin/rooms` | POST | 新增自习室 |
| `/api/admin/rooms/<room_id>` | PATCH/DELETE | 编辑或删除自习室 |

#### 4.1.2 前端页面

- 登录页
- 注册页
- 主页
- 自习室列表页
- 座位详情页
- 我的预约页
- 违规记录页
- 管理员后台总览
- 自习室管理页
- 座位管理页
- 预约管理页
- 用户管理页
- 违规处理页
- 数据报表页

#### 4.1.3 数据模型

- `User`
- `Room`
- `Seat`
- `Booking`
- `Violation`

### 4.2 范围外

| 内容 | 原因 |
|---|---|
| 生产部署安全加固 | 当前规格聚焦功能和业务逻辑 |
| 数据库备份恢复 | 不属于本系统应用层测试 |
| 第三方服务异常 | 当前代码未集成第三方服务 |
| Node API 完整测试 | README 说明当前统一使用 Django 后端 |
| 完整权限鉴权测试 | 当前系统未实现 Token/Session 鉴权 |

## 5. 业务规则规格

### 5.1 用户与角色

- 用户角色包括 `student` 和 `admin`。
- 登录时如果请求中提供 `role`，账号必须匹配对应角色。
- 注册接口创建的用户默认角色为 `student`。
- 账号字段唯一。

### 5.2 自习室与座位

- 自习室包含编号、名称、位置、开放时间、设施和排序字段。
- 座位状态包括 `free`、`used`、`booked`、`maintenance`。
- 查询自习室时应统计：
  - `free`：空闲座位数。
  - `used`：`used` 与 `booked` 的合计。
  - `maintenance`：维修座位数。
- 查询座位时：
  - 维修座位固定显示 `maintenance`。
  - 时间段内存在 `checked_in` 预约时显示 `used`。
  - 时间段内存在 `pending` 预约时显示 `booked`。
  - 无冲突预约时显示 `free`。

### 5.3 预约

- 创建预约必须提供 `userId`、`roomId`、`seatNo`、`startTime`、`endTime`。
- `startTime` 必须早于 `endTime`。
- 维修座位不可预约。
- 同一座位的 `pending` 或 `checked_in` 预约时间段不可重叠。
- 相邻时间段不算冲突。
- 创建成功后预约状态为 `pending`。

### 5.4 状态与违规

允许的预约状态：

- `pending`
- `checked_in`
- `completed`
- `canceled`

中文状态映射：

| 英文状态 | 中文含义 |
|---|---|
| `pending` | 待签到 |
| `checked_in` | 已签到 |
| `completed` | 已签退 |
| `canceled` | 已取消 |

迟到签到扣分规则：

| 条件 | 违规类型 | 扣分 |
|---|---|---|
| 迟到 > 5 分钟且 <= 15 分钟 | 轻微迟到 | -2 |
| 迟到 > 15 分钟且 <= 30 分钟 | 迟到签到 | -5 |
| 迟到 > 30 分钟 | 严重迟到 | -8 |

取消预约扣分规则：

| 条件 | 违规类型 | 扣分 |
|---|---|---|
| 开始后取消 | 开始后取消 | -8 |
| 开始前 <= 10 分钟取消 | 取消超时 | -5 |
| 开始前 <= 30 分钟取消 | 临近取消 | -3 |
| 开始前 > 30 分钟取消 | 无违规 | 0 |

### 5.5 违规申诉

- 申诉理由不能为空。
- 用户只能申诉自己的违规记录。
- 已撤回违规不可再次申诉。
- 已处于申诉待处理状态时，重复提交应返回待处理提示。
- 管理员可驳回申诉或撤回违规。
- 已撤回违规不再计入扣分。

### 5.6 管理员管理

- 新增自习室时自动生成 48 个默认座位。
- 有预约记录的自习室不可删除。
- 有预约或违规记录的学生不可删除。
- 管理员可更新座位状态。
- 管理员用户列表应计算预约次数、信用分、信用状态。

## 6. 测试环境规格

### 6.1 推荐环境

| 项目 | 规格 |
|---|---|
| 操作系统 | Windows |
| 前端运行环境 | Node.js + npm |
| 后端运行环境 | Python + Django |
| 默认数据库 | SQLite |
| 可选数据库 | MySQL |
| 前端端口 | `5173` |
| 后端端口 | `3001` |

### 6.2 启动命令

后端：

```bash
start-django-api.cmd
```

前端：

```bash
start-dev.cmd
```

后端 API：

```text
http://127.0.0.1:3001/api
```

前端页面：

```text
http://127.0.0.1:5173
```

## 7. 测试数据规格

### 7.1 默认账号

| 类型 | 账号 | 密码 |
|---|---|---|
| 学生 | `20230218` | `123456` |
| 学生 | `20230219` | `123456` |
| 学生 | `20230220` | `123456` |
| 管理员 | `admin001` | `admin123` |
| 管理员 | `admin002` | `admin123` |

### 7.2 推荐构造数据

- 至少 2 个学生用户。
- 至少 1 个管理员用户。
- 至少 2 个自习室。
- 每个自习室至少包含：
  - 空闲座位。
  - 已占用座位。
  - 已预约座位。
  - 维修座位。
- 至少包含以下预约：
  - `pending`
  - `checked_in`
  - `completed`
  - `canceled`
- 至少包含以下违规：
  - 未申诉。
  - 申诉待处理。
  - 申诉已驳回。
  - 违规已撤回。

## 8. 测试用例规格

| 用例编号 | 测试类型 | 测试目标 | 前置条件 | 测试步骤 | 输入数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|
| TC-001 | API-功能 | 健康检查 | Django 服务启动 | GET `/api/health` | 无 | 返回 200，`ok=true` | P0 |
| TC-002 | API-功能 | 学生登录成功 | 存在学生账号 | POST `/api/auth/login` | `20230218/123456/student` | 返回 user，role 为 student | P0 |
| TC-003 | API-异常 | 密码错误 | 存在账号 | POST 登录 | 错误密码 | 返回 401 | P0 |
| TC-004 | API-权限 | 角色不匹配登录 | 学生账号存在 | 用 admin role 登录学生账号 | `role=admin` | 返回 401 | P0 |
| TC-005 | API-功能 | 注册成功 | 账号不存在 | POST `/api/auth/register` | 完整学生信息 | 返回 201，新用户 role=student | P0 |
| TC-006 | API-边界 | 注册缺失字段 | 无 | 缺少 phone/email | 空联系方式 | 返回 400 | P0 |
| TC-007 | API-异常 | 重复注册 | 账号已存在 | POST 注册 | 已存在 account | 返回 409 | P0 |
| TC-008 | API-功能 | 查询自习室列表 | 已 seed 数据 | GET `/api/rooms` | 无 | 返回 rooms，座位统计正确 | P0 |
| TC-009 | API-功能 | 查询座位状态 | 有 pending/checked_in 预约 | GET `/api/rooms/{id}/seats` | 指定时间段 | pending 显示 booked，checked_in 显示 used | P0 |
| TC-010 | API-边界 | 相邻时间段不冲突 | 有 10:00-12:00 预约 | 创建 12:00-13:00 | 同座位相邻 | 返回 201 | P0 |
| TC-011 | API-边界 | 部分重叠冲突 | 有 10:00-12:00 预约 | 创建 11:00-13:00 | 同座位重叠 | 返回 409 | P0 |
| TC-012 | API-边界 | 包含式重叠冲突 | 有 10:00-12:00 预约 | 创建 09:00-13:00 | 同座位包含 | 返回 409 | P0 |
| TC-013 | API-异常 | 维修座位不可预约 | 座位 status=maintenance | POST `/api/bookings` | 维修座位 | 返回 409 | P0 |
| TC-014 | API-异常 | 不存在座位 | 无该座位 | POST `/api/bookings` | `seatNo=Z99` | 返回 404 | P0 |
| TC-015 | API-边界 | 开始等于结束 | 无 | POST 预约 | `startTime=endTime` | 返回 400 | P0 |
| TC-016 | API-功能 | 用户预约列表 | 用户有预约 | GET `/api/bookings/{userId}` | userId | 返回预约，状态为中文文案 | P0 |
| TC-017 | API-功能 | 签到状态更新 | 有 pending 预约 | PATCH status | `checked_in` 或 `已签到` | 返回已签到 | P0 |
| TC-018 | API-业务 | 迟到 6 分钟生成轻微违规 | 构造开始时间 | PATCH checked_in | 开始时间为 now-6min | 生成扣 2 违规 | P1 |
| TC-019 | API-业务 | 迟到 16 分钟生成迟到违规 | 构造开始时间 | PATCH checked_in | now-16min | 生成扣 5 违规 | P1 |
| TC-020 | API-业务 | 迟到 31 分钟生成严重迟到 | 构造开始时间 | PATCH checked_in | now-31min | 生成扣 8 违规 | P1 |
| TC-021 | API-业务 | 提前 31 分钟取消不扣分 | 有 pending 预约 | PATCH canceled | start=now+31min | 无违规 | P1 |
| TC-022 | API-业务 | 提前 30 分钟取消扣 3 | 有 pending 预约 | PATCH canceled | start=now+30min | 生成扣 3 违规 | P1 |
| TC-023 | API-业务 | 提前 10 分钟取消扣 5 | 有 pending 预约 | PATCH canceled | start=now+10min | 生成扣 5 违规 | P1 |
| TC-024 | API-业务 | 开始后取消扣 8 | 有 pending 预约 | PATCH canceled | start=now-1min | 生成扣 8 违规 | P1 |
| TC-025 | API-异常 | 非法预约状态 | 有预约 | PATCH status | `unknown` | 返回 400 | P0 |
| TC-026 | API-功能 | 查询违规记录 | 用户有违规 | GET `/api/violations/{userId}` | userId | 返回扣分、状态、申诉理由拆分 | P1 |
| TC-027 | API-功能 | 提交申诉 | 有未申诉违规 | PATCH appeal | userId + reason | 状态变为申诉待处理 | P0 |
| TC-028 | API-边界 | 空申诉理由 | 有违规 | PATCH appeal | 空 reason | 返回 400 | P0 |
| TC-029 | API-权限 | 申诉他人违规 | 有他人违规 | PATCH appeal | 错误 userId | 返回 404 | P0 |
| TC-030 | API-功能 | 管理员统计 | 有基础数据 | GET `/api/admin/stats` | 无 | 返回今日预约、签到率、空闲座位、待处理违规 | P1 |
| TC-031 | API-功能 | 管理员预约列表 | 有预约 | GET `/api/admin/bookings` | 无 | 返回用户、房间、座位、时间、状态 | P1 |
| TC-032 | API-功能 | 管理员用户列表信用计算 | 有违规 | GET `/api/admin/users` | 无 | credit=100+违规扣分，撤回违规不扣分 | P0 |
| TC-033 | API-功能 | 管理员编辑学生 | 学生存在 | PATCH `/api/admin/users/{id}` | 姓名学院班级电话 | 返回更新后用户 | P1 |
| TC-034 | API-异常 | 删除有关联记录学生 | 学生有预约或违规 | DELETE 用户 | userId | 返回 409 | P0 |
| TC-035 | API-功能 | 新增自习室 | roomId 不存在 | POST `/api/admin/rooms` | 合法房间信息 | 返回 201，并创建 48 个座位 | P0 |
| TC-036 | API-边界 | 非法房间编号 | 无 | POST room | `中文 空格 !` | 返回 400 | P0 |
| TC-037 | API-异常 | 重复房间编号 | roomId 已存在 | POST room | 重复 id | 返回 409 | P0 |
| TC-038 | API-功能 | 编辑自习室 | 房间存在 | PATCH room | 新名称/位置/时间/设施 | 返回更新后的 room | P1 |
| TC-039 | API-异常 | 删除有预约房间 | 房间有关联 booking | DELETE room | roomId | 返回 409 | P0 |
| TC-040 | API-功能 | 更新座位维修状态 | 座位存在 | PATCH seat status | `maintenance/free` | 返回状态并持久化 | P1 |
| TC-041 | API-异常 | 非法座位状态 | 座位存在 | PATCH seat status | `broken` | 返回 400 | P0 |
| TC-042 | API-功能 | 管理员处理申诉-驳回 | 有待处理申诉 | PATCH violation status | `action=reject` | 状态为驳回，扣分保留 | P1 |
| TC-043 | API-功能 | 管理员处理申诉-撤回 | 有待处理申诉 | PATCH violation status | `action=revoke` | 状态为撤回，信用分恢复 | P1 |
| TC-044 | 前端-功能 | 登录成功进入主页 | API 可用 | 填学生账号登录 | 正确账号密码 | 显示学生导航和主页数据 | P0 |
| TC-045 | 前端-功能 | 管理员登录进入后台 | API 可用 | 切换管理员登录 | admin001/admin123 | 显示管理员导航 | P0 |
| TC-046 | 前端-功能 | 注册后自动进入系统 | API 可用 | 填写注册表单 | 新学号 | 进入系统，localStorage 保存用户 | P1 |
| TC-047 | 前端-异常 | API 不可用降级 | 停止后端 | 打开页面并加载 | 无 | 页面不崩，显示演示数据和错误提示 | P1 |
| TC-048 | 前端-功能 | 预约座位页面链路 | API 可用 | 自习室列表进入座位详情并预约 | 空闲座位 | 新预约显示在我的预约 | P0 |
| TC-049 | 前端-功能 | 签到/签退按钮状态 | 有 active booking | 点击签到再签退 | 无 | 状态依次变为已签到、已签退 | P0 |
| TC-050 | 前端-功能 | 违规申诉弹窗 | 有可申诉违规 | 打开弹窗提交理由 | 预设或自定义理由 | 列表状态更新为待处理 | P1 |
| TC-051 | 前端-功能 | 管理员房间增删改 | 管理员登录 | 新增、编辑、删除房间 | 合法房间 | 页面和后端一致 | P1 |
| TC-052 | 前端-功能 | 管理员座位维修切换 | 管理员登录 | 点击设为维修/恢复空闲 | 座位卡片 | 状态更新并刷新 | P1 |
| TC-053 | 前端-功能 | 管理员违规处理 | 有待处理申诉 | 点击驳回/撤回 | action | 列表移除或状态更新 | P1 |
| TC-054 | 工具函数 | 状态转换 | 无 | 调用 `normalizeStatus/toApiBookingStatus` | 英文、中文、未知状态 | 已知状态正确转换，未知原样返回 | P1 |
| TC-055 | 中间件 | CORS 预检 | 服务启动 | OPTIONS `/api/health` | 无 | 204，包含 CORS 头 | P1 |

## 9. 自动化测试规格

### 9.1 后端测试

推荐使用 Django 内置测试框架。

建议新增文件：

```text
django_backend/booking/tests/
  __init__.py
  test_auth_api.py
  test_rooms_and_seats_api.py
  test_bookings_api.py
  test_violations_api.py
  test_admin_api.py
  test_seed_demo.py
```

建议执行命令：

```bash
cd django_backend
python manage.py test booking
```

### 9.2 前端单元测试

推荐使用 Vitest。

建议新增文件：

```text
src/api.test.js
```

建议新增依赖：

```bash
npm install -D vitest @vue/test-utils jsdom
```

建议新增脚本：

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

建议执行命令：

```bash
npm run test
```

### 9.3 前端 E2E 测试

推荐使用 Playwright。

建议新增文件：

```text
e2e/
  auth.spec.js
  booking-flow.spec.js
  admin-flow.spec.js
```

建议执行命令：

```bash
npx playwright test
```

### 9.4 构建验证

每次提交前建议执行：

```bash
npm run build
```

## 10. 回归测试规格

### 10.1 每次提交必须回归

- TC-001 到 TC-017。
- TC-025。
- TC-027 到 TC-029。
- TC-032。
- TC-035。
- TC-044、TC-045、TC-048、TC-049。

### 10.2 发版前必须回归

- 所有 P0 用例。
- 所有 P1 API 用例。
- 前端学生主流程。
- 前端管理员主流程。
- API 不可用时的降级流程。

### 10.3 人工回归

- 页面视觉一致性。
- 移动端布局。
- toast 文案清晰度。
- 管理员报表展示。
- 演示数据模式体验。

## 11. 风险与缺陷观察项

| 风险 | 说明 | 建议 |
|---|---|---|
| 管理员接口未鉴权 | 当前 `/api/admin/...` 可被直接访问 | 后续增加 Token 或 Session 鉴权 |
| 密码明文存储 | 当前模型和种子数据均为明文密码 | 后续接入 Django 密码哈希 |
| 状态流转限制不足 | 当前接口允许直接设置任意合法状态 | 后续增加状态机校验 |
| 中文编码显示异常 | 部分源码和 README 存在乱码 | 测试断言优先基于结构和业务状态 |
| 前端演示数据兜底 | API 失败时页面可能仍显示旧数据 | E2E 需区分真实数据和演示数据 |
| Node API 与 Django API 并存 | 可能造成维护混淆 | 明确 Django 为唯一主后端 |

## 12. 建议实施顺序

1. 编写 Django API 基础测试：健康检查、登录、注册。
2. 编写自习室和座位查询测试。
3. 编写预约创建、冲突判断、维修座位、时间边界测试。
4. 编写状态更新和违规扣分边界测试。
5. 编写申诉和管理员违规处理测试。
6. 编写管理员用户、自习室、座位管理测试。
7. 编写 `seed_demo` 测试。
8. 编写 `src/api.js` 工具函数测试。
9. 执行前端构建验证。
10. 执行学生端 E2E。
11. 执行管理员端 E2E。
12. 将 P0 用例纳入日常回归，将 P1 用例纳入发版前回归。
