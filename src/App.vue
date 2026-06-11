<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { apiRequest, normalizeStatus, toApiBookingStatus } from './api'
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  DoorOpen,
  LayoutDashboard,
  LogIn,
  LogOut,
  MapPin,
  MonitorCog,
  Search,
  Repeat2,
  UserPlus,
  Users,
  Wrench,
  XCircle,
} from 'lucide-vue-next'

const authMode = ref('login')
const loginRole = ref('student')
const currentPage = ref('home')
const userRole = ref('student')
const selectedRoomId = ref('mingde-301')
const selectedSeatId = ref('A03')
const bookingStatus = ref('待签到')
const searchText = ref('')
const currentFilter = ref('all')
const selectedDate = ref('2026-06-05')
const selectedStartTime = ref('19:00')
const selectedEndTime = ref('21:00')
const toastMessage = ref('')
const profileMenuOpen = ref(false)
const checkinConfirmOpen = ref(false)
const checkoutConfirmOpen = ref(false)
const cancelConfirmOpen = ref(false)
const appealDialogOpen = ref(false)
const roomEditorOpen = ref(false)
const bookingDetailOpen = ref(false)
const roomDeleteConfirmOpen = ref(false)
const userDeleteConfirmOpen = ref(false)
const userDetailOpen = ref(false)
const timePickerOpen = ref('')
const beijingNow = ref(new Date())
const currentUser = ref(null)
const currentBookingId = ref(null)
const apiOnline = ref(false)
const liveSyncing = ref(false)
const adminStats = ref({
  todayBookings: 328,
  checkRate: 87,
  freeSeats: 120,
  pendingViolations: 3,
})
const adminSelectedRoomId = ref('all')
const editingRoomId = ref('')
const selectedAdminBooking = ref(null)
const selectedAppealViolation = ref(null)
const pendingDeleteRoom = ref(null)
const pendingDeleteUser = ref(null)
const selectedAdminUser = ref(null)
const roomEditorForm = ref({
  id: '',
  name: '',
  location: '',
  hours: '',
  facilities: '',
})
const userEditorForm = ref({
  name: '',
  college: '',
  className: '',
  phone: '',
  password: '',
})
const appealForm = ref({
  reason: '',
  customReason: '',
})
const appealReasonOptions = [
  '签到设备异常，已到场但无法完成签到',
  '预约时间或系统状态显示异常',
  '突发课程、考试或学院事务冲突',
  '身体不适或紧急情况影响到场',
  '其他原因，手动填写',
]
const LOGIN_CACHE_KEY = 'study-room-last-login'
const REGISTERED_USERS_CACHE_KEY = 'study-room-registered-users'

function readSavedLogin(role = 'student') {
  try {
    const saved = JSON.parse(window.localStorage.getItem(LOGIN_CACHE_KEY) || 'null')
    if (saved?.role === role) {
      return {
        account: saved.account || '',
        password: saved.password || '',
      }
    }
  } catch {
    // Ignore broken localStorage data and fall back to an empty form.
  }
  return { account: '', password: '' }
}

function saveLogin(role) {
  window.localStorage.setItem(
    LOGIN_CACHE_KEY,
    JSON.stringify({
      role,
      account: loginForm.value.account,
      password: loginForm.value.password,
    }),
  )
}

function readRegisteredUsers() {
  try {
    const saved = JSON.parse(window.localStorage.getItem(REGISTERED_USERS_CACHE_KEY) || '[]')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

function saveRegisteredUser(user) {
  if (!user?.account) return
  const rows = readRegisteredUsers()
  const nextUser = {
    account: user.account,
    name: user.name || user.account,
    college: user.college || '',
    className: user.className || '',
    phone: user.phone || '',
    bookings: 0,
    credit: 100,
    status: '正常',
  }
  const nextRows = [nextUser, ...rows.filter((item) => item.account !== nextUser.account)]
  window.localStorage.setItem(REGISTERED_USERS_CACHE_KEY, JSON.stringify(nextRows))
  localRegisteredUsers.value = nextRows
}

const loginForm = ref(readSavedLogin('student'))
const registerForm = ref({
  account: '',
  name: '',
  phone: '',
  college: '',
  className: '',
  password: '',
  confirmPassword: '',
})
const collegeOptions = [
  { name: '软件工程学院', classes: ['软件工程 2301', '软件工程 2302', '软件工程 2303'] },
  { name: '计算机科学学院', classes: ['计算机科学 2301', '数据科学 2301', '人工智能 2301'] },
  { name: '信息管理学院', classes: ['信息管理 2301', '电子商务 2301', '数字媒体 2301'] },
  { name: '电子信息学院', classes: ['通信工程 2301', '电子信息 2301', '自动化 2301'] },
]
let toastTimer
let clockTimer
let liveTimer

const allNavItems = [
  { key: 'home', label: '主页', icon: LayoutDashboard },
  { key: 'rooms', label: '自习室', icon: DoorOpen },
  { key: 'seat', label: '座位详情', icon: BookOpen },
  { key: 'booking', label: '我的预约', mobileLabel: '我的', icon: CalendarCheck },
  { key: 'violations', label: '违规记录', icon: AlertTriangle },
  { key: 'admin', label: '管理员', icon: MonitorCog },
]

const adminNavItems = [
  { key: 'admin', label: '后台总览', icon: MonitorCog },
  { key: 'adminRooms', label: '自习室管理', icon: DoorOpen },
  { key: 'adminSeats', label: '座位管理', icon: BookOpen },
  { key: 'adminBookings', label: '预约管理', icon: ClipboardList },
  { key: 'adminUsers', label: '用户管理', icon: Users },
  { key: 'adminViolations', label: '违规处理', icon: AlertTriangle },
  { key: 'adminReports', label: '数据报表', icon: BarChart3 },
]

const pageMeta = {
  home: { title: '主页界面', subtitle: '系统功能入口与今日学习状态' },
  rooms: { title: '自习室列表界面', subtitle: '展示自习室和座位状态' },
  seat: { title: '座位详情界面', subtitle: '座位信息和预约按钮' },
  booking: { title: '我的预约界面', subtitle: '预约记录、签到签退、取消' },
  violations: { title: '违规记录界面', subtitle: '违规信息展示' },
  admin: { title: '管理员后台界面', subtitle: '管理功能页面' },
  adminRooms: { title: '自习室管理', subtitle: '维护开放时间、位置和容量信息' },
  adminSeats: { title: '座位管理', subtitle: '查看座位状态并处理设备报修' },
  adminBookings: { title: '预约管理', subtitle: '查看预约、签到、签退和取消记录' },
  adminUsers: { title: '用户管理', subtitle: '维护学生账号、学院班级和权限状态' },
  adminViolations: { title: '违规处理', subtitle: '复核违规记录、扣分和申诉状态' },
  adminReports: { title: '数据报表', subtitle: '统计使用率、高峰时段和运营趋势' },
}

const rooms = ref([
  {
    id: 'mingde-301',
    name: '明德楼 301',
    location: '三楼东侧',
    hours: '08:00-22:00',
    seats: { free: 24, used: 36, maintenance: 2 },
    facilities: ['插座', '台灯', '靠窗区'],
  },
  {
    id: 'mingde-302',
    name: '明德楼 302',
    location: '三楼西侧',
    hours: '08:00-22:00',
    seats: { free: 18, used: 42, maintenance: 0 },
    facilities: ['静音区', '空调'],
  },
  {
    id: 'library-a',
    name: '图书馆 A 区',
    location: '二楼南侧',
    hours: '07:30-23:00',
    seats: { free: 46, used: 88, maintenance: 4 },
    facilities: ['大桌区', '插座', '饮水点'],
  },
  {
    id: 'library-b',
    name: '图书馆 B 区',
    location: '四楼北侧',
    hours: '07:30-23:00',
    seats: { free: 12, used: 96, maintenance: 1 },
    facilities: ['安静区', '阅览区'],
  },
  {
    id: 'lab-501',
    name: '实验楼 501',
    location: '五楼',
    hours: '09:00-21:30',
    seats: { free: 20, used: 28, maintenance: 0 },
    facilities: ['电脑位', '投影'],
  },
])

const seatStates = [
  'free',
  'used',
  'free',
  'booked',
  'maintenance',
  'free',
  'used',
  'free',
  'free',
  'used',
  'free',
  'free',
  'booked',
  'used',
  'free',
  'free',
  'maintenance',
  'free',
  'used',
  'free',
  'free',
  'used',
  'booked',
  'free',
  'maintenance',
  'free',
  'free',
  'used',
  'free',
  'free',
  'booked',
  'free',
  'free',
  'used',
  'free',
  'free',
  'free',
  'used',
  'maintenance',
  'free',
  'free',
  'used',
  'free',
  'free',
  'free',
  'booked',
  'used',
  'free',
]

const seats = ref(seatStates.map((status, index) => {
  const row = String.fromCharCode(65 + Math.floor(index / 8))
  return {
    id: `${row}${String(index % 8 + 1).padStart(2, '0')}`,
    status,
  }
}))

const historyRows = ref([
  { date: '2026-06-04', room: '明德楼 301', seat: 'A03', time: '19:00-21:00', status: '待签到' },
  { date: '2026-06-03', room: '图书馆 A 区', seat: 'C12', time: '14:00-17:00', status: '已签退' },
  { date: '2026-06-02', room: '明德楼 302', seat: 'B08', time: '09:00-11:00', status: '已取消' },
  { date: '2026-05-31', room: '实验楼 501', seat: 'E02', time: '18:00-20:00', status: '已签退' },
])

const violations = ref([
  { date: '2026-05-18', type: '迟到签到', reason: '预约开始后 22 分钟签到', status: '已处理', scoreChange: -5 },
  { date: '2026-04-26', type: '取消超时', reason: '开始前 10 分钟取消预约', status: '已处理', scoreChange: -5 },
  { date: '2026-03-12', type: '爽约', reason: '预约后未签到', status: '已处理', scoreChange: -12 },
])

const creditRules = [
  { title: '迟到签到', text: '开始后 15 分钟内扣 2 分，超过 15 分钟扣 5 分。' },
  { title: '临近取消', text: '开始前 10-30 分钟取消扣 3 分，10 分钟内扣 5 分。' },
  { title: '爽约未到', text: '开始后 30 分钟仍未签到，释放座位并扣 12 分。' },
  { title: '守约恢复', text: '正常签到签退加 1 分，连续 7 次守约加 3 分。' },
]

const adminModules = [
  { page: 'adminRooms', title: '自习室管理', text: '新增、编辑开放时间与位置', icon: DoorOpen },
  { page: 'adminSeats', title: '座位管理', text: '维护座位状态与设备信息', icon: BookOpen },
  { page: 'adminBookings', title: '预约管理', text: '查看预约、签到签退记录', icon: ClipboardList },
  { page: 'adminUsers', title: '用户管理', text: '学生账号和权限维护', icon: Users },
  { page: 'adminViolations', title: '违规处理', text: '审核违规记录和限制策略', icon: AlertTriangle },
  { page: 'adminReports', title: '数据报表', text: '统计使用率与高峰时段', icon: BarChart3 },
]

const roomHourOptions = [
  '07:00-23:00',
  '07:30-23:00',
  '07:30-22:30',
  '07:30-22:00',
  '08:00-22:00',
  '08:00-21:30',
  '09:00-21:30',
]

const fallbackAdminUsers = [
  { account: '20230218', name: '林同学', college: '软件工程学院', className: '软件工程 2301', bookings: 18, credit: 88, status: '正常' },
  { account: '20230406', name: '陈同学', college: '计算机科学学院', className: '数据科学 2301', bookings: 11, credit: 96, status: '正常' },
  { account: '20230127', name: '赵同学', college: '信息管理学院', className: '电子商务 2301', bookings: 7, credit: 63, status: '预警' },
  { account: '20230519', name: '周同学', college: '电子信息学院', className: '通信工程 2301', bookings: 4, credit: 42, status: '限制' },
]

const adminUsers = ref([])
const adminBookings = ref([])
const adminViolations = ref([])
const adminSeats = ref([])
const localRegisteredUsers = ref(readRegisteredUsers())

const adminRepairRows = ref([
  { room: '图书馆 B 区', seat: 'D04', issue: '插座无电', status: '待确认', reporter: '20230127' },
  { room: '图书馆 B 区', seat: 'D05', issue: '台灯损坏', status: '处理中', reporter: '20230406' },
  { room: '明德楼 302', seat: 'B12', issue: '座椅松动', status: '待确认', reporter: '巡检' },
])

const reportRows = [
  { label: '07:30-09:30', value: 64, note: '早高峰' },
  { label: '14:00-16:00', value: 78, note: '下午持续上升' },
  { label: '19:00-21:00', value: 93, note: '晚间峰值' },
  { label: '21:00-23:00', value: 71, note: '图书馆区域更集中' },
]

const filterOptions = [
  { key: 'all', label: '全部' },
  { key: 'free', label: '空闲较多' },
  { key: 'power', label: '有插座' },
]

const timeOptions = Array.from({ length: 31 }, (_, index) => {
  const totalMinutes = 7 * 60 + index * 30
  const hour = String(Math.floor(totalMinutes / 60)).padStart(2, '0')
  const minute = String(totalMinutes % 60).padStart(2, '0')
  return `${hour}:${minute}`
})

const studentProfile = {
  name: '林同学',
  id: '20230218',
  college: '软件工程学院',
  className: '软件工程 2301',
  phone: 'lin@example.com',
}

const adminProfile = {
  name: '管理员',
  id: 'admin001',
  college: '教务管理中心',
  className: '自习室管理组',
  phone: '010-88880000',
}

const selectedRoom = computed(() => rooms.value.find((room) => room.id === selectedRoomId.value) || rooms.value[0])
const selectedSeat = computed(() => seats.value.find((seat) => seat.id === selectedSeatId.value) || seats.value[2])
const isAdmin = computed(() => userRole.value === 'admin')
const navItems = computed(() => (isAdmin.value ? adminNavItems : allNavItems.filter((item) => item.key !== 'admin')))
const currentProfile = computed(() => {
  if (!currentUser.value) {
    return isAdmin.value ? adminProfile : studentProfile
  }

  return {
    name: currentUser.value.name,
    id: currentUser.value.account,
    college: currentUser.value.college,
    className: currentUser.value.className,
    phone: currentUser.value.phone,
  }
})
const profileInitial = computed(() => currentProfile.value.name?.trim()?.charAt(0) || (isAdmin.value ? '管' : '学'))
const currentClassOptions = computed(
  () => collegeOptions.find((college) => college.name === registerForm.value.college)?.classes || [],
)
const meta = computed(() => pageMeta[currentPage.value])
const showSearchBox = computed(() => !isAdmin.value && currentPage.value === 'rooms')
const roomStats = computed(() =>
  rooms.value.reduce(
    (total, room) => {
      total.free += room.seats.free
      total.used += room.seats.used
      total.maintenance += room.seats.maintenance
      return total
    },
    { free: 0, used: 0, maintenance: 0 },
  ),
)
const seatStats = computed(() =>
  seats.value.reduce(
    (total, seat) => {
      total[seat.status] += 1
      return total
    },
    { free: 0, used: 0, booked: 0, maintenance: 0 },
  ),
)

function isActiveBookingStatus(status) {
  return status === '待签到' || status === '已签到'
}

function findActiveBookingRow(preferredId = currentBookingId.value) {
  const preferredRow = preferredId
    ? historyRows.value.find((item) => item.id === preferredId && isActiveBookingStatus(item.status))
    : null
  return preferredRow || historyRows.value.find((item) => isActiveBookingStatus(item.status)) || null
}

const activeBooking = computed(() => {
  const row = findActiveBookingRow()
  if (!row) return null

  return {
    id: row.id,
    date: row.date,
    room: row.room,
    seat: row.seat,
    time: row.time,
    status: row.status,
    actualCheckInAt: row.actualCheckInAt || '',
    actualCheckOutAt: row.actualCheckOutAt || '',
    studyMinutes: Number(row.studyMinutes || 0),
  }
})
const creditScore = computed(() => {
  const score = violations.value.reduce((total, item) => total + getViolationScoreChange(item), 100)
  return Math.max(0, Math.min(110, score))
})
const creditState = computed(() => {
  const score = creditScore.value
  if (score >= 90) return { label: '优秀', badgeClass: 'success', text: '预约状态良好，可正常预约' }
  if (score >= 70) return { label: '正常', badgeClass: 'success', text: '可正常预约，请保持守约' }
  if (score >= 60) return { label: '预警', badgeClass: 'warning', text: '每日限约 1 次，预约前将提醒' }
  if (score >= 40) return { label: '限制', badgeClass: 'warning', text: '仅可预约非热门时段' }
  return { label: '冻结', badgeClass: 'danger', text: '暂停预约 7 天，可提交申诉' }
})
const creditDelta = computed(() =>
  violations.value.reduce((total, item) => total + Math.min(getViolationScoreChange(item), 0), 0),
)
const todayStudyMinutes = computed(() =>
  historyRows.value.reduce((total, row) => total + getTodayStudyMinutes(row), 0),
)
const todayStudyDuration = computed(() => formatStudyDuration(todayStudyMinutes.value))
const activeCheckInWarning = computed(() => creditViolationWarning('已签到'))
const activeCancelWarning = computed(() => creditViolationWarning('已取消'))
const searchKeyword = computed(() => normalizeSearchValue(searchText.value))
const homeStatCards = computed(() => [
  { label: '可预约座位', value: roomStats.value.free, note: '空闲' },
  { label: '今日学习时长', value: todayStudyDuration.value, note: activeBooking.value ? '含当前进行中' : '实际签到至签退' },
  { label: '信用分', value: creditScore.value, note: creditState.value.label },
  { label: '累计学习', value: '38h', note: '本月' },
  { label: '违规次数', value: violations.value.length, note: '已处理' },
])
const homeEntryCards = computed(() => [
  { page: 'rooms', title: '自习室预约', text: '查看空闲教室和座位', icon: DoorOpen },
  { page: 'booking', title: '我的预约', text: '签到、签退、取消预约', icon: CalendarCheck },
  { page: 'violations', title: '违规记录', text: '查看迟到、爽约等记录', icon: AlertTriangle },
  ...(isAdmin.value ? [{ page: 'admin', title: '管理员后台', text: '进入管理功能页面', icon: MonitorCog }] : []),
])
const filteredHomeStats = computed(() =>
  homeStatCards.value.filter((item) => matchesSearch([item.label, item.value, item.note])),
)
const filteredHomeEntries = computed(() =>
  homeEntryCards.value.filter((item) => matchesSearch([item.title, item.text])),
)
const filteredRooms = computed(() => {
  return rooms.value.filter((room) => {
    const matchesKeyword = matchesSearch([room.name, room.location, room.hours, ...room.facilities])
    const matchesFilter =
      currentFilter.value === 'all' ||
      (currentFilter.value === 'free' && room.seats.free >= 20) ||
      (currentFilter.value === 'power' && room.facilities.includes('插座'))
    return matchesKeyword && matchesFilter
  })
})
const filteredSeats = computed(() =>
  seats.value.filter((seat) => matchesSearch([seat.id, seat.status, seatStatusLabel(seat.status)])),
)
const filteredHistoryRows = computed(() =>
  sortHistoryRows(historyRows.value.filter((row) => matchesSearch([row.date, row.room, row.seat, row.time, row.status]))),
)
const filteredViolations = computed(() =>
  violations.value.filter((item) => matchesSearch([item.date, item.type, item.reason, item.status])),
)
const filteredAdminModules = computed(() =>
  adminModules.filter((item) => matchesSearch([item.title, item.text])),
)
const roomEditorHourOptions = computed(() => {
  const current = roomEditorForm.value.hours
  return current && !roomHourOptions.includes(current) ? [current, ...roomHourOptions] : roomHourOptions
})
const adminUserRows = computed(() => {
  const source = adminUsers.value.length > 0 ? adminUsers.value : fallbackAdminUsers
  const merged = [...localRegisteredUsers.value, ...source]
  const seen = new Set()
  return merged.filter((user) => {
    if (!user?.account || seen.has(user.account)) return false
    seen.add(user.account)
    return true
  })
})
const adminRoomOptions = computed(() => [
  { id: 'all', name: '全部自习室' },
  ...rooms.value.map((room) => ({ id: room.id, name: room.name })),
])
const adminRoomRows = computed(() =>
  rooms.value.map((room) => ({
    ...room,
    total: room.seats.free + room.seats.used + room.seats.maintenance,
    usage: Math.round((room.seats.used / Math.max(room.seats.free + room.seats.used + room.seats.maintenance, 1)) * 100),
  })),
)
const adminSeatRows = computed(() => {
  if (adminSeats.value.length > 0) {
    return adminSeats.value.map((seat) => ({
      id: seat.id,
      seatNo: seat.seatNo,
      room: seat.room,
      area: seat.positionNote,
      status: seatStatusLabel(seat.status),
      apiStatus: seat.status,
      equipment: seat.config,
    }))
  }
  const rows = seats.value.map((seat, index) => ({
    id: seat.id,
    seatNo: seat.id,
    room: selectedRoom.value.name,
    area: `${String.fromCharCode(65 + Math.floor(index / 8))} 排`,
    status: seatStatusLabel(seat.status),
    apiStatus: seat.status,
    equipment: index % 5 === 0 ? '插座报修' : index % 7 === 0 ? '台灯待检' : '设备正常',
  }))
  if (adminSelectedRoomId.value === 'all') return rows
  return rows.map((row) => ({ ...row, room: rooms.value.find((room) => room.id === adminSelectedRoomId.value)?.name || row.room }))
})
const adminBookingRows = computed(() =>
  adminBookings.value.length > 0
    ? adminBookings.value
    : historyRows.value.map((row, index) => ({
        ...row,
        user: ['林同学', '陈同学', '赵同学', '周同学'][index % 4],
        account: ['20230218', '20230406', '20230127', '20230519'][index % 4],
      })),
)
const adminViolationRows = computed(() =>
  adminViolations.value.length > 0
    ? adminViolations.value
    : violations.value
        .filter((item) => item.status === '申诉待处理')
        .map((item, index) => ({
          ...item,
          user: item.user || ['林同学', '赵同学', '周同学'][index % 3],
          account: item.account || ['20230218', '20230127', '20230519'][index % 3],
        })),
)
const currentBeijing = computed(() => getBeijingSnapshot())
const minBookingDate = computed(() => currentBeijing.value.date)
const isSelectedToday = computed(() => selectedDate.value === currentBeijing.value.date)
const startTimeOptions = computed(() => {
  const baseOptions = timeOptions.slice(0, -1)
  if (!isSelectedToday.value) return baseOptions
  return baseOptions.filter((time) => timeToMinutes(time) >= currentBeijing.value.minutes)
})
const endTimeOptions = computed(() => {
  if (!selectedStartTime.value) return []
  return timeOptions.filter((time) => time > selectedStartTime.value)
})
const noTimeSlotText = computed(() => (isSelectedToday.value ? '今日已无可选' : '暂无预约时段'))
const selectedTimeSlot = computed(() => `${selectedStartTime.value}-${selectedEndTime.value}`)
const selectedSlotLabel = computed(() => `${selectedDate.value} ${selectedTimeSlot.value}`)

function normalizeSearchValue(value) {
  return String(value ?? '').trim().toLowerCase()
}

function bookingOrderValue(row) {
  const createdAt = parseLocalDateTime(row.createdAt)
  if (createdAt) return createdAt.getTime()
  if (Number.isFinite(Number(row.id))) return Number(row.id)
  const startAt = parseLocalDateTime(`${row.date} ${String(row.time || '').split('-')[0] || '00:00'}:00`)
  return startAt ? startAt.getTime() : 0
}

function sortHistoryRows(rows) {
  return [...rows].sort((a, b) => bookingOrderValue(b) - bookingOrderValue(a))
}

function matchesSearch(fields) {
  const keyword = searchKeyword.value
  if (!keyword) return true

  const values = fields.map((field) => normalizeSearchValue(field)).filter(Boolean)
  const exactMatch = values.some((value) => value === keyword)
  const fuzzyText = values.join(' ')
  const fuzzyMatch = keyword.split(/\s+/).every((part) => fuzzyText.includes(part))
  return exactMatch || fuzzyMatch
}

function seatStatusLabel(status) {
  const labels = {
    free: '空闲',
    booked: '已预约',
    used: '已占',
    maintenance: '维修',
  }
  return labels[status] || status
}

function getBeijingSnapshot(date = beijingNow.value) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    hourCycle: 'h23',
  }).formatToParts(date)
  const valueOf = (type) => parts.find((part) => part.type === type)?.value || '00'
  return {
    date: `${valueOf('year')}-${valueOf('month')}-${valueOf('day')}`,
    time: `${valueOf('hour')}:${valueOf('minute')}`,
    minutes: Number(valueOf('hour')) * 60 + Number(valueOf('minute')),
  }
}

function timeToMinutes(time) {
  const [hour, minute] = time.split(':').map(Number)
  return hour * 60 + minute
}

function ensureValidSelectedDate() {
  if (!selectedDate.value || selectedDate.value < minBookingDate.value) {
    selectedDate.value = minBookingDate.value
  }
}

function ensureValidTimeRange() {
  ensureValidSelectedDate()
  if (startTimeOptions.value.length === 0) {
    selectedStartTime.value = ''
    selectedEndTime.value = ''
    return
  }
  if (!startTimeOptions.value.includes(selectedStartTime.value)) {
    selectedStartTime.value = startTimeOptions.value[0] || ''
  }
  if (!endTimeOptions.value.includes(selectedEndTime.value)) {
    selectedEndTime.value = endTimeOptions.value[0] || ''
  }
}

function toggleTimePicker(key) {
  timePickerOpen.value = timePickerOpen.value === key ? '' : key
}

function selectStartTime(time) {
  selectedStartTime.value = time
  ensureValidTimeRange()
  timePickerOpen.value = ''
}

function selectEndTime(time) {
  selectedEndTime.value = time
  timePickerOpen.value = ''
}

function closeFloatingMenus() {
  profileMenuOpen.value = false
  timePickerOpen.value = ''
}

function toDateTimeRange(date, start, end) {
  return {
    startTime: `${date} ${start}:00`,
    endTime: `${date} ${end}:00`,
  }
}

function parseLocalDateTime(value) {
  if (!value) return null
  const normalized = String(value).replace(' ', 'T')
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatLocalDateTime(date = new Date()) {
  const snapshot = getBeijingSnapshot(date)
  return `${snapshot.date} ${snapshot.time}:00`
}

function plannedStartDate(row = activeBooking.value) {
  if (!row?.date || !row?.time) return null
  const [start] = String(row.time).split('-')
  return parseLocalDateTime(`${row.date} ${start}:00`)
}

function formatStudyDuration(minutes) {
  const safeMinutes = Math.max(0, Math.floor(Number(minutes) || 0))
  const hours = Math.floor(safeMinutes / 60)
  const rest = safeMinutes % 60
  if (hours <= 0) return `${rest}min`
  return rest > 0 ? `${hours}h ${rest}min` : `${hours}h`
}

function getTodayStudyMinutes(row) {
  const checkInAt = parseLocalDateTime(row.actualCheckInAt)
  if (!checkInAt) return 0
  const today = currentBeijing.value.date
  const checkOutAt = parseLocalDateTime(row.actualCheckOutAt)
  const end = checkOutAt || (row.status === '已签到' ? beijingNow.value : null)
  if (!end) return Number(row.studyMinutes || 0)
  const dayStart = parseLocalDateTime(`${today} 00:00:00`)
  const dayEnd = new Date(dayStart.getTime() + 24 * 60 * 60 * 1000)
  const effectiveStart = new Date(Math.max(checkInAt.getTime(), dayStart.getTime()))
  const effectiveEnd = new Date(Math.min(end.getTime(), dayEnd.getTime()))
  return Math.max(0, Math.floor((effectiveEnd - effectiveStart) / 60000))
}

function creditViolationFor(status, row = activeBooking.value) {
  const startAt = plannedStartDate(row)
  if (!startAt) return null
  const now = beijingNow.value
  if (status === '已签到') {
    const minutesLate = Math.floor((now - startAt) / 60000)
    if (minutesLate > 30) return { type: '严重迟到', scoreChange: -8 }
    if (minutesLate > 15) return { type: '迟到签到', scoreChange: -5 }
    if (minutesLate > 5) return { type: '轻微迟到', scoreChange: -2 }
  }
  if (status === '已取消') {
    const minutesBefore = Math.floor((startAt - now) / 60000)
    if (minutesBefore < 0) return { type: '开始后取消', scoreChange: -8 }
    if (minutesBefore <= 10) return { type: '取消超时', scoreChange: -5 }
    if (minutesBefore <= 30) return { type: '临近取消', scoreChange: -3 }
  }
  return null
}

function creditViolationWarning(status, row = activeBooking.value) {
  const violation = creditViolationFor(status, row)
  return violation ? `${violation.type}，本次操作将扣 ${Math.abs(violation.scoreChange)} 分。` : ''
}

function getViolationScoreChange(item) {
  if (item.status === '违规已撤回') return 0
  if (Number.isFinite(Number(item.scoreChange))) return Number(item.scoreChange)
  if (item.type.includes('爽约')) return -12
  if (item.type.includes('取消')) return -5
  if (item.type.includes('占座')) return -6
  if (item.type.includes('迟到')) return -5
  return 0
}

function canAppealViolation(item) {
  return !['申诉待处理', '申诉已驳回', '违规已撤回'].includes(item.status)
}

function violationAppealText(item) {
  if (item.status === '申诉待处理') return '申诉已提交，等待管理员审核。'
  if (item.status === '申诉已驳回') return '管理员已驳回申诉，违规扣分维持不变。'
  if (item.status === '违规已撤回') return '管理员已撤回本次违规，相关扣分已取消。'
  return ''
}

function violationAppealActionLabel(item) {
  if (item.status === '申诉待处理') return '审核中'
  if (item.status === '申诉已驳回') return '已驳回'
  if (item.status === '违规已撤回') return '已撤回'
  return '申诉'
}

const selectedAppealReason = computed(() => {
  if (appealForm.value.reason === '其他原因，手动填写') {
    return appealForm.value.customReason.trim()
  }
  return appealForm.value.reason.trim()
})

function showToast(message, duration = 2600) {
  toastMessage.value = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
  }, duration)
}

function parseFacilityText(value) {
  return String(value || '')
    .split(/[，,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function openRoomEditor(room = null) {
  const target = room || {
    id: '',
    name: '',
    location: '',
    hours: '',
    facilities: [],
  }
  editingRoomId.value = target.id
  roomEditorForm.value = {
    id: target.id || '',
    name: target.name || '',
    location: target.location || '',
    hours: target.hours || '',
    facilities: (target.facilities || []).join('、'),
  }
  roomEditorOpen.value = true
}

function closeRoomEditor() {
  roomEditorOpen.value = false
  editingRoomId.value = ''
}

function openAdminBookingDetail(row) {
  selectedAdminBooking.value = row
  bookingDetailOpen.value = true
}

function closeAdminBookingDetail() {
  bookingDetailOpen.value = false
  selectedAdminBooking.value = null
}

function openRoomDeleteConfirm(room) {
  pendingDeleteRoom.value = room
  roomDeleteConfirmOpen.value = true
}

function closeRoomDeleteConfirm() {
  roomDeleteConfirmOpen.value = false
  pendingDeleteRoom.value = null
}

function removeRegisteredUser(account) {
  const nextRows = readRegisteredUsers().filter((item) => item.account !== account)
  window.localStorage.setItem(REGISTERED_USERS_CACHE_KEY, JSON.stringify(nextRows))
  localRegisteredUsers.value = nextRows
}

function updateRegisteredUser(user) {
  if (!user?.account) return
  const rows = readRegisteredUsers()
  if (!rows.some((item) => item.account === user.account)) return
  const nextRows = rows.map((item) => (item.account === user.account ? { ...item, ...user } : item))
  window.localStorage.setItem(REGISTERED_USERS_CACHE_KEY, JSON.stringify(nextRows))
  localRegisteredUsers.value = nextRows
}

function openUserDetail(user) {
  selectedAdminUser.value = user
  userEditorForm.value = {
    name: user.name || '',
    college: user.college || '',
    className: user.className || '',
    phone: user.phone || '',
    password: '',
  }
  userDetailOpen.value = true
}

function closeUserDetail() {
  userDetailOpen.value = false
  selectedAdminUser.value = null
}

function openUserDeleteConfirm(user) {
  pendingDeleteUser.value = user
  userDeleteConfirmOpen.value = true
}

function closeUserDeleteConfirm() {
  userDeleteConfirmOpen.value = false
  pendingDeleteUser.value = null
}

async function confirmDeleteRoom() {
  const room = pendingDeleteRoom.value
  if (!room?.id) return

  try {
    await apiRequest(`/admin/rooms/${encodeURIComponent(room.id)}`, {
      method: 'DELETE',
    })
    rooms.value = rooms.value.filter((item) => item.id !== room.id)
    if (selectedRoomId.value === room.id) {
      selectedRoomId.value = rooms.value[0]?.id || ''
    }
    if (adminSelectedRoomId.value === room.id) {
      adminSelectedRoomId.value = 'all'
    }
    closeRoomDeleteConfirm()
    await refreshLiveData()
    showToast(`${room.name} 已删除`)
  } catch (error) {
    closeRoomDeleteConfirm()
    showToast(`删除失败：${error.message}`)
  }
}

async function confirmDeleteUser() {
  const user = pendingDeleteUser.value
  if (!user?.account) return

  if (!user.id) {
    removeRegisteredUser(user.account)
    adminUsers.value = adminUsers.value.filter((item) => item.account !== user.account)
    closeUserDeleteConfirm()
    showToast(`${user.name} 已从本地列表删除`)
    return
  }

  try {
    await apiRequest(`/admin/users/${user.id}`, {
      method: 'DELETE',
    })
    adminUsers.value = adminUsers.value.filter((item) => item.id !== user.id)
    removeRegisteredUser(user.account)
    closeUserDeleteConfirm()
    await refreshLiveData()
    showToast(`${user.name} 已删除`)
  } catch (error) {
    closeUserDeleteConfirm()
    showToast(`删除失败：${error.message}`)
  }
}

async function saveUserDetail() {
  const user = selectedAdminUser.value
  const form = userEditorForm.value
  if (!user?.account) return
  if (!form.name.trim() || !form.college.trim() || !form.className.trim() || !form.phone.trim()) {
    showToast('请完整填写姓名、学院、班级和联系方式')
    return
  }
  if (form.password && form.password.length < 6) {
    showToast('新密码至少需要 6 位')
    return
  }

  const payload = {
    name: form.name.trim(),
    college: form.college.trim(),
    className: form.className.trim(),
    phone: form.phone.trim(),
    ...(form.password ? { password: form.password } : {}),
  }

  if (!user.id) {
    const nextUser = { ...user, ...payload }
    updateRegisteredUser(nextUser)
    closeUserDetail()
    showToast(`${nextUser.name} 信息已保存`)
    return
  }

  try {
    await apiRequest(`/admin/users/${user.id}`, {
      method: 'PATCH',
      body: payload,
    })
    const nextUser = { ...user, ...payload }
    adminUsers.value = adminUsers.value.map((item) => (item.id === user.id ? { ...item, ...nextUser } : item))
    updateRegisteredUser(nextUser)
    closeUserDetail()
    await refreshLiveData()
    showToast(`${nextUser.name} 信息已保存`)
  } catch (error) {
    const nextUser = { ...user, ...payload }
    adminUsers.value = adminUsers.value.map((item) => (item.account === user.account ? { ...item, ...nextUser } : item))
    updateRegisteredUser(nextUser)
    closeUserDetail()
    showToast(`接口暂不可用，已先更新页面展示：${error.message}`)
  }
}

function bookingStatusNote(status) {
  if (status === '待签到') return '学生尚未签到，可由管理员取消该预约并释放座位。'
  if (status === '已签到') return '学生已到场，可在离场后由管理员确认签退。'
  if (status === '已取消') return '预约已取消，座位已释放，该记录仅用于审计留存。'
  if (status === '已签退') return '预约已正常结束，学习记录已归档。'
  return '预约状态已归档。'
}

async function saveRoomEditor() {
  const form = roomEditorForm.value
  const facilities = parseFacilityText(form.facilities)
  if (!form.name.trim() || !form.location.trim() || !form.hours.trim()) {
    showToast('请完整填写自习室名称、位置和开放时间')
    return
  }
  if (!editingRoomId.value && !form.id.trim()) {
    showToast('请填写自习室编号')
    return
  }

  const payload = {
    id: form.id.trim(),
    name: form.name.trim(),
    location: form.location.trim(),
    hours: form.hours.trim(),
    facilities,
  }
  const roomId = editingRoomId.value

  if (!roomId) {
    try {
      await apiRequest('/admin/rooms', {
        method: 'POST',
        body: payload,
      })
      await refreshLiveData()
      closeRoomEditor()
      showToast(`${payload.name} 已新增`)
    } catch (error) {
      const localRoom = {
        id: payload.id,
        name: payload.name,
        location: payload.location,
        hours: payload.hours,
        facilities,
        seats: { free: 48, used: 0, maintenance: 0 },
      }
      rooms.value = [localRoom, ...rooms.value.filter((room) => room.id !== localRoom.id)]
      closeRoomEditor()
      showToast(`接口暂不可用，已先添加到页面展示：${error.message}`)
    }
    return
  }

  try {
    await apiRequest(`/admin/rooms/${encodeURIComponent(roomId)}`, {
      method: 'PATCH',
      body: payload,
    })
    await refreshLiveData()
    closeRoomEditor()
    showToast(`${payload.name} 信息已保存`)
  } catch (error) {
    const index = rooms.value.findIndex((room) => room.id === roomId)
    if (index >= 0) {
      rooms.value[index] = { ...rooms.value[index], ...payload }
    }
    closeRoomEditor()
    showToast(`接口暂不可用，已先更新页面展示：${error.message}`)
  }
}

async function loadRooms() {
  const payload = await apiRequest('/rooms')
  rooms.value = payload.rooms
  if (payload.rooms[0] && !rooms.value.some((room) => room.id === selectedRoomId.value)) {
    selectedRoomId.value = payload.rooms[0].id
  }
}

async function loadSeats(roomId = selectedRoomId.value) {
  const range = selectedStartTime.value && selectedEndTime.value
    ? toDateTimeRange(selectedDate.value, selectedStartTime.value, selectedEndTime.value)
    : null
  const query = range
    ? `?startTime=${encodeURIComponent(range.startTime)}&endTime=${encodeURIComponent(range.endTime)}`
    : ''
  const payload = await apiRequest(`/rooms/${roomId}/seats${query}`)
  seats.value = payload.seats
  const firstFreeSeat = payload.seats.find((seat) => seat.status === 'free')
  if (firstFreeSeat && !payload.seats.some((seat) => seat.id === selectedSeatId.value && seat.status === 'free')) {
    selectedSeatId.value = firstFreeSeat.id
  }
}

async function loadBookings(userId = currentUser.value?.id) {
  if (!userId) return

  const payload = await apiRequest(`/bookings/${userId}`)
  historyRows.value = sortHistoryRows(payload.bookings.map((row) => ({
    ...row,
    status: normalizeStatus(row.status),
  })))
  const activeRow = findActiveBookingRow()
  currentBookingId.value = activeRow?.id || null
  bookingStatus.value = activeRow?.status || '暂无预约'
}

async function loadViolations(userId = currentUser.value?.id) {
  if (!userId) return

  const payload = await apiRequest(`/violations/${userId}`)
  violations.value = payload.violations.map((item) => ({
    ...item,
    scoreChange: Number(item.scoreChange ?? getViolationScoreChange(item)),
  }))
}

async function loadAdminStats() {
  const payload = await apiRequest('/admin/stats')
  adminStats.value = payload
}

async function loadAdminBookings() {
  const payload = await apiRequest('/admin/bookings')
  adminBookings.value = payload.bookings.map((row) => ({
    ...row,
    status: normalizeStatus(row.status),
  }))
}

async function loadAdminUsers() {
  const payload = await apiRequest('/admin/users')
  adminUsers.value = payload.users
}

async function loadAdminViolations() {
  const payload = await apiRequest('/admin/violations')
  adminViolations.value = payload.violations.map((item) => ({
    ...item,
    scoreChange: Number(item.scoreChange ?? getViolationScoreChange(item)),
  }))
}

async function loadAdminSeats(roomId = adminSelectedRoomId.value) {
  const query = roomId && roomId !== 'all' ? `?roomId=${encodeURIComponent(roomId)}` : ''
  const payload = await apiRequest(`/admin/seats${query}`)
  adminSeats.value = payload.seats
}

async function loadAdminData() {
  const results = await Promise.allSettled([
    loadAdminStats(),
    loadAdminBookings(),
    loadAdminUsers(),
    loadAdminViolations(),
    loadAdminSeats(),
  ])
  const failed = results.find((result) => result.status === 'rejected')
  if (failed) {
    apiOnline.value = false
  }
}

async function loadAppData(role = userRole.value) {
  try {
    await loadRooms()
    await loadSeats()
    if (role === 'admin') {
      await loadAdminData()
    } else {
      await Promise.all([loadBookings(), loadViolations()])
    }
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    showToast(`数据库未连接，当前使用演示数据：${error.message}`)
  }
}

async function refreshLiveData({ silent = true } = {}) {
  if (authMode.value !== 'app' || liveSyncing.value) return
  liveSyncing.value = true
  try {
    await loadRooms()
    if (isAdmin.value) {
      await loadAdminData()
    } else {
      await Promise.all([
        loadBookings(),
        loadViolations(),
        loadSeats(selectedRoomId.value),
      ])
    }
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    if (!silent) showToast(`同步失败：${error.message}`)
  } finally {
    liveSyncing.value = false
  }
}

function startLiveSync() {
  window.clearInterval(liveTimer)
  liveTimer = window.setInterval(() => {
    refreshLiveData()
  }, 5000)
}

function stopLiveSync() {
  window.clearInterval(liveTimer)
  liveTimer = null
}

async function loginAs(role = 'student') {
  try {
    const payload = await apiRequest('/auth/login', {
      method: 'POST',
      body: {
        account: loginForm.value.account,
        password: loginForm.value.password,
        role,
      },
    })
    currentUser.value = payload.user
    apiOnline.value = true
    saveLogin(role)
  } catch (error) {
    apiOnline.value = false
    showToast(error.status === 401 ? '账号或密码错误，请重新输入' : `登录失败：${error.message}`)
    return
  }

  await enterApp(role === 'admin' ? 'admin' : 'home', role)
}

function switchLoginRole(role) {
  loginRole.value = role
  authMode.value = 'login'
  toastMessage.value = ''
  loginForm.value = readSavedLogin(role)
}

function toggleAuthMode() {
  if (authMode.value === 'login') {
    loginRole.value = 'student'
    authMode.value = 'register'
    return
  }
  authMode.value = 'login'
}

async function registerAccount() {
  if (
    !registerForm.value.account ||
    !registerForm.value.name ||
    !registerForm.value.phone ||
    !registerForm.value.college ||
    !registerForm.value.className ||
    !registerForm.value.password ||
    !registerForm.value.confirmPassword
  ) {
    showToast('请完整填写注册信息')
    return
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    showToast('两次密码不一致')
    return
  }

  try {
    const payload = await apiRequest('/auth/register', {
      method: 'POST',
      body: {
        account: registerForm.value.account,
        name: registerForm.value.name,
        email: registerForm.value.phone,
        phone: registerForm.value.phone,
        college: registerForm.value.college,
        className: registerForm.value.className,
        password: registerForm.value.password,
      },
    })
    currentUser.value = payload.user
    saveRegisteredUser(payload.user)
    apiOnline.value = true
    loginForm.value = {
      account: registerForm.value.account,
      password: registerForm.value.password,
    }
    saveLogin('student')
  } catch (error) {
    apiOnline.value = false
    showToast(`注册失败：${error.message}`)
    return
  }

  await enterApp('home', 'student')
}

async function enterApp(page = 'home', role = 'student') {
  const mode = authMode.value
  userRole.value = role
  currentPage.value = page
  authMode.value = 'app'
  profileMenuOpen.value = false
  currentBookingId.value = null
  await loadAppData(role)
  startLiveSync()
  showToast(role === 'admin' ? '管理员登录成功' : mode === 'register' ? '注册成功，已进入系统' : '登录成功，欢迎回来')
}

function logout() {
  stopLiveSync()
  profileMenuOpen.value = false
  currentUser.value = null
  userRole.value = 'student'
  loginRole.value = 'student'
  authMode.value = 'login'
  currentPage.value = 'home'
  currentBookingId.value = null
}

function switchAccount() {
  stopLiveSync()
  profileMenuOpen.value = false
  currentUser.value = null
  userRole.value = 'student'
  loginRole.value = 'student'
  authMode.value = 'login'
  currentPage.value = 'home'
  currentBookingId.value = null
  showToast('已切换到登录界面')
}

function goPage(page) {
  if (isAdmin.value) {
    currentPage.value = adminNavItems.some((item) => item.key === page) ? page : 'admin'
    return
  }
  if (page === 'admin' && !isAdmin.value) {
    currentPage.value = 'home'
    showToast('当前学生账号无管理员权限')
    return
  }
  currentPage.value = page
}

async function openRoom(roomId) {
  selectedRoomId.value = roomId
  try {
    await loadSeats(roomId)
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    showToast(`座位数据接口不可用，继续使用演示座位：${error.message}`)
  }
  currentPage.value = 'seat'
  showToast('已切换到座位详情')
}

function selectSeat(seat) {
  if (seat.status === 'free') {
    selectedSeatId.value = seat.id
  }
}

async function reserveSeat() {
  ensureValidTimeRange()
  if (!selectedStartTime.value || !selectedEndTime.value) {
    showToast('当前日期已无可预约时段')
    return
  }
  if (activeBooking.value) {
    showToast('当前已有待签到或已签到预约，请完成后再预约新座位')
    currentPage.value = 'booking'
    return
  }
  const liveSeat = seats.value.find((seat) => seat.id === selectedSeatId.value)
  if (!liveSeat || liveSeat.status !== 'free') {
    showToast('该座位当前不可预约，请选择空闲座位')
    return
  }
  bookingStatus.value = '待签到'
  const bookingContext = {
    date: selectedDate.value,
    roomId: selectedRoom.value.id,
    roomName: selectedRoom.value.name,
    seatNo: selectedSeat.value.id,
    time: selectedTimeSlot.value,
  }
  const range = toDateTimeRange(selectedDate.value, selectedStartTime.value, selectedEndTime.value)
  try {
    const payload = await apiRequest('/bookings', {
      method: 'POST',
      body: {
        userId: currentUser.value?.id,
        roomId: bookingContext.roomId,
        seatNo: bookingContext.seatNo,
        startTime: range.startTime,
        endTime: range.endTime,
      },
    })
    await Promise.all([loadBookings(), loadRooms(), loadSeats(bookingContext.roomId)])
    const reservedRow = historyRows.value.find(
      (row) =>
        (payload.id && row.id === payload.id) ||
        (payload.booking?.id && row.id === payload.booking.id) ||
        (row.date === bookingContext.date &&
        row.room === bookingContext.roomName &&
        row.seat === bookingContext.seatNo &&
        row.time === bookingContext.time &&
        row.status === '待签到')
    )
    currentBookingId.value = reservedRow?.id || null
    bookingStatus.value = reservedRow?.status || normalizeStatus(payload.status)
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    const localBookingId = `local-${Date.now()}`
    historyRows.value = [{
      id: localBookingId,
      date: bookingContext.date,
      room: bookingContext.roomName,
      seat: bookingContext.seatNo,
      time: bookingContext.time,
      status: '待签到',
      createdAt: formatLocalDateTime(beijingNow.value),
    }, ...historyRows.value]
    currentBookingId.value = localBookingId
  }
  currentPage.value = 'booking'
  showToast(`已预约 ${bookingContext.roomName} ${bookingContext.seatNo}`)
}

async function updateBookingStatus(status) {
  const bookingId = activeBooking.value?.id

  if (bookingId && String(bookingId).startsWith('local-')) {
    bookingStatus.value = status
    const activeIndex = historyRows.value.findIndex((item) => item.id === bookingId)
    if (activeIndex >= 0) {
      const now = formatLocalDateTime(beijingNow.value)
      historyRows.value[activeIndex] = {
        ...historyRows.value[activeIndex],
        status,
        actualCheckInAt: status === '已签到' ? now : historyRows.value[activeIndex].actualCheckInAt,
        actualCheckOutAt: status === '已签退' ? now : historyRows.value[activeIndex].actualCheckOutAt,
      }
    }
    showToast(`预约状态已更新为：${status}`)
    return
  }

  if (bookingId) {
    try {
      const payload = await apiRequest(`/bookings/${bookingId}/status`, {
        method: 'PATCH',
        body: { status: toApiBookingStatus(status) },
      })
      bookingStatus.value = normalizeStatus(payload.status)
      const activeIndex = historyRows.value.findIndex((item) => item.id === bookingId)
      if (activeIndex >= 0) {
        historyRows.value[activeIndex] = {
          ...historyRows.value[activeIndex],
          status: bookingStatus.value,
          actualCheckInAt: payload.actualCheckInAt || historyRows.value[activeIndex].actualCheckInAt,
          actualCheckOutAt: payload.actualCheckOutAt || historyRows.value[activeIndex].actualCheckOutAt,
          studyMinutes: payload.studyMinutes ?? historyRows.value[activeIndex].studyMinutes,
        }
      }
      await Promise.all([loadBookings(), loadViolations(), loadRooms(), loadSeats(selectedRoomId.value)])
      apiOnline.value = true
      if (payload.violation) {
        showToast(`${payload.violation.type}，信用分扣 ${Math.abs(payload.violation.scoreChange)} 分`, 4200)
        return
      }
    } catch (error) {
      apiOnline.value = false
      showToast(`数据库更新失败，页面未保存本次操作：${error.message}`)
      return
    }
  }

  const activeIndex = historyRows.value.findIndex((item) => item.id === bookingId)
  if (activeIndex >= 0) {
    historyRows.value[activeIndex] = { ...historyRows.value[activeIndex], status: bookingStatus.value }
  }
  showToast(`预约状态已更新为：${status}`)
}

async function updateAdminBookingStatus(row, status) {
  if (!row?.id) return
  try {
    const payload = await apiRequest(`/admin/bookings/${row.id}/status`, {
      method: 'PATCH',
      body: { status: toApiBookingStatus(status) },
    })
    row.status = normalizeStatus(payload.status)
    showToast(`已将 ${row.user} 的预约更新为：${normalizeStatus(payload.status)}`)
    try {
      await refreshLiveData()
    } catch {
      row.status = normalizeStatus(payload.status)
    }
  } catch (error) {
    showToast(`更新预约失败：${error.message}`)
  }
}

async function updateAdminSeatStatus(seat, status) {
  if (!seat?.id || typeof seat.id !== 'number') {
    showToast('演示座位暂不能写入数据库')
    return
  }
  try {
    await apiRequest(`/admin/seats/${seat.id}/status`, {
      method: 'PATCH',
      body: { status },
    })
    seat.apiStatus = status
    seat.status = seatStatusLabel(status)
    showToast(`${seat.room} ${seat.seatNo} 已更新为：${seatStatusLabel(status)}`)
    try {
      await refreshLiveData()
    } catch {
      seat.apiStatus = status
      seat.status = seatStatusLabel(status)
    }
  } catch (error) {
    showToast(`更新座位失败：${error.message}`)
  }
}

function openAppealDialog(item) {
  if (!canAppealViolation(item)) return
  selectedAppealViolation.value = item
  appealForm.value = {
    reason: appealReasonOptions[0],
    customReason: '',
  }
  appealDialogOpen.value = true
}

function closeAppealDialog() {
  appealDialogOpen.value = false
  selectedAppealViolation.value = null
  appealForm.value = {
    reason: '',
    customReason: '',
  }
}

async function submitViolationAppeal(item, reason) {
  if (!item) return
  const appealReason = String(reason || '').trim()
  if (!appealReason) {
    showToast('请选择或填写申诉理由')
    return
  }
  if (!item.id || String(item.id).startsWith('local-')) {
    item.status = '申诉待处理'
    item.appealReason = appealReason
    showToast('申诉已提交，等待管理员审核')
    closeAppealDialog()
    return
  }

  try {
    const payload = await apiRequest(`/violations/${item.id}/appeal`, {
      method: 'PATCH',
      body: { userId: currentUser.value?.id, reason: appealReason },
    })
    item.status = payload.status || '申诉待处理'
    item.appealReason = appealReason
    await loadViolations()
    closeAppealDialog()
    showToast(payload.message || '申诉已提交，等待管理员审核')
  } catch (error) {
    showToast(`申诉提交失败：${error.message}`)
  }
}

async function confirmViolationAppeal() {
  await submitViolationAppeal(selectedAppealViolation.value, selectedAppealReason.value)
}

async function resolveAdminViolation(item, action = 'reject') {
  if (!item?.id) return
  try {
    const payload = await apiRequest(`/admin/violations/${item.id}/status`, {
      method: 'PATCH',
      body: { action },
    })
    item.status = payload.status
    showToast(payload.message || `申诉已处理：${payload.status}`)
    try {
      await refreshLiveData()
    } catch {
      adminViolations.value = adminViolations.value.filter((row) => row.id !== item.id)
    }
  } catch (error) {
    showToast(`复核失败：${error.message}`)
  }
}

async function handleCheckIn() {
  if (!activeBooking.value) {
    showToast('当前还没有预约')
    return
  }
  if (activeBooking.value.status === '已签到') {
    showToast('已经签到，请勿重复签到')
    return
  }
  if (activeCheckInWarning.value) {
    checkinConfirmOpen.value = true
    return
  }
  await updateBookingStatus('已签到')
}

async function confirmCheckIn() {
  checkinConfirmOpen.value = false
  await updateBookingStatus('已签到')
}

async function handleCheckOut() {
  if (!activeBooking.value) {
    showToast('当前还没有预约')
    return
  }
  if (activeBooking.value.status === '待签到') {
    showToast('请先签到后再签退')
    return
  }
  checkoutConfirmOpen.value = true
}

async function confirmCheckOut() {
  checkoutConfirmOpen.value = false
  await updateBookingStatus('已签退')
  bookingStatus.value = '暂无预约'
  currentBookingId.value = null
  showToast(`签退成功，今日学习时长 ${todayStudyDuration.value}`)
}

async function handleCancelBooking() {
  if (!activeBooking.value) {
    showToast('当前还没有预约')
    return
  }
  if (activeBooking.value.status === '已签到') {
    showToast('已签到的预约不能取消，请签退')
    return
  }
  if (activeCancelWarning.value) {
    showToast(activeCancelWarning.value, 4200)
  }
  cancelConfirmOpen.value = true
}

async function confirmCancelBooking() {
  cancelConfirmOpen.value = false
  await updateBookingStatus('已取消')
  bookingStatus.value = '暂无预约'
  currentBookingId.value = null
  showToast('预约已取消，当前暂无预约')
}

onMounted(async () => {
  clockTimer = window.setInterval(() => {
    beijingNow.value = new Date()
    ensureValidSelectedDate()
    ensureValidTimeRange()
  }, 60000)
  ensureValidSelectedDate()
  ensureValidTimeRange()
  try {
    await apiRequest('/health')
    apiOnline.value = true
  } catch {
    apiOnline.value = false
  }
})

onUnmounted(() => {
  window.clearInterval(clockTimer)
  stopLiveSync()
})

watch(selectedDate, () => {
  ensureValidSelectedDate()
  ensureValidTimeRange()
  if (!isAdmin.value && authMode.value === 'app') {
    loadSeats(selectedRoomId.value).catch((error) => {
      showToast(`座位状态同步失败：${error.message}`)
    })
  }
})

watch([selectedStartTime, selectedEndTime], () => {
  if (!isAdmin.value && authMode.value === 'app') {
    loadSeats(selectedRoomId.value).catch((error) => {
      showToast(`座位状态同步失败：${error.message}`)
    })
  }
})

watch(() => registerForm.value.college, () => {
  registerForm.value.className = ''
})

watch(adminSelectedRoomId, async () => {
  if (!isAdmin.value || authMode.value !== 'app') return
  try {
    await loadAdminSeats()
  } catch (error) {
    showToast(`座位同步失败：${error.message}`)
  }
})

watch(currentPage, () => {
  if (!showSearchBox.value) {
    searchText.value = ''
  }
  refreshLiveData()
})
</script>

<template>
  <main v-if="authMode !== 'app'" class="auth-screen">
    <section class="auth-brand">
      <div class="brand-mark">学</div>
      <h1>校园自习室<br />预约系统</h1>
      <p>在线选座、预约管理、签到签退与违规记录一体化</p>
    </section>

    <section
      class="auth-card"
      :class="{ 'auth-card--login': authMode === 'login', 'auth-card--register': authMode === 'register' }"
    >
      <div class="auth-head">
        <component :is="authMode === 'register' ? UserPlus : loginRole === 'admin' ? MonitorCog : LogIn" />
        <div>
          <h2>{{ authMode === 'register' ? '用户注册' : loginRole === 'admin' ? '管理员登录' : '用户登录' }}</h2>
          <p>
            {{
              authMode === 'register'
                ? '填写注册信息后即可预约座位'
                : loginRole === 'admin'
                  ? '请输入管理员账号和密码进入后台'
                  : '请输入账号和密码进入系统'
            }}
          </p>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="authMode === 'login' ? loginAs(loginRole) : registerAccount()">
        <label>
          <span>{{ loginRole === 'admin' && authMode === 'login' ? '管理员账号' : authMode === 'login' ? '账号' : '学号' }}</span>
          <input
            v-model="loginForm.account"
            v-if="authMode === 'login'"
            autocomplete="off"
            :placeholder="loginRole === 'admin' ? '请输入管理员账号' : '请输入账号'"
          />
          <input v-model="registerForm.account" v-else placeholder="请输入学号" />
        </label>
        <label v-if="authMode === 'register'">
          <span>姓名</span>
          <input v-model="registerForm.name" placeholder="请输入姓名" />
        </label>
        <label v-if="authMode === 'register'">
          <span>邮箱</span>
          <input v-model="registerForm.phone" type="email" placeholder="请输入邮箱" />
        </label>
        <label v-if="authMode === 'register'">
          <span>学院</span>
          <select v-model="registerForm.college">
            <option value="" disabled>请选择学院</option>
            <option v-for="college in collegeOptions" :key="college.name" :value="college.name">
              {{ college.name }}
            </option>
          </select>
        </label>
        <label v-if="authMode === 'register'">
          <span>班级</span>
          <select v-model="registerForm.className" :disabled="!registerForm.college">
            <option value="" disabled>请选择班级</option>
            <option v-for="className in currentClassOptions" :key="className" :value="className">
              {{ className }}
            </option>
          </select>
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="loginForm.password"
            v-if="authMode === 'login'"
            type="password"
            autocomplete="new-password"
            placeholder="请输入密码"
          />
          <input v-model="registerForm.password" v-else type="password" placeholder="请输入密码" />
        </label>
        <label v-if="authMode === 'register'">
          <span>确认密码</span>
          <input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" />
        </label>
        <button class="primary-action" type="submit">
          {{ authMode === 'login' ? '登录' : '注册账号' }}
        </button>
      </form>

      <button
        v-if="authMode === 'login'"
        class="admin-login"
        type="button"
        @click="switchLoginRole(loginRole === 'admin' ? 'student' : 'admin')"
      >
        <component :is="loginRole === 'admin' ? LogIn : MonitorCog" />
        {{ loginRole === 'admin' ? '返回用户登录' : '以管理员身份登录' }}
      </button>

      <button v-if="loginRole !== 'admin' || authMode === 'register'" class="text-link" @click="toggleAuthMode">
        {{ authMode === 'login' ? '没有账号？立即注册' : '已有账号，返回登录' }}
      </button>
    </section>

    <transition name="toast">
      <div v-if="toastMessage" class="toast auth-toast">
        <AlertTriangle />
        {{ toastMessage }}
      </div>
    </transition>
  </main>

  <main v-else class="app-shell" :class="{ 'app-shell--admin': isAdmin }" @click="closeFloatingMenus">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">学</div>
        <div>
          <strong>校园自习室预约系统</strong>
          <span>Study Room Booking</span>
        </div>
      </div>
      <nav>
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="{ active: currentPage === item.key }"
          @click="goPage(item.key)"
        >
          <component :is="item.icon" />
          <span>{{ item.mobileLabel || item.label }}</span>
        </button>
      </nav>
      <button class="logout" @click="logout">
        <LogOut />
        退出登陆
      </button>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <h1>{{ meta.title }}</h1>
          <p>{{ meta.subtitle }}</p>
        </div>
        <label v-if="showSearchBox" class="searchbox">
          <Search />
          <input v-model="searchText" placeholder="在此搜索" />
        </label>
        <div class="profile-wrap" @click.stop>
          <button
            class="profile"
            type="button"
            :aria-expanded="profileMenuOpen"
            aria-haspopup="menu"
            @click="profileMenuOpen = !profileMenuOpen"
          >
            <span>{{ profileInitial }}</span>
            <b>{{ isAdmin ? `管理员 ${currentProfile.id}` : `学生 ${currentProfile.id}` }}</b>
          </button>
          <transition name="menu-pop">
            <section v-if="profileMenuOpen" class="profile-menu" role="menu">
              <div class="profile-menu__head">
                <span>{{ profileInitial }}</span>
                <div>
                  <strong>{{ currentProfile.name }}</strong>
                  <small>{{ isAdmin ? '工号' : '学号' }} {{ currentProfile.id }}</small>
                </div>
              </div>
              <dl class="profile-info">
                <div>
                  <dt>学院</dt>
                  <dd>{{ currentProfile.college }}</dd>
                </div>
                <div>
                  <dt>{{ isAdmin ? '岗位' : '班级' }}</dt>
                  <dd>{{ currentProfile.className }}</dd>
                </div>
                <div>
                  <dt>邮箱</dt>
                  <dd>{{ currentProfile.phone }}</dd>
                </div>
              </dl>
              <div class="profile-actions">
                <button type="button" role="menuitem" @click="switchAccount">
                  <Repeat2 />
                  切换账号
                </button>
                <button type="button" role="menuitem" class="danger" @click="logout">
                  <LogOut />
                  退出账号
                </button>
              </div>
            </section>
          </transition>
        </div>
      </header>

      <transition name="toast">
        <div v-if="toastMessage" class="toast">
          <CheckCircle2 />
          {{ toastMessage }}
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="checkinConfirmOpen" class="confirm-mask" @click.self="checkinConfirmOpen = false">
          <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="checkin-title">
            <div class="confirm-icon">
              <AlertTriangle />
            </div>
            <h2 id="checkin-title">确认签到？</h2>
            <p>
              {{ activeCheckInWarning }}确认后系统会记录本次实际签到时间。
            </p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="checkinConfirmOpen = false">暂不签到</button>
              <button class="primary-action compact" type="button" @click="confirmCheckIn">确认签到</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="checkoutConfirmOpen" class="confirm-mask" @click.self="checkoutConfirmOpen = false">
          <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="checkout-title">
            <div class="confirm-icon">
              <CalendarCheck />
            </div>
            <h2 id="checkout-title">确认签退？</h2>
            <p>
              签退后当前预约将结束，并从当前预约区域隐藏。该记录仍会保留在预约记录中。
            </p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="checkoutConfirmOpen = false">暂不签退</button>
              <button class="primary-action compact" type="button" @click="confirmCheckOut">确认签退</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="cancelConfirmOpen" class="confirm-mask" @click.self="cancelConfirmOpen = false">
          <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
            <div class="confirm-icon">
              <XCircle />
            </div>
            <h2 id="cancel-title">确认取消预约？</h2>
            <p>
              取消后当前预约将结束，并从当前预约区域隐藏。该记录仍会保留在预约记录中。
              <strong v-if="activeCancelWarning" class="credit-warning">{{ activeCancelWarning }}</strong>
            </p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="cancelConfirmOpen = false">暂不取消</button>
              <button class="danger-action compact" type="button" @click="confirmCancelBooking">确认取消</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="appealDialogOpen && selectedAppealViolation" class="confirm-mask" @click.self="closeAppealDialog">
          <section class="confirm-dialog appeal-dialog" role="dialog" aria-modal="true" aria-labelledby="appeal-title">
            <div class="confirm-icon">
              <AlertTriangle />
            </div>
            <h2 id="appeal-title">提交违规申诉</h2>
            <p>
              针对「{{ selectedAppealViolation.type }}」提交申诉理由，管理员会在违规处理界面复核。
            </p>
            <div class="appeal-dialog__form">
              <label>
                <span>申诉理由</span>
                <select v-model="appealForm.reason">
                  <option v-for="reason in appealReasonOptions" :key="reason" :value="reason">{{ reason }}</option>
                </select>
              </label>
              <label v-if="appealForm.reason === '其他原因，手动填写'">
                <span>自定义理由</span>
                <textarea v-model="appealForm.customReason" rows="4" maxlength="160" placeholder="请简要说明申诉原因"></textarea>
              </label>
            </div>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeAppealDialog">取消</button>
              <button class="primary-action compact" type="button" @click="confirmViolationAppeal">提交申诉</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="roomEditorOpen" class="confirm-mask" @click.self="closeRoomEditor">
          <section class="confirm-dialog room-editor" role="dialog" aria-modal="true" aria-labelledby="room-editor-title">
            <div class="confirm-icon">
              <DoorOpen />
            </div>
            <h2 id="room-editor-title">{{ editingRoomId ? '编辑自习室' : '新增自习室' }}</h2>
            <div class="room-editor__form">
              <label>
                <span>自习室编号</span>
                <input v-model="roomEditorForm.id" :disabled="Boolean(editingRoomId)" placeholder="例如 new-study-room" />
              </label>
              <label>
                <span>自习室名称</span>
                <input v-model="roomEditorForm.name" placeholder="请输入自习室名称" />
              </label>
              <label>
                <span>位置</span>
                <input v-model="roomEditorForm.location" placeholder="请输入位置" />
              </label>
              <label>
                <span>开放时间</span>
                <select v-model="roomEditorForm.hours">
                  <option value="" disabled>请选择开放时间</option>
                  <option v-for="hours in roomEditorHourOptions" :key="hours" :value="hours">
                    {{ hours }}
                  </option>
                </select>
              </label>
              <label>
                <span>设施标签</span>
                <input v-model="roomEditorForm.facilities" placeholder="用顿号、逗号或空格分隔" />
              </label>
            </div>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeRoomEditor">取消</button>
              <button class="primary-action compact" type="button" @click="saveRoomEditor">保存</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="bookingDetailOpen && selectedAdminBooking" class="confirm-mask" @click.self="closeAdminBookingDetail">
          <section class="confirm-dialog booking-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="booking-detail-title">
            <div class="confirm-icon">
              <ClipboardList />
            </div>
            <div class="detail-head booking-detail-head">
              <h2 id="booking-detail-title">预约详情</h2>
              <span class="badge success">{{ selectedAdminBooking.status }}</span>
            </div>
            <dl class="booking-detail-list">
              <div>
                <dt>学生</dt>
                <dd>{{ selectedAdminBooking.user || '未知学生' }}</dd>
              </div>
              <div>
                <dt>账号</dt>
                <dd>{{ selectedAdminBooking.account || '-' }}</dd>
              </div>
              <div>
                <dt>自习室</dt>
                <dd>{{ selectedAdminBooking.room }}</dd>
              </div>
              <div>
                <dt>座位</dt>
                <dd>{{ selectedAdminBooking.seat }}</dd>
              </div>
              <div>
                <dt>日期</dt>
                <dd>{{ selectedAdminBooking.date }}</dd>
              </div>
              <div>
                <dt>时段</dt>
                <dd>{{ selectedAdminBooking.time }}</dd>
              </div>
              <div v-if="selectedAdminBooking.createdAt">
                <dt>创建时间</dt>
                <dd>{{ selectedAdminBooking.createdAt }}</dd>
              </div>
            </dl>
            <p class="booking-detail-note">{{ bookingStatusNote(selectedAdminBooking.status) }}</p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeAdminBookingDetail">关闭</button>
              <button
                v-if="selectedAdminBooking.status === '待签到'"
                class="danger-action compact"
                type="button"
                @click="updateAdminBookingStatus(selectedAdminBooking, '已取消')"
              >
                取消预约
              </button>
              <button
                v-if="selectedAdminBooking.status === '已签到'"
                class="primary-action compact"
                type="button"
                @click="updateAdminBookingStatus(selectedAdminBooking, '已签退')"
              >
                确认签退
              </button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="roomDeleteConfirmOpen && pendingDeleteRoom" class="confirm-mask" @click.self="closeRoomDeleteConfirm">
          <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="room-delete-title">
            <div class="confirm-icon">
              <AlertTriangle />
            </div>
            <h2 id="room-delete-title">删除自习室？</h2>
            <p>
              将删除「{{ pendingDeleteRoom.name }}」及其座位信息。若该自习室已有预约记录，系统会阻止删除以保留历史数据。
            </p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeRoomDeleteConfirm">取消</button>
              <button class="danger-action compact" type="button" @click="confirmDeleteRoom">确认删除</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="userDeleteConfirmOpen && pendingDeleteUser" class="confirm-mask" @click.self="closeUserDeleteConfirm">
          <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="user-delete-title">
            <div class="confirm-icon">
              <AlertTriangle />
            </div>
            <h2 id="user-delete-title">删除学生账号？</h2>
            <p>
              将删除「{{ pendingDeleteUser.name }}」的学生账号。若该学生已有预约或违规记录，系统会阻止删除以保留历史数据。
            </p>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeUserDeleteConfirm">取消</button>
              <button class="danger-action compact" type="button" @click="confirmDeleteUser">确认删除</button>
            </div>
          </section>
        </div>
      </transition>

      <transition name="modal-fade">
        <div v-if="userDetailOpen && selectedAdminUser" class="confirm-mask" @click.self="closeUserDetail">
          <section class="confirm-dialog user-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="user-detail-title">
            <div class="confirm-icon">
              <Users />
            </div>
            <div class="detail-head booking-detail-head">
              <h2 id="user-detail-title">学生账号详情</h2>
              <span class="badge success">{{ selectedAdminUser.status }}</span>
            </div>
            <dl class="booking-detail-list">
              <div>
                <dt>账号</dt>
                <dd>{{ selectedAdminUser.account }}</dd>
              </div>
              <div>
                <dt>预约次数</dt>
                <dd>{{ selectedAdminUser.bookings }} 次</dd>
              </div>
              <div>
                <dt>信用分</dt>
                <dd>{{ selectedAdminUser.credit }}</dd>
              </div>
              <div>
                <dt>账号状态</dt>
                <dd>{{ selectedAdminUser.status }}</dd>
              </div>
            </dl>
            <div class="room-editor__form user-detail-form">
              <label>
                <span>姓名</span>
                <input v-model="userEditorForm.name" placeholder="请输入姓名" />
              </label>
              <label>
                <span>学院</span>
                <input v-model="userEditorForm.college" placeholder="请输入学院" />
              </label>
              <label>
                <span>班级</span>
                <input v-model="userEditorForm.className" placeholder="请输入班级" />
              </label>
              <label>
                <span>邮箱 / 电话</span>
                <input v-model="userEditorForm.phone" placeholder="请输入邮箱或电话" />
              </label>
              <label class="user-detail-form__wide">
                <span>新密码</span>
                <input v-model="userEditorForm.password" type="password" autocomplete="new-password" placeholder="留空则不修改密码" />
              </label>
            </div>
            <div class="confirm-actions">
              <button class="secondary-action compact" type="button" @click="closeUserDetail">关闭</button>
              <button class="primary-action compact" type="button" @click="saveUserDetail">保存修改</button>
            </div>
          </section>
        </div>
      </transition>

      <section class="content">
        <template v-if="currentPage === 'home'">
          <div class="welcome">
            <div>
              <h2>下午好，{{ currentProfile.name }}</h2>
              <p>今日开放自习室 {{ rooms.length }} 间，当前可预约座位 {{ roomStats.free }} 个</p>
            </div>
            <button class="primary-action compact" @click="currentPage = 'rooms'">
              开始预约
              <ChevronRight />
            </button>
          </div>

          <div class="stat-grid">
            <article v-for="item in filteredHomeStats" :key="item.label" class="card stat-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <em>{{ item.note }}</em>
            </article>
          </div>

          <div class="entry-grid">
            <article v-for="item in filteredHomeEntries" :key="item.page" class="card entry-card" @click="goPage(item.page)">
              <component :is="item.icon" />
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </article>
            <article v-if="searchKeyword && filteredHomeStats.length === 0 && filteredHomeEntries.length === 0" class="card empty-state">
              <Search />
              <h3>没有找到匹配内容</h3>
              <p>可以输入完整名称精确查询，也可以输入部分关键词模糊查询。</p>
            </article>
          </div>
        </template>

        <template v-else-if="currentPage === 'rooms'">
          <section class="booking-selector" aria-label="预约时间选择">
            <label>
              <span>预约日期</span>
              <input v-model="selectedDate" type="date" :min="minBookingDate" />
            </label>
            <label>
              <span>开始时间</span>
              <div class="time-picker" @click.stop>
                <button class="time-picker__button" type="button" @click="toggleTimePicker('rooms-start')">
                  {{ selectedStartTime || noTimeSlotText }}
                  <ChevronRight />
                </button>
                <div v-if="timePickerOpen === 'rooms-start'" class="time-picker__menu">
                  <button
                    v-for="time in startTimeOptions"
                    :key="time"
                    :class="{ active: selectedStartTime === time }"
                    type="button"
                    @click="selectStartTime(time)"
                  >
                    {{ time }}
                  </button>
                  <span v-if="startTimeOptions.length === 0">{{ noTimeSlotText }}</span>
                </div>
              </div>
            </label>
            <label>
              <span>结束时间</span>
              <div class="time-picker" @click.stop>
                <button class="time-picker__button" type="button" @click="toggleTimePicker('rooms-end')">
                  {{ selectedEndTime || (!selectedStartTime || endTimeOptions.length === 0 ? noTimeSlotText : '请选择') }}
                  <ChevronRight />
                </button>
                <div v-if="timePickerOpen === 'rooms-end'" class="time-picker__menu">
                  <button
                    v-for="time in endTimeOptions"
                    :key="time"
                    :class="{ active: selectedEndTime === time }"
                    type="button"
                    @click="selectEndTime(time)"
                  >
                    {{ time }}
                  </button>
                  <span v-if="endTimeOptions.length === 0">{{ noTimeSlotText }}</span>
                </div>
              </div>
            </label>
          </section>
          <div class="filter-row">
            <button
              v-for="option in filterOptions"
              :key="option.key"
              :class="['pill', { active: currentFilter === option.key }]"
              @click="currentFilter = option.key"
            >
              {{ option.label }}
            </button>
          </div>
          <div class="room-list">
            <article v-for="room in filteredRooms" :key="room.id" class="card room-row">
              <div>
                <h3>{{ room.name }}</h3>
                <p><MapPin /> {{ room.location }}</p>
                <div class="room-tags">
                  <span v-for="facility in room.facilities" :key="facility">{{ facility }}</span>
                </div>
              </div>
              <div class="room-meta">
                <Clock />
                {{ room.hours }}
              </div>
              <div class="seat-summary">
                <span class="free">空闲 {{ room.seats.free }}</span>
                <span class="used">已占 {{ room.seats.used }}</span>
                <span class="fix">维修 {{ room.seats.maintenance }}</span>
              </div>
              <button class="primary-action compact" @click="openRoom(room.id)">查看座位</button>
            </article>
            <article v-if="filteredRooms.length === 0" class="card empty-state">
              <Search />
              <h3>没有找到匹配的自习室</h3>
              <p>可以换个关键词，或者切回“全部”查看所有开放自习室。</p>
            </article>
          </div>
        </template>

        <template v-else-if="currentPage === 'seat'">
          <div class="seat-layout">
            <section class="card seat-map-card">
              <div class="section-title">
                <h2>{{ selectedRoom.name }} 座位平面图</h2>
              </div>
              <div class="seat-status-strip">
                <span class="free">空闲 {{ seatStats.free }}</span>
                <span class="booked">已预约 {{ seatStats.booked }}</span>
                <span class="used">已占 {{ seatStats.used }}</span>
                <span class="maintenance">维修 {{ seatStats.maintenance }}</span>
              </div>
              <div class="seat-grid">
                <button
                  v-for="seat in filteredSeats"
                  :key="seat.id"
                  :class="['seat', seat.status, { selected: seat.id === selectedSeatId }]"
                  :disabled="seat.status !== 'free'"
                  @click="selectSeat(seat)"
                >
                  {{ seat.id }}
                </button>
                <div v-if="filteredSeats.length === 0" class="seat-empty">
                  没有找到匹配的座位
                </div>
              </div>
            </section>

            <aside class="card detail-card">
              <div class="detail-head">
                <h2>座位 {{ selectedSeat.id }}</h2>
                <span class="badge success">可预约</span>
              </div>
              <dl>
                <div>
                  <dt>自习室</dt>
                  <dd>{{ selectedRoom.name }}</dd>
                </div>
                <div>
                  <dt>位置</dt>
                  <dd>靠窗第 1 排</dd>
                </div>
                <div>
                  <dt>配置</dt>
                  <dd>{{ selectedRoom.facilities.join(' / ') }}</dd>
                </div>
                <div>
                  <dt>可预约时段</dt>
                  <dd class="slot-field">
                    <div class="slot-field__controls">
                      <div class="time-picker" @click.stop>
                        <button class="time-picker__button" type="button" @click="toggleTimePicker('detail-start')">
                          {{ selectedStartTime || noTimeSlotText }}
                          <ChevronRight />
                        </button>
                        <div v-if="timePickerOpen === 'detail-start'" class="time-picker__menu">
                          <button
                            v-for="time in startTimeOptions"
                            :key="time"
                            :class="{ active: selectedStartTime === time }"
                            type="button"
                            @click="selectStartTime(time)"
                          >
                            {{ time }}
                          </button>
                          <span v-if="startTimeOptions.length === 0">{{ noTimeSlotText }}</span>
                        </div>
                      </div>
                      <div class="time-picker" @click.stop>
                        <button class="time-picker__button" type="button" @click="toggleTimePicker('detail-end')">
                          {{ selectedEndTime || (!selectedStartTime || endTimeOptions.length === 0 ? noTimeSlotText : '请选择') }}
                          <ChevronRight />
                        </button>
                        <div v-if="timePickerOpen === 'detail-end'" class="time-picker__menu">
                          <button
                            v-for="time in endTimeOptions"
                            :key="time"
                            :class="{ active: selectedEndTime === time }"
                            type="button"
                            @click="selectEndTime(time)"
                          >
                            {{ time }}
                          </button>
                          <span v-if="endTimeOptions.length === 0">{{ noTimeSlotText }}</span>
                        </div>
                      </div>
                    </div>
                    <small>{{ selectedDate }}</small>
                  </dd>
                </div>
              </dl>
              <button class="primary-action" @click="reserveSeat">立即预约</button>
              <div class="legend">
                <span><i class="free"></i>空闲</span>
                <span><i class="booked"></i>已预约</span>
                <span><i class="used"></i>已占</span>
                <span><i class="maintenance"></i>维修</span>
              </div>
            </aside>
          </div>
        </template>

        <template v-else-if="currentPage === 'booking'">
          <div class="booking-grid">
            <article v-if="activeBooking" class="card active-booking">
              <div class="detail-head">
                <h2>当前预约</h2>
                <span class="badge warning">{{ activeBooking.status }}</span>
              </div>
              <p>{{ activeBooking.room }} · {{ activeBooking.seat }}</p>
              <p>{{ activeBooking.time }}</p>
              <div class="action-row">
                <button
                  v-if="activeBooking.status === '待签到'"
                  class="primary-action compact"
                  @click="handleCheckIn"
                >
                  <CheckCircle2 />
                  签到
                </button>
                <button
                  v-if="activeBooking.status === '已签到'"
                  class="primary-action compact"
                  @click="handleCheckOut"
                >
                  签退
                </button>
                <button v-if="activeBooking.status === '待签到'" class="danger-action compact" @click="handleCancelBooking">
                  <XCircle />
                  取消
                </button>
              </div>
            </article>
            <article v-else class="card active-booking empty-booking">
              <CalendarCheck />
              <h2>还没有预约</h2>
              <p>当前没有待签到或已签到的预约，预约成功后会在这里显示。</p>
              <button class="primary-action compact" @click="goPage('rooms')">
                去预约
                <ChevronRight />
              </button>
            </article>
            <article class="card booking-table">
              <h2>预约记录</h2>
              <div v-for="row in filteredHistoryRows" :key="row.id || `${row.createdAt}-${row.date}-${row.seat}-${row.time}`" class="table-row">
                <span>{{ row.date }}</span>
                <strong>{{ row.room }} / {{ row.seat }}</strong>
                <span>{{ row.time }}</span>
                <em>{{ row.status }}</em>
              </div>
              <div v-if="filteredHistoryRows.length === 0" class="empty-inline">
                没有找到匹配的预约记录
              </div>
            </article>
          </div>
        </template>

        <template v-else-if="currentPage === 'violations'">
          <div class="violation-grid">
            <article class="card credit-card">
              <h2>预约信用状态</h2>
              <strong>{{ creditScore }}</strong>
              <p>{{ creditState.text }}</p>
              <span :class="['badge', creditState.badgeClass]">{{ creditState.label }}</span>
              <div class="credit-summary">
                <span>初始 100 分</span>
                <span>当前扣分 {{ Math.abs(creditDelta) }}</span>
              </div>
            </article>
            <article class="card credit-rules">
              <h2>信用分规则</h2>
              <div class="rule-grid">
                <div v-for="rule in creditRules" :key="rule.title" class="rule-item">
                  <strong>{{ rule.title }}</strong>
                  <p>{{ rule.text }}</p>
                </div>
              </div>
            </article>
            <article class="card violation-list">
              <h2>违规信息</h2>
              <div v-for="item in filteredViolations" :key="`${item.date}-${item.type}`" class="violation-row">
                <div>
                  <strong>{{ item.type }}</strong>
                  <p>{{ item.reason }}</p>
                  <small v-if="item.appealReason">申诉理由：{{ item.appealReason }}</small>
                  <small v-if="violationAppealText(item)">{{ violationAppealText(item) }}</small>
                </div>
                <span>{{ item.date }}</span>
                <b>{{ getViolationScoreChange(item) }}分</b>
                <em>{{ item.status }}</em>
                <button
                  class="appeal-action"
                  type="button"
                  :disabled="!canAppealViolation(item)"
                  @click="openAppealDialog(item)"
                >
                  {{ violationAppealActionLabel(item) }}
                </button>
              </div>
              <div v-if="filteredViolations.length === 0" class="empty-inline">
                没有找到匹配的违规记录
              </div>
            </article>
          </div>
        </template>

        <template v-else-if="currentPage === 'admin'">
          <div class="stat-grid">
            <article class="card stat-card">
              <span>今日预约</span>
              <strong>{{ adminStats.todayBookings }}</strong>
              <em>较昨日 +24</em>
            </article>
            <article class="card stat-card">
              <span>签到率</span>
              <strong>{{ adminStats.checkRate }}%</strong>
              <em>稳定</em>
            </article>
            <article class="card stat-card">
              <span>空闲座位</span>
              <strong>{{ adminStats.freeSeats || roomStats.free }}</strong>
              <em>实时</em>
            </article>
            <article class="card stat-card">
              <span>违规待处理</span>
              <strong>{{ adminStats.pendingViolations }}</strong>
              <em>需复核</em>
            </article>
          </div>

          <div class="admin-grid">
            <article v-for="item in filteredAdminModules" :key="item.title" class="card admin-card">
              <component :is="item.icon" />
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.text }}</p>
              </div>
              <button class="secondary-action compact" @click="goPage(item.page)">管理</button>
            </article>
            <article v-if="filteredAdminModules.length === 0" class="card empty-state">
              <Search />
              <h3>没有找到匹配的管理功能</h3>
              <p>可以输入模块名称或说明中的关键词。</p>
            </article>
          </div>

          <article class="card todo-card">
            <Wrench />
            <div>
              <h3>待处理事项</h3>
              <p>图书馆 B 区 4 个座位报修待确认 · 3 条违规记录待复核 · 明德楼 302 需更新开放时间</p>
            </div>
            <button class="primary-action compact" @click="goPage('adminViolations')">去处理</button>
          </article>
        </template>

        <template v-else-if="currentPage === 'adminRooms'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>自习室开放维护</h2>
                <p>按教学楼查看开放时间、容量和实时使用率。</p>
              </div>
              <button class="primary-action compact" @click="openRoomEditor()">新增自习室</button>
            </div>
            <div class="admin-table card">
              <div class="admin-table__head admin-table__room">
                <span>自习室</span>
                <span>位置</span>
                <span>开放时间</span>
                <span>容量</span>
                <span>使用率</span>
                <span>操作</span>
              </div>
              <div v-for="room in adminRoomRows" :key="room.id" class="admin-table__row admin-table__room">
                <strong>{{ room.name }}</strong>
                <span>{{ room.location }}</span>
                <span>{{ room.hours }}</span>
                <span>{{ room.total }} 座</span>
                <div class="meter"><i :style="{ '--meter': `${room.usage}%` }"></i><b>{{ room.usage }}%</b></div>
                <div class="admin-row-actions">
                  <button class="secondary-action compact" @click="openRoomEditor(room)">编辑</button>
                  <button class="danger-action compact" @click="openRoomDeleteConfirm(room)">删除</button>
                </div>
              </div>
            </div>
          </section>
        </template>

        <template v-else-if="currentPage === 'adminSeats'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>座位状态巡检</h2>
                <p>筛选自习室，统一维护座位占用、预约和设备状态。</p>
              </div>
              <label class="admin-select">
                <span>自习室</span>
                <select v-model="adminSelectedRoomId">
                  <option v-for="room in adminRoomOptions" :key="room.id" :value="room.id">{{ room.name }}</option>
                </select>
              </label>
            </div>
            <div class="seat-status-strip admin-seat-strip">
              <span class="free">空闲 {{ seatStats.free }}</span>
              <span class="booked">已预约 {{ seatStats.booked }}</span>
              <span class="used">已占 {{ seatStats.used }}</span>
              <span class="maintenance">维修 {{ seatStats.maintenance }}</span>
            </div>
            <div class="admin-seat-grid">
              <article v-for="seat in adminSeatRows" :key="seat.id" class="card admin-seat-card">
                <strong>{{ seat.seatNo }}</strong>
                <span :class="['badge', seat.status === '空闲' ? 'success' : seat.status === '维修' ? 'danger' : 'warning']">
                  {{ seat.status }}
                </span>
                <p>{{ seat.room }} · {{ seat.area }}</p>
                <em>{{ seat.equipment }}</em>
                <button
                  class="secondary-action compact"
                  @click="updateAdminSeatStatus(seat, seat.apiStatus === 'maintenance' ? 'free' : 'maintenance')"
                >
                  {{ seat.apiStatus === 'maintenance' ? '恢复空闲' : '设为维修' }}
                </button>
              </article>
            </div>
            <article class="card todo-card">
              <Wrench />
              <div>
                <h3>报修队列</h3>
                <p>{{ adminRepairRows.map((row) => `${row.room} ${row.seat} ${row.issue}`).join(' · ') }}</p>
              </div>
              <button class="primary-action compact" @click="showToast('已批量标记报修待确认')">批量处理</button>
            </article>
          </section>
        </template>

        <template v-else-if="currentPage === 'adminBookings'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>预约与签到记录</h2>
                <p>集中查看学生预约、签到、签退和取消状态。</p>
              </div>
              <button class="secondary-action compact" @click="showToast('预约记录已导出')">导出记录</button>
            </div>
            <div class="admin-table card">
              <div class="admin-table__head admin-table__booking">
                <span>学生</span>
                <span>自习室 / 座位</span>
                <span>日期</span>
                <span>时段</span>
                <span>状态</span>
                <span>操作</span>
              </div>
              <div v-for="row in adminBookingRows" :key="`${row.date}-${row.account}-${row.seat}`" class="admin-table__row admin-table__booking">
                <strong>{{ row.user }} · {{ row.account }}</strong>
                <span>{{ row.room }} / {{ row.seat }}</span>
                <span>{{ row.date }}</span>
                <span>{{ row.time }}</span>
                <em>{{ row.status }}</em>
                <div class="admin-row-actions">
                  <button class="secondary-action compact" @click="openAdminBookingDetail(row)">详情</button>
                  <button
                    v-if="row.status === '待签到'"
                    class="danger-action compact"
                    @click="updateAdminBookingStatus(row, '已取消')"
                  >
                    取消
                  </button>
                  <button
                    v-if="row.status === '已签到'"
                    class="primary-action compact"
                    @click="updateAdminBookingStatus(row, '已签退')"
                  >
                    签退
                  </button>
                </div>
              </div>
            </div>
          </section>
        </template>

        <template v-else-if="currentPage === 'adminUsers'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>学生账号维护</h2>
                <p>查看账号、学院班级、预约次数和信用状态。</p>
              </div>
              <button class="primary-action compact" @click="showToast('已打开新增用户表单')">新增用户</button>
            </div>
            <div class="admin-table card">
              <div class="admin-table__head admin-table__user">
                <span>账号</span>
                <span>姓名</span>
                <span>学院 / 班级</span>
                <span>预约次数</span>
                <span>信用分</span>
                <span>状态</span>
                <span>操作</span>
              </div>
              <div v-for="user in adminUserRows" :key="user.account" class="admin-table__row admin-table__user">
                <strong>{{ user.account }}</strong>
                <span>{{ user.name }}</span>
                <span>{{ user.college }} / {{ user.className }}</span>
                <span>{{ user.bookings }} 次</span>
                <b>{{ user.credit }}</b>
                <em>{{ user.status }}</em>
                <div class="admin-row-actions">
                  <button class="secondary-action compact" @click="openUserDetail(user)">详情</button>
                  <button class="danger-action compact" @click="openUserDeleteConfirm(user)">删除</button>
                </div>
              </div>
            </div>
          </section>
        </template>

        <template v-else-if="currentPage === 'adminViolations'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>违规复核中心</h2>
                <p>处理迟到、临近取消、爽约和申诉记录。</p>
              </div>
              <button class="secondary-action compact" @click="showToast('违规策略已同步')">同步规则</button>
            </div>
            <div class="admin-table card">
              <div class="admin-table__head admin-table__violation">
                <span>学生</span>
                <span>违规类型</span>
                <span>原因</span>
                <span>申诉理由</span>
                <span>扣分</span>
                <span>状态</span>
                <span>操作</span>
              </div>
              <div v-for="item in adminViolationRows" :key="`${item.account}-${item.date}-${item.type}`" class="admin-table__row admin-table__violation">
                <strong>{{ item.user }} · {{ item.account }}</strong>
                <span>{{ item.type }}</span>
                <span>{{ item.reason }}</span>
                <span>{{ item.appealReason || '未填写' }}</span>
                <b>{{ getViolationScoreChange(item) }} 分</b>
                <em>{{ item.status }}</em>
                <div class="admin-row-actions">
                  <button class="danger-action compact" @click="resolveAdminViolation(item, 'reject')">驳回</button>
                  <button class="primary-action compact" @click="resolveAdminViolation(item, 'revoke')">撤回违规</button>
                </div>
              </div>
              <div v-if="adminViolationRows.length === 0" class="empty-inline">
                暂无学生申诉的违规订单
              </div>
            </div>
          </section>
        </template>

        <template v-else-if="currentPage === 'adminReports'">
          <section class="admin-module">
            <div class="admin-module__toolbar">
              <div>
                <h2>运营数据报表</h2>
                <p>追踪使用率、签到率和高峰时段，为开放策略提供依据。</p>
              </div>
              <button class="secondary-action compact" @click="showToast('报表已生成')">生成报表</button>
            </div>
            <div class="report-grid">
              <article class="card report-card">
                <span>平均使用率</span>
                <strong>76%</strong>
                <p>较上周提升 8%，晚间峰值明显。</p>
              </article>
              <article class="card report-card">
                <span>签到完成率</span>
                <strong>{{ adminStats.checkRate }}%</strong>
                <p>爽约率保持在 4% 以下。</p>
              </article>
              <article class="card report-card">
                <span>设备完好率</span>
                <strong>95%</strong>
                <p>报修集中在图书馆 B 区。</p>
              </article>
            </div>
            <div class="card report-panel">
              <h3>高峰时段</h3>
              <div v-for="row in reportRows" :key="row.label" class="report-row">
                <span>{{ row.label }}</span>
                <div class="meter"><i :style="{ '--meter': `${row.value}%` }"></i><b>{{ row.value }}%</b></div>
                <em>{{ row.note }}</em>
              </div>
            </div>
          </section>
        </template>

        <section v-if="currentPage === 'booking'" class="account-footer" aria-label="账户操作">
          <div>
            <strong>{{ currentProfile.name }}</strong>
            <span>{{ isAdmin ? '管理员' : '学生' }} {{ currentProfile.id }}</span>
          </div>
          <div class="account-footer__actions">
            <button type="button" class="secondary-action compact" @click="switchAccount">
              <Repeat2 />
              切换账号
            </button>
            <button type="button" class="danger-action compact" @click="logout">
              <LogOut />
              退出账户
            </button>
          </div>
        </section>
      </section>
    </section>

    <nav v-if="!isAdmin" class="mobile-nav">
      <button
        v-for="item in navItems.slice(0, 4)"
        :key="item.key"
        :class="{ active: currentPage === item.key }"
        @click="goPage(item.key)"
      >
        <component :is="item.icon" />
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </main>
</template>
