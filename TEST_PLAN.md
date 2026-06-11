# 校园自习室预约系统测试计划

## 一、项目理解

当前系统是一个校园自习室预约系统，主要由以下部分组成：

- 前端：Vue 3 + Vite，核心文件为 `src/App.vue` 和 `src/api.js`。
- 主后端：Django，核心实现位于 `django_backend/booking`。
- 数据层：支持 SQLite 本地开发，也可通过 `.env` 配置 MySQL；表结构参考 `database/schema.sql`。
- 早期后端：`server/index.js` 为 Node 版本实现，README 中说明当前不再作为默认后端。

本测试计划优先覆盖 Django 后端、Vue 前端主流程、API 数据流、核心业务规则和异常边界。

重点代码文件：

- `django_backend/booking/views.py`
- `django_backend/booking/models.py`
- `django_backend/booking/urls.py`
- `django_backend/booking/management/commands/seed_demo.py`
- `src/App.vue`
- `src/api.js`
- `database/schema.sql`

## 二、测试目标

### 2.1 核心功能

- 验证学生注册、学生登录、管理员登录、角色区分是否正确。
- 验证自习室列表、座位状态、预约创建、预约查询、签到、签退、取消预约等主流程。
- 验证预约冲突判断、维修座位不可预约、状态更新、违规生成和信用分计算。
- 验证违规记录查询、学生申诉、管理员驳回申诉、管理员撤回违规。
- 验证管理员端统计、自习室管理、座位管理、预约管理、用户管理、违规处理等功能。

### 2.2 辅助功能

- 验证 `apiRequest` 对请求体、响应体、错误状态的处理。
- 验证 `normalizeStatus` 和 `toApiBookingStatus` 的状态映射。
- 验证 Vite `/api` 代理到 Django API。
- 验证 localStorage 中登录缓存、注册用户缓存、损坏缓存兜底逻辑。

### 2.3 异常处理

- 验证非法输入、缺失字段、非法状态、资源不存在、重复数据、预约冲突等错误响应。
- 验证接口不可用、数据库异常、返回非 JSON 数据时前端是否保持可用。
- 验证错误提示、toast 提示、页面降级展示是否合理。

### 2.4 边界行为

- 验证预约时间边界、时间段重叠边界、迟到扣分边界、取消扣分边界。
- 验证空字符串、超长字符串、特殊字符、重复账号、重复房间编号等输入。
- 验证空数据、大量数据、筛选无结果、默认新增房间 48 个座位等场景。

## 三、测试范围

### 3.1 纳入范围

#### 后端 API

- `GET /api/health`
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
- `PATCH /api/admin/bookings/<booking_id>/status`
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

#### 数据模型

- `User`
- `Room`
- `Seat`
- `Booking`
- `Violation`

#### 前端页面

- 登录页
- 注册页
- 主页
- 自习室列表页
- 座位详情页
- 我的预约页
- 违规记录页
- 管理员后台总览
- 自习室管理
- 座位管理
- 预约管理
- 用户管理
- 违规处理
- 数据报表

#### 工具与配置

- `src/api.js`
- `vite.config.js`
- `booking.middleware.ApiCorsMiddleware`
- `seed_demo` 管理命令

### 3.2 不纳入范围

- `server/index.js` 不作为主验证对象，仅建议保留兼容性冒烟测试。
- 真实生产部署、HTTPS、备份恢复、数据库运维不纳入本次测试。
- 密码加密、Token、Session、细粒度鉴权不作为已有能力测试，因为当前实现未提供完整鉴权机制。
- 第三方服务异常不作为重点，因为项目当前未集成外部第三方接口。

### 3.3 假设

- 当前主后端为 Django。
- 测试环境可使用 SQLite，以降低 MySQL 依赖。
- 如果使用 MySQL，需提前执行 `database/schema.sql` 或 Django migration，并准备测试数据。
- 前端允许在 API 不可用时显示演示数据。

## 四、功能逻辑测试

### 4.1 认证与注册

- 学生使用正确账号、密码、角色登录成功。
- 管理员使用正确账号、密码、角色登录成功。
- 学生账号使用管理员角色登录失败。
- 错误密码登录失败。
- 注册时必填字段完整，账号不存在时创建学生账号。
- 注册后用户默认角色为 `student`。
- 重复账号注册返回冲突错误。

### 4.2 自习室与座位

- 查询自习室列表时返回房间编号、名称、位置、开放时间、设施、座位统计。
- 座位统计中 `free`、`used/booked`、`maintenance` 计算正确。
- 查询座位时，维修座位显示 `maintenance`。
- 存在 `checked_in` 预约的座位显示 `used`。
- 存在 `pending` 预约的座位显示 `booked`。
- 时间段不冲突时座位显示为空闲。
- 房间不存在时返回空座位列表或合理响应。

### 4.3 预约流程

- 用户选择自习室、座位、开始时间、结束时间后可创建预约。
- 创建成功后状态为 `pending`，前端显示“待签到”。
- 查询用户预约列表时返回日期、房间、座位、时间、中文状态。
- 同一座位相邻时间段不冲突。
- 同一座位部分重叠、完全重叠、包含式重叠均应冲突。
- 维修座位不可预约。
- 不存在座位不可预约。
- 开始时间必须早于结束时间。

### 4.4 状态流转与违规生成

- 预约可从待签到更新为已签到。
- 已签到预约可更新为已签退。
- 待签到预约可取消。
- 非法状态返回错误。
- 当前实现未限制状态跳转顺序，应通过测试记录该行为。
- 签到迟到超过 5 分钟、15 分钟、30 分钟分别生成不同扣分违规。
- 取消预约在开始后、开始前 10 分钟内、开始前 30 分钟内生成不同扣分违规。
- 违规生成应与状态更新处于同一事务中。

### 4.5 违规与申诉

- 用户可查询自己的违规记录。
- 信用分根据违规类型扣分。
- 已撤回的违规扣分为 0。
- 申诉理由为空时拒绝提交。
- 用户只能申诉自己的违规。
- 未申诉违规提交后状态变为“申诉待处理”。
- 已经处于待处理状态的申诉重复提交时返回幂等提示。
- 已撤回违规不可再次申诉。

### 4.6 管理员功能

- 统计接口返回今日预约数、签到率、空闲座位数、待处理违规数。
- 管理员可查看全部预约。
- 管理员可更新预约状态。
- 管理员可查看学生列表，并看到预约次数、信用分、信用状态。
- 管理员可编辑学生姓名、学院、班级、联系方式和密码。
- 有预约或违规关联的学生不可删除。
- 管理员可新增自习室，系统自动生成 48 个默认座位。
- 管理员可编辑自习室信息。
- 有预约关联的自习室不可删除。
- 管理员可将座位设为维修或恢复空闲。
- 管理员可驳回申诉或撤回违规。

### 4.7 前端交互

- 登录成功后进入对应角色首页。
- 学生导航不显示管理员菜单。
- 管理员登录后显示管理员导航。
- 自习室列表筛选和搜索正常。
- 座位详情中不同状态座位显示样式正确。
- 预约成功后“我的预约”出现新记录。
- 签到、签退、取消按钮根据当前状态显示。
- 申诉弹窗提交后列表状态更新。
- 管理员编辑、删除、处理操作后刷新数据。
- API 不可用时使用演示数据，并显示错误提示。

## 五、边界测试

### 5.1 字符串边界

- 空账号、空密码、空姓名、空学院、空班级、空联系方式。
- 超长账号、超长姓名、超长房间名称、超长设施字段。
- 房间编号包含中文、空格、特殊符号。
- 房间编号仅包含字母、数字、下划线、短横线。
- 设施字段传数组。
- 设施字段传空格或分隔符组成的字符串。

### 5.2 时间边界

- `startTime == endTime`。
- `startTime > endTime`。
- 预约时间刚好相邻，不应冲突。
- 预约时间开始重叠、结束重叠、完全包含、被包含。
- 迟到 5、6、15、16、30、31 分钟。
- 取消预约距离开始 31、30、10、9、0、-1 分钟。

### 5.3 数值与数量边界

- 空自习室列表。
- 自习室存在但座位数为 0。
- 新增房间默认 48 个座位。
- 大量用户、大量预约、大量违规记录。
- 信用分低于 0 时前端应钳制到合理范围，后端用户列表当前使用 `max(0, 100 + score_delta)`。

### 5.4 对象与数组边界

- 请求体为空对象。
- 请求体缺少部分字段。
- `facilities` 为数组、字符串、空字符串、非法类型。
- localStorage 中保存的数据不是 JSON。
- localStorage 中注册用户缓存不是数组。

### 5.5 网络与响应边界

- API 服务未启动。
- API 返回 500。
- API 返回非 JSON 响应。
- OPTIONS 预检请求。
- 后端数据库不可用。

## 六、异常与错误处理测试

应重点验证以下错误场景：

- 400：注册信息缺失、预约字段缺失、非法时间段、非法预约状态、非法座位状态、非法房间编号、空申诉理由。
- 401：账号、密码或角色错误。
- 404：预约不存在、座位不存在、学生不存在、违规不存在、自习室不存在。
- 405：接口方法不支持。
- 409：重复账号、重复房间、预约冲突、维修座位预约、有关联数据的学生或房间删除。
- 500：数据库异常、JSON 解析异常、未知服务端异常。

前端应验证：

- 错误时显示清晰 toast。
- 页面不白屏。
- 已加载数据不被意外清空。
- 可回退到演示数据或当前页面数据。
- 写操作失败时不会误导用户认为已持久化，或应明确提示“接口暂不可用，已先更新页面展示”。

## 七、回归测试建议

### 7.1 优先保留为自动化回归的用例

- 登录成功和失败。
- 注册成功、缺失字段、重复注册。
- 自习室列表和座位状态查询。
- 创建预约成功。
- 预约冲突判断。
- 维修座位不可预约。
- 签到、签退、取消状态更新。
- 迟到和取消违规扣分边界。
- 申诉提交和管理员处理。
- 管理员用户信用计算。
- 管理员新增房间生成 48 个座位。
- 用户和房间删除保护。
- `apiRequest` 和状态映射函数。

### 7.2 适合自动化的测试

- Django API 单元测试和集成测试。
- Django 模型及业务函数测试。
- 前端工具函数单测。
- 关键前端 E2E 流程。
- CORS 和 OPTIONS 请求。

### 7.3 需要人工验证的测试

- 页面视觉效果。
- 移动端响应式体验。
- toast 文案是否清晰。
- 管理员报表的业务含义是否符合课程设计要求。
- 离线演示数据降级体验是否符合预期。

## 八、测试用例清单

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

## 九、Codex 执行建议

### 9.1 后端测试框架

项目当前没有发现已有测试文件。后端建议优先使用 Django 内置测试框架，避免引入额外依赖。

建议新增目录：

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

### 9.2 前端测试框架

项目当前没有前端测试依赖。若允许新增依赖，建议使用 Vitest。

建议新增：

```text
src/api.test.js
```

建议安装：

```bash
npm install -D vitest @vue/test-utils jsdom
```

建议在 `package.json` 增加：

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

建议执行：

```bash
npm run test
```

### 9.3 E2E 测试

如果需要自动化浏览器验证，建议使用 Playwright。

建议目录：

```text
e2e/
  auth.spec.js
  booking-flow.spec.js
  admin-flow.spec.js
```

建议执行：

```bash
npx playwright test
```

### 9.4 构建与联调命令

构建检查：

```bash
npm run build
```

本地启动：

```bash
start-django-api.cmd
start-dev.cmd
```

API 地址：

```text
http://127.0.0.1:3001/api
```

前端地址：

```text
http://127.0.0.1:5173
```

## 十、建议实施顺序

1. 新增 Django API 测试，先覆盖认证、注册、自习室、座位、预约创建。
2. 补充预约冲突、时间边界、状态更新、违规扣分测试。
3. 补充申诉和管理员违规处理测试。
4. 补充管理员用户、房间、座位管理测试。
5. 补充 `seed_demo` 数据初始化测试。
6. 新增 `src/api.js` 工具函数单元测试。
7. 执行 `npm run build` 验证前端构建。
8. 使用浏览器或 Playwright 执行学生主流程 E2E。
9. 执行管理员主流程 E2E。
10. 将 P0 用例纳入每次回归，将 P1 用例纳入发版前回归。

## 十一、风险与备注

- 当前 Django 接口未实现真正的登录态或 Token 鉴权，管理员接口可被直接调用。测试时应记录为安全风险，而不是把它误判为测试失败。
- 当前项目存在中文编码显示异常的文件内容，测试断言应优先基于状态码、字段结构、业务状态码或内部英文状态，不宜过度依赖乱码文案。
- 前端包含演示数据兜底逻辑，E2E 测试应区分“API 在线真实数据模式”和“API 离线演示数据模式”。
- `server/index.js` 与 Django 后端存在相似逻辑但不是当前主路径，除非后续重新启用 Node API，否则不建议投入大量测试成本。
