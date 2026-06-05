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

function violationScoreCase() {
  return `case
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
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,OPTIONS',
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
      if (!body.account || !body.name || !body.password) {
        sendJson(res, 400, { message: '学号、姓名和密码不能为空' })
        return
      }

      await mysqlExec(
        `insert into users (account, password, name, role, college, class_name, phone)
         values (${sqlValue(body.account)}, ${sqlValue(body.password)}, ${sqlValue(body.name)}, 'student',
         '软件工程学院', ${sqlValue(body.className || '软件工程 2301')}, ${sqlValue(body.phone || '')})`,
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
      const rows = await mysqlExec(
        `select seat_no as id, status, position_note as positionNote, config
         from seats
         where room_id = ${sqlValue(decodeURIComponent(seatsMatch[1]))}
         order by seat_no`,
        { parseRows: true },
      )
      sendJson(res, 200, { seats: rows })
      return
    }

    if (req.method === 'POST' && path === '/api/bookings') {
      const body = await readBody(req)
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
      if (seatRows[0].status !== 'free') {
        sendJson(res, 409, { message: '该座位当前不可预约' })
        return
      }

      await mysqlExec(
        `start transaction;
         update seats set status = 'booked' where id = ${sqlValue(seatRows[0].id)};
         insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
         values (${sqlValue(body.userId)}, ${sqlValue(body.roomId)}, ${sqlValue(seatRows[0].id)},
         ${sqlValue(body.startTime || '2026-06-04 19:00:00')}, ${sqlValue(body.endTime || '2026-06-04 21:00:00')}, 'pending');
         commit;`,
      )
      sendJson(res, 201, { status: '待签到' })
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
      const allowed = new Set(['pending', 'checked_in', 'completed', 'canceled'])
      if (!allowed.has(body.status)) {
        sendJson(res, 400, { message: '预约状态不正确' })
        return
      }

      const rows = await mysqlExec(
        `select
          seat_id,
          user_id,
          timestampdiff(minute, start_time, now()) as minutesLate,
          timestampdiff(minute, now(), start_time) as minutesBefore
         from bookings
         where id = ${sqlValue(bookingStatusMatch[1])}`,
        { parseRows: true },
      )
      if (rows.length === 0) {
        sendJson(res, 404, { message: '预约记录不存在' })
        return
      }

      const violation = getCreditViolation(
        body.status,
        Number(rows[0].minutesLate || 0),
        Number(rows[0].minutesBefore || 0),
      )
      const seatStatus = body.status === 'completed' || body.status === 'canceled' ? 'free' : 'booked'
      const violationSql = violation
        ? `insert into violations (user_id, type, reason, status, happened_at)
           values (${sqlValue(rows[0].user_id)}, ${sqlValue(violation.type)}, ${sqlValue(violation.reason)},
           '已处理', now());`
        : ''
      await mysqlExec(
        `start transaction;
         update bookings set status = ${sqlValue(body.status)} where id = ${sqlValue(bookingStatusMatch[1])};
         update seats set status = ${sqlValue(seatStatus)} where id = ${sqlValue(rows[0].seat_id)};
         ${violationSql}
         commit;`,
      )
      sendJson(res, 200, { status: bookingStatusToCn(body.status), violation })
      return
    }

    const violationMatch = path.match(/^\/api\/violations\/(\d+)$/)
    if (req.method === 'GET' && violationMatch) {
      const rows = await mysqlExec(
        `select
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
      sendJson(res, 200, { violations: rows })
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
          (select count(*) from violations where status = '待处理') as pendingViolations`,
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
