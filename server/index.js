import { execFile } from 'node:child_process'
import { readFileSync } from 'node:fs'
import http from 'node:http'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const env = loadEnv()
const port = Number(env.API_PORT || 3001)
const mysqlBin = env.MYSQL_BIN || 'mysql'

function loadEnv() {
  try {
    const content = readFileSync('.env', 'utf8')
    return Object.fromEntries(
      content
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line && !line.startsWith('#'))
        .map((line) => {
          const index = line.indexOf('=')
          return [line.slice(0, index), line.slice(index + 1)]
        }),
    )
  } catch {
    return {}
  }
}

function sqlValue(value) {
  if (value === null || value === undefined || value === '') return 'null'
  return `'${String(value).replace(/\\/g, '\\\\').replace(/'/g, "''")}'`
}

async function mysqlExec(sql, { parseRows = false } = {}) {
  const args = [
    '-h',
    env.DB_HOST || 'localhost',
    '-P',
    String(env.DB_PORT || 3306),
    '-u',
    env.DB_USER || 'root',
    `-p${env.DB_PASSWORD || ''}`,
    '--default-character-set=utf8mb4',
    '--batch',
    '--raw',
    '-D',
    env.DB_NAME || 'SchoolStudyroomReservation',
    '-e',
    sql,
  ]

  const { stdout } = await execFileAsync(mysqlBin, args, {
    maxBuffer: 1024 * 1024 * 8,
    windowsHide: true,
  })

  if (!parseRows) return []
  return parseMysqlRows(stdout)
}

function parseMysqlRows(stdout) {
  const lines = stdout.trim().split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) return []

  const headers = lines[0].split('\t')
  return lines.slice(1).map((line) => {
    const values = line.split('\t')
    return Object.fromEntries(headers.map((header, index) => [header, values[index] === 'NULL' ? null : values[index]]))
  })
}

function toPublicUser(row) {
  return {
    id: Number(row.id),
    account: row.account,
    name: row.name,
    role: row.role,
    college: row.college,
    className: row.class_name,
    phone: row.phone,
  }
}

function bookingStatusToCn(status) {
  return {
    pending: '待签到',
    checked_in: '已签到',
    completed: '已签退',
    canceled: '已取消',
  }[status] || status
}

function userCreditState(score) {
  if (score >= 70) return '正常'
  if (score >= 60) return '预警'
  if (score >= 40) return '限制'
  return '冻结'
}

async function updateBookingStatus(bookingId, status) {
  const allowed = new Set(['pending', 'checked_in', 'completed', 'canceled'])
  if (!allowed.has(status)) {
    return { error: { statusCode: 400, message: '预约状态不正确' } }
  }

  const rows = await mysqlExec(
    `select
      seat_id,
      user_id,
      timestampdiff(minute, start_time, now()) as minutesLate,
      timestampdiff(minute, now(), start_time) as minutesBefore
     from bookings
     where id = ${sqlValue(bookingId)}`,
    { parseRows: true },
  )
  if (rows.length === 0) {
    return { error: { statusCode: 404, message: '预约记录不存在' } }
  }

  const violation = getCreditViolation(
    status,
    Number(rows[0].minutesLate || 0),
    Number(rows[0].minutesBefore || 0),
  )
  const violationSql = violation
    ? `insert into violations (user_id, type, reason, status, happened_at)
       values (${sqlValue(rows[0].user_id)}, ${sqlValue(violation.type)}, ${sqlValue(violation.reason)},
       '未申诉', now());`
    : ''
  await mysqlExec(
    `start transaction;
     update bookings set status = ${sqlValue(status)} where id = ${sqlValue(bookingId)};
     ${violationSql}
     commit;`,
  )
  return { status: bookingStatusToCn(status), violation }
}

function violationScoreCase() {
  return `case
    when status = '违规已撤回' then 0
    when type = '爽约' then -12
    when type = '开始后取消' then -8
    when type = '严重迟到' then -8
    when type = '占座超时' then -6
    when type = '取消超时' then -5
    when type = '迟到签到' then -5
    when type = '临近取消' then -3
    when type = '轻微迟到' then -2
    else 0
  end`
}

function splitAppealReason(row) {
  const delimiter = '\n申诉理由：'
  const reason = String(row.reason || '')
  const [baseReason, ...appealParts] = reason.split(delimiter)
  return {
    ...row,
    reason: baseReason,
    appealReason: appealParts.join(delimiter).trim(),
  }
}

function getCreditViolation(status, minutesLate, minutesBefore) {
  if (status === 'checked_in') {
    if (minutesLate > 30) {
      return { type: '严重迟到', reason: `预约开始后 ${minutesLate} 分钟签到`, scoreChange: -8 }
    }
    if (minutesLate > 15) {
      return { type: '迟到签到', reason: `预约开始后 ${minutesLate} 分钟签到`, scoreChange: -5 }
    }
    if (minutesLate > 5) {
      return { type: '轻微迟到', reason: `预约开始后 ${minutesLate} 分钟签到`, scoreChange: -2 }
    }
  }

  if (status === 'canceled') {
    if (minutesBefore < 0) {
      return { type: '开始后取消', reason: '预约开始后取消预约', scoreChange: -8 }
    }
    if (minutesBefore <= 10) {
      return { type: '取消超时', reason: `开始前 ${minutesBefore} 分钟取消预约`, scoreChange: -5 }
    }
    if (minutesBefore <= 30) {
      return { type: '临近取消', reason: `开始前 ${minutesBefore} 分钟取消预约`, scoreChange: -3 }
    }
  }

  return null
}

async function readBody(req) {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  const text = Buffer.concat(chunks).toString('utf8')
  return text ? JSON.parse(text) : {}
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  })
  res.end(JSON.stringify(payload))
}

function notFound(res) {
  sendJson(res, 404, { message: '接口不存在' })
}

async function handleRequest(req, res) {
  if (req.method === 'OPTIONS') {
    sendJson(res, 204, {})
    return
  }

  const url = new URL(req.url, `http://${req.headers.host}`)
  const path = url.pathname

  try {
    if (req.method === 'GET' && path === '/api/health') {
      const rows = await mysqlExec('select 1 as ok', { parseRows: true })
      sendJson(res, 200, { ok: rows[0]?.ok === '1' })
      return
    }

    if (req.method === 'POST' && path === '/api/auth/login') {
      const body = await readBody(req)
      const rows = await mysqlExec(
        `select * from users
         where account = ${sqlValue(body.account)}
           and password = ${sqlValue(body.password)}
           and (${sqlValue(body.role)} is null or role = ${sqlValue(body.role)})
         limit 1`,
        { parseRows: true },
      )

      if (rows.length === 0) {
        sendJson(res, 401, { message: '账号、密码或身份不正确' })
        return
      }

      sendJson(res, 200, { user: toPublicUser(rows[0]) })
      return
    }

    if (req.method === 'POST' && path === '/api/auth/register') {
      const body = await readBody(req)
      const email = body.email || body.phone
      if (!body.account || !body.name || !email || !body.college || !body.className || !body.password) {
        sendJson(res, 400, { message: '注册信息不能为空' })
        return
      }

      const existing = await mysqlExec(`select id from users where account = ${sqlValue(body.account)} limit 1`, {
        parseRows: true,
      })
      if (existing.length > 0) {
        sendJson(res, 409, { message: '该学号已注册，请直接登录' })
        return
      }

      await mysqlExec(
        `insert into users (account, password, name, role, college, class_name, phone)
         values (${sqlValue(body.account)}, ${sqlValue(body.password)}, ${sqlValue(body.name)}, 'student',
         ${sqlValue(body.college)}, ${sqlValue(body.className)}, ${sqlValue(email)})`,
      )
      const rows = await mysqlExec(`select * from users where account = ${sqlValue(body.account)} limit 1`, {
        parseRows: true,
      })
      sendJson(res, 201, { user: toPublicUser(rows[0]) })
      return
    }

    if (req.method === 'GET' && path === '/api/rooms') {
      const rows = await mysqlExec(
        `select
          r.id,
          r.name,
          r.location,
          r.open_hours as hours,
          cast(r.facilities as char) as facilities,
          sum(if(s.status = 'free', 1, 0)) as free,
          sum(if(s.status in ('used', 'booked'), 1, 0)) as used,
          sum(if(s.status = 'maintenance', 1, 0)) as maintenance
        from rooms r
        left join seats s on s.room_id = r.id
        group by r.id, r.name, r.location, r.open_hours, r.facilities
        order by r.sort_order, r.id`,
        { parseRows: true },
      )

      sendJson(res, 200, {
        rooms: rows.map((row) => ({
          id: row.id,
          name: row.name,
          location: row.location,
          hours: row.hours,
          facilities: JSON.parse(row.facilities || '[]'),
          seats: {
            free: Number(row.free || 0),
            used: Number(row.used || 0),
            maintenance: Number(row.maintenance || 0),
          },
        })),
      })
      return
    }

    const seatsMatch = path.match(/^\/api\/rooms\/([^/]+)\/seats$/)
    if (req.method === 'GET' && seatsMatch) {
      const startTime = url.searchParams.get('startTime')
      const endTime = url.searchParams.get('endTime')
      const rows = await mysqlExec(
        `select
          s.seat_no as id,
          case
            when s.status = 'maintenance' then 'maintenance'
            when exists (
              select 1
              from bookings b
              where b.seat_id = s.id
                and b.status = 'checked_in'
                and (${sqlValue(startTime)} is null or (b.start_time < ${sqlValue(endTime)} and b.end_time > ${sqlValue(startTime)}))
            ) then 'used'
            when exists (
              select 1
              from bookings b
              where b.seat_id = s.id
                and b.status = 'pending'
                and (${sqlValue(startTime)} is null or (b.start_time < ${sqlValue(endTime)} and b.end_time > ${sqlValue(startTime)}))
            ) then 'booked'
            when s.status in ('free', 'booked') then 'free'
            else s.status
          end as status,
          s.position_note as positionNote,
          s.config
         from seats s
         where s.room_id = ${sqlValue(decodeURIComponent(seatsMatch[1]))}
         order by s.seat_no`,
        { parseRows: true },
      )
      sendJson(res, 200, { seats: rows })
      return
    }

    if (req.method === 'POST' && path === '/api/bookings') {
      const body = await readBody(req)
      if (!body.userId || !body.roomId || !body.seatNo || !body.startTime || !body.endTime) {
        sendJson(res, 400, { message: '预约用户、座位和时间段不能为空' })
        return
      }
      if (new Date(body.startTime).getTime() >= new Date(body.endTime).getTime()) {
        sendJson(res, 400, { message: '预约结束时间必须晚于开始时间' })
        return
      }
      const seatRows = await mysqlExec(
        `select id, status from seats
         where room_id = ${sqlValue(body.roomId)}
           and seat_no = ${sqlValue(body.seatNo)}
         limit 1`,
        { parseRows: true },
      )

      if (seatRows.length === 0) {
        sendJson(res, 404, { message: '座位不存在' })
        return
      }
      if (seatRows[0].status === 'maintenance') {
        sendJson(res, 409, { message: '该座位正在维修，暂不可预约' })
        return
      }

      const conflictRows = await mysqlExec(
        `select id
         from bookings
         where seat_id = ${sqlValue(seatRows[0].id)}
           and status in ('pending', 'checked_in')
           and start_time < ${sqlValue(body.endTime)}
           and end_time > ${sqlValue(body.startTime)}
         limit 1`,
        { parseRows: true },
      )
      if (conflictRows.length > 0) {
        sendJson(res, 409, { message: '该座位在所选时间段已被预约，请选择其他时间段' })
        return
      }

      const bookingRows = await mysqlExec(
        `start transaction;
         insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
         values (${sqlValue(body.userId)}, ${sqlValue(body.roomId)}, ${sqlValue(seatRows[0].id)},
         ${sqlValue(body.startTime)}, ${sqlValue(body.endTime)}, 'pending');
         set @booking_id = last_insert_id();
         commit;
         select @booking_id as id;`,
        { parseRows: true },
      )
      sendJson(res, 201, { id: Number(bookingRows[0]?.id), status: '待签到' })
      return
    }

    const bookingListMatch = path.match(/^\/api\/bookings\/(\d+)$/)
    if (req.method === 'GET' && bookingListMatch) {
      const rows = await mysqlExec(
        `select
          b.id,
          date_format(b.start_time, '%Y-%m-%d') as date,
          r.name as room,
          s.seat_no as seat,
          concat(date_format(b.start_time, '%H:%i'), '-', date_format(b.end_time, '%H:%i')) as time,
          b.status
        from bookings b
        join rooms r on r.id = b.room_id
        join seats s on s.id = b.seat_id
        where b.user_id = ${sqlValue(bookingListMatch[1])}
        order by b.start_time desc`,
        { parseRows: true },
      )

      sendJson(res, 200, {
        bookings: rows.map((row) => ({
          ...row,
          id: Number(row.id),
          status: bookingStatusToCn(row.status),
        })),
      })
      return
    }

    const bookingStatusMatch = path.match(/^\/api\/bookings\/(\d+)\/status$/)
    if (req.method === 'PATCH' && bookingStatusMatch) {
      const body = await readBody(req)
      const result = await updateBookingStatus(bookingStatusMatch[1], body.status)
      if (result.error) {
        sendJson(res, result.error.statusCode, { message: result.error.message })
        return
      }
      sendJson(res, 200, result)
      return
    }

    const violationAppealMatch = path.match(/^\/api\/violations\/(\d+)\/appeal$/)
    if (req.method === 'PATCH' && violationAppealMatch) {
      const body = await readBody(req)
      const appealReason = String(body.reason || '').trim()
      if (!appealReason) {
        sendJson(res, 400, { message: '请填写申诉理由' })
        return
      }
      const rows = await mysqlExec(
        `select id, user_id, status, reason from violations where id = ${sqlValue(violationAppealMatch[1])} limit 1`,
        { parseRows: true },
      )
      if (rows.length === 0 || String(rows[0].user_id) !== String(body.userId || '')) {
        sendJson(res, 404, { message: '违规记录不存在' })
        return
      }
      if (rows[0].status === '违规已撤回') {
        sendJson(res, 409, { message: '该违规已撤回，无需申诉' })
        return
      }
      if (rows[0].status === '申诉待处理') {
        sendJson(res, 200, { status: '申诉待处理', message: '申诉已提交，请等待管理员审核' })
        return
      }

      const cleanReason = String(rows[0].reason || '').split('\n申诉理由：')[0]
      await mysqlExec(
        `update violations
         set status = '申诉待处理',
             reason = ${sqlValue(`${cleanReason}\n申诉理由：${appealReason}`)}
         where id = ${sqlValue(violationAppealMatch[1])}`,
      )
      sendJson(res, 200, { status: '申诉待处理', message: '申诉已提交，请等待管理员审核' })
      return
    }

    const violationMatch = path.match(/^\/api\/violations\/(\d+)$/)
    if (req.method === 'GET' && violationMatch) {
      const rows = await mysqlExec(
        `select
          id,
          date_format(happened_at, '%Y-%m-%d') as date,
          type,
          reason,
          status,
          ${violationScoreCase()} as scoreChange
         from violations
         where user_id = ${sqlValue(violationMatch[1])}
         order by happened_at desc`,
        { parseRows: true },
      )
      sendJson(res, 200, {
        violations: rows.map((row) => ({ ...splitAppealReason(row), id: Number(row.id) })),
      })
      return
    }

    if (req.method === 'GET' && path === '/api/admin/stats') {
      const rows = await mysqlExec(
        `select
          (select count(*) from bookings where date(start_time) = curdate()) as todayBookings,
          coalesce(round(
            (select count(*) from bookings where status in ('checked_in', 'completed')) /
            nullif((select count(*) from bookings), 0) * 100
          ), 0) as checkRate,
          (select count(*) from seats where status = 'free') as freeSeats,
          (select count(*) from violations where status = '申诉待处理') as pendingViolations`,
        { parseRows: true },
      )
      const stats = rows[0] || {}
      sendJson(res, 200, {
        todayBookings: Number(stats.todayBookings || 0),
        checkRate: Number(stats.checkRate || 0),
        freeSeats: Number(stats.freeSeats || 0),
        pendingViolations: Number(stats.pendingViolations || 0),
      })
      return
    }

    if (req.method === 'GET' && path === '/api/admin/bookings') {
      const rows = await mysqlExec(
        `select
          b.id,
          u.account,
          u.name as user,
          date_format(b.start_time, '%Y-%m-%d') as date,
          r.name as room,
          s.seat_no as seat,
          concat(date_format(b.start_time, '%H:%i'), '-', date_format(b.end_time, '%H:%i')) as time,
          b.status,
          date_format(b.created_at, '%Y-%m-%d %H:%i') as createdAt
        from bookings b
        join users u on u.id = b.user_id
        join rooms r on r.id = b.room_id
        join seats s on s.id = b.seat_id
        order by b.created_at desc, b.start_time desc`,
        { parseRows: true },
      )
      sendJson(res, 200, {
        bookings: rows.map((row) => ({
          ...row,
          id: Number(row.id),
          status: bookingStatusToCn(row.status),
        })),
      })
      return
    }

    if (req.method === 'GET' && path === '/api/admin/users') {
      const rows = await mysqlExec(
        `select
          u.id,
          u.account,
          u.name,
          u.college,
          u.class_name as className,
          u.phone,
          coalesce(b.bookingCount, 0) as bookings,
          100 + coalesce(v.scoreChange, 0) as credit
        from users u
        left join (
          select user_id, count(*) as bookingCount
          from bookings
          group by user_id
        ) b on b.user_id = u.id
        left join (
          select user_id, sum(${violationScoreCase()}) as scoreChange
          from violations
          group by user_id
        ) v on v.user_id = u.id
        where u.role = 'student'
        order by u.id desc`,
        { parseRows: true },
      )
      sendJson(res, 200, {
        users: rows.map((row) => {
          const credit = Number(row.credit || 0)
          return {
            ...row,
            id: Number(row.id),
            bookings: Number(row.bookings || 0),
            credit,
            status: userCreditState(credit),
          }
        }),
      })
      return
    }

    const adminUserMatch = path.match(/^\/api\/admin\/users\/(\d+)$/)
    if (req.method === 'PATCH' && adminUserMatch) {
      const userId = adminUserMatch[1]
      const body = await readBody(req)
      if (!body.name || !body.college || !body.className || !body.phone) {
        sendJson(res, 400, { message: '学生姓名、学院、班级和联系方式不能为空' })
        return
      }

      const rows = await mysqlExec(
        `select id, account, role from users where id = ${sqlValue(userId)} limit 1`,
        { parseRows: true },
      )
      if (rows.length === 0 || rows[0].role !== 'student') {
        sendJson(res, 404, { message: '学生账号不存在' })
        return
      }

      await mysqlExec(
        `update users
         set name = ${sqlValue(body.name)},
             college = ${sqlValue(body.college)},
             class_name = ${sqlValue(body.className)},
             phone = ${sqlValue(body.phone)}
             ${body.password ? `, password = ${sqlValue(body.password)}` : ''}
         where id = ${sqlValue(userId)}`,
      )
      sendJson(res, 200, {
        user: {
          id: Number(userId),
          account: rows[0].account,
          name: body.name,
          college: body.college,
          className: body.className,
          phone: body.phone,
        },
      })
      return
    }

    if (req.method === 'DELETE' && adminUserMatch) {
      const userId = adminUserMatch[1]
      const rows = await mysqlExec(
        `select id, account, name, role from users where id = ${sqlValue(userId)} limit 1`,
        { parseRows: true },
      )
      if (rows.length === 0 || rows[0].role !== 'student') {
        sendJson(res, 404, { message: '学生账号不存在' })
        return
      }

      const relationRows = await mysqlExec(
        `select
          (select count(*) from bookings where user_id = ${sqlValue(userId)}) as bookings,
          (select count(*) from violations where user_id = ${sqlValue(userId)}) as violations`,
        { parseRows: true },
      )
      if (Number(relationRows[0]?.bookings || 0) > 0 || Number(relationRows[0]?.violations || 0) > 0) {
        sendJson(res, 409, { message: '该学生已有预约或违规记录，不能直接删除' })
        return
      }

      await mysqlExec(`delete from users where id = ${sqlValue(userId)}`)
      sendJson(res, 200, { id: Number(userId), account: rows[0].account, name: rows[0].name })
      return
    }

    if (req.method === 'GET' && path === '/api/admin/violations') {
      const rows = await mysqlExec(
        `select
          v.id,
          u.account,
          u.name as user,
          date_format(v.happened_at, '%Y-%m-%d') as date,
          v.type,
          v.reason,
          v.status,
          ${violationScoreCase()} as scoreChange
        from violations v
        join users u on u.id = v.user_id
        where v.status = '申诉待处理'
        order by v.happened_at desc`,
        { parseRows: true },
      )
      sendJson(res, 200, {
        violations: rows.map((row) => ({
          ...splitAppealReason(row),
          id: Number(row.id),
          scoreChange: Number(row.scoreChange || 0),
        })),
      })
      return
    }

    if (req.method === 'GET' && path === '/api/admin/seats') {
      const roomId = url.searchParams.get('roomId')
      const rows = await mysqlExec(
        `select
          s.id,
          s.room_id as roomId,
          r.name as room,
          s.seat_no as seatNo,
          s.status,
          s.position_note as positionNote,
          s.config
        from seats s
        join rooms r on r.id = s.room_id
        where (${sqlValue(roomId)} is null or s.room_id = ${sqlValue(roomId)})
        order by r.sort_order, s.seat_no`,
        { parseRows: true },
      )
      sendJson(res, 200, { seats: rows.map((row) => ({ ...row, id: Number(row.id) })) })
      return
    }

    if (req.method === 'POST' && path === '/api/admin/rooms') {
      const body = await readBody(req)
      const roomId = String(body.id || '').trim()
      if (!roomId || !body.name || !body.location || !body.hours) {
        sendJson(res, 400, { message: '自习室编号、名称、位置和开放时间不能为空' })
        return
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(roomId)) {
        sendJson(res, 400, { message: '自习室编号只能包含字母、数字、下划线和短横线' })
        return
      }

      const existing = await mysqlExec(`select id from rooms where id = ${sqlValue(roomId)} limit 1`, { parseRows: true })
      if (existing.length > 0) {
        sendJson(res, 409, { message: '该自习室编号已存在' })
        return
      }

      const facilities = Array.isArray(body.facilities)
        ? body.facilities.map((item) => String(item).trim()).filter(Boolean)
        : String(body.facilities || '')
            .split(/[，,\s]+/)
            .map((item) => item.trim())
            .filter(Boolean)
      const facilityJson = JSON.stringify(facilities)
      const sortRows = await mysqlExec('select coalesce(max(sort_order), 0) + 1 as sortOrder from rooms', { parseRows: true })
      const sortOrder = Number(sortRows[0]?.sortOrder || 1)
      const seatValues = []
      for (let index = 0; index < 48; index += 1) {
        const row = String.fromCharCode(65 + Math.floor(index / 8))
        const seatNo = `${row}${String((index % 8) + 1).padStart(2, '0')}`
        const positionNote = `${row} 排 ${index % 8 + 1} 号`
        seatValues.push(`(${sqlValue(roomId)}, ${sqlValue(seatNo)}, 'free', ${sqlValue(positionNote)}, '插座 / 台灯')`)
      }

      await mysqlExec(
        `start transaction;
         insert into rooms (id, name, location, open_hours, facilities, sort_order)
         values (${sqlValue(roomId)}, ${sqlValue(body.name)}, ${sqlValue(body.location)}, ${sqlValue(body.hours)},
         cast(${sqlValue(facilityJson)} as json), ${sqlValue(sortOrder)});
         insert into seats (room_id, seat_no, status, position_note, config)
         values ${seatValues.join(',')};
         commit;`,
      )
      sendJson(res, 201, {
        room: {
          id: roomId,
          name: body.name,
          location: body.location,
          hours: body.hours,
          facilities,
          seats: { free: 48, used: 0, maintenance: 0 },
        },
      })
      return
    }

    const adminRoomMatch = path.match(/^\/api\/admin\/rooms\/([^/]+)$/)
    if (req.method === 'DELETE' && adminRoomMatch) {
      const roomId = decodeURIComponent(adminRoomMatch[1])
      const rows = await mysqlExec(`select id, name from rooms where id = ${sqlValue(roomId)} limit 1`, { parseRows: true })
      if (rows.length === 0) {
        sendJson(res, 404, { message: '自习室不存在' })
        return
      }

      const bookingRows = await mysqlExec(`select count(*) as total from bookings where room_id = ${sqlValue(roomId)}`, {
        parseRows: true,
      })
      if (Number(bookingRows[0]?.total || 0) > 0) {
        sendJson(res, 409, { message: '该自习室已有预约记录，不能直接删除' })
        return
      }

      await mysqlExec(
        `start transaction;
         delete from seats where room_id = ${sqlValue(roomId)};
         delete from rooms where id = ${sqlValue(roomId)};
         commit;`,
      )
      sendJson(res, 200, { id: roomId, name: rows[0].name })
      return
    }

    if (req.method === 'PATCH' && adminRoomMatch) {
      const body = await readBody(req)
      const roomId = decodeURIComponent(adminRoomMatch[1])
      if (!body.name || !body.location || !body.hours) {
        sendJson(res, 400, { message: '自习室名称、位置和开放时间不能为空' })
        return
      }

      const facilities = Array.isArray(body.facilities)
        ? body.facilities.map((item) => String(item).trim()).filter(Boolean)
        : String(body.facilities || '')
            .split(/[，,\s]+/)
            .map((item) => item.trim())
            .filter(Boolean)
      const facilityJson = JSON.stringify(facilities)
      const rows = await mysqlExec(`select id from rooms where id = ${sqlValue(roomId)} limit 1`, { parseRows: true })
      if (rows.length === 0) {
        sendJson(res, 404, { message: '自习室不存在' })
        return
      }

      await mysqlExec(
        `update rooms
         set name = ${sqlValue(body.name)},
             location = ${sqlValue(body.location)},
             open_hours = ${sqlValue(body.hours)},
             facilities = cast(${sqlValue(facilityJson)} as json)
         where id = ${sqlValue(roomId)}`,
      )
      sendJson(res, 200, {
        room: {
          id: roomId,
          name: body.name,
          location: body.location,
          hours: body.hours,
          facilities,
        },
      })
      return
    }

    const adminBookingStatusMatch = path.match(/^\/api\/admin\/bookings\/(\d+)\/status$/)
    if (req.method === 'PATCH' && adminBookingStatusMatch) {
      const body = await readBody(req)
      const result = await updateBookingStatus(adminBookingStatusMatch[1], body.status)
      if (result.error) {
        sendJson(res, result.error.statusCode, { message: result.error.message })
        return
      }
      sendJson(res, 200, result)
      return
    }

    const adminSeatStatusMatch = path.match(/^\/api\/admin\/seats\/(\d+)\/status$/)
    if (req.method === 'PATCH' && adminSeatStatusMatch) {
      const body = await readBody(req)
      const allowed = new Set(['free', 'used', 'booked', 'maintenance'])
      if (!allowed.has(body.status)) {
        sendJson(res, 400, { message: '座位状态不正确' })
        return
      }
      await mysqlExec(`update seats set status = ${sqlValue(body.status)} where id = ${sqlValue(adminSeatStatusMatch[1])}`)
      sendJson(res, 200, { status: body.status })
      return
    }

    const adminViolationStatusMatch = path.match(/^\/api\/admin\/violations\/(\d+)\/status$/)
    if (req.method === 'PATCH' && adminViolationStatusMatch) {
      const body = await readBody(req)
      const statusByAction = {
        reject: '申诉已驳回',
        revoke: '违规已撤回',
      }
      const status = statusByAction[body.action] || body.status || '申诉已驳回'
      if (!['申诉已驳回', '违规已撤回', '申诉待处理'].includes(status)) {
        sendJson(res, 400, { message: '违规处理状态不正确' })
        return
      }
      await mysqlExec(
        `update violations set status = ${sqlValue(status)} where id = ${sqlValue(adminViolationStatusMatch[1])}`,
      )
      const message = status === '违规已撤回'
        ? '管理员已撤回本次违规，相关扣分已取消'
        : '管理员已驳回本次申诉，违规扣分维持不变'
      sendJson(res, 200, { status, message })
      return
    }

    notFound(res)
  } catch (error) {
    console.error(error)
    const message = error.stderr || error.message || '服务器内部错误，请检查数据库连接和表结构'
    sendJson(res, 500, { message })
  }
}

http.createServer(handleRequest).listen(port, '127.0.0.1', () => {
  console.log(`Study room booking API running at http://127.0.0.1:${port}`)
  console.log(`MySQL database: ${env.DB_NAME || 'SchoolStudyroomReservation'}`)
})
