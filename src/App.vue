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
const checkoutConfirmOpen = ref(false)
const timePickerOpen = ref('')
const beijingNow = ref(new Date())
const currentUser = ref(null)
const apiOnline = ref(false)
const adminStats = ref({
  todayBookings: 328,
  checkRate: 87,
  freeSeats: 120,
  pendingViolations: 3,
})
const LOGIN_CACHE_KEY = 'study-room-last-login'

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

const loginForm = ref(readSavedLogin('student'))
const registerForm = ref({
  account: '20230218',
  name: '林同学',
  phone: '13800000000',
  className: '软件工程 2301',
  password: '123456',
  confirmPassword: '123456',
})
let toastTimer
let clockTimer

const allNavItems = [
  { key: 'home', label: '主页', icon: LayoutDashboard },
  { key: 'rooms', label: '自习室', icon: DoorOpen },
  { key: 'seat', label: '座位详情', icon: BookOpen },
  { key: 'booking', label: '我的预约', mobileLabel: '我的', icon: CalendarCheck },
  { key: 'violations', label: '违规记录', icon: AlertTriangle },
  { key: 'admin', label: '管理员', icon: MonitorCog },
]

const pageMeta = {
  home: { title: '主页界面', subtitle: '系统功能入口与今日学习状态' },
  rooms: { title: '自习室列表界面', subtitle: '展示自习室和座位状态' },
  seat: { title: '座位详情界面', subtitle: '座位信息和预约按钮' },
  booking: { title: '我的预约界面', subtitle: '预约记录、签到签退、取消' },
  violations: { title: '违规记录界面', subtitle: '违规信息展示' },
  admin: { title: '管理员后台界面', subtitle: '管理功能页面' },
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
  { title: '自习室管理', text: '新增、编辑开放时间与位置', icon: DoorOpen },
  { title: '座位管理', text: '维护座位状态与设备信息', icon: BookOpen },
  { title: '预约管理', text: '查看预约、签到签退记录', icon: ClipboardList },
  { title: '用户管理', text: '学生账号和权限维护', icon: Users },
  { title: '违规处理', text: '审核违规记录和限制策略', icon: AlertTriangle },
  { title: '数据报表', text: '统计使用率与高峰时段', icon: BarChart3 },
]

const filterOptions = [
  { key: 'all', label: '全部' },
  { key: 'free', label: '空闲较多' },
  { key: 'openLate', label: '近期开门' },
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
  phone: '138****0000',
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
const navItems = computed(() =>
  isAdmin.value ? allNavItems.filter((item) => item.key === 'admin') : allNavItems.filter((item) => item.key !== 'admin'),
)
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
const activeBooking = computed(() => {
  const row = historyRows.value.find((item) => item.status === '待签到' || item.status === '已签到')
  if (!row) return null

  return {
    id: row.id,
    date: row.date,
    room: row.room,
    seat: row.seat,
    time: row.time,
    status: row.status,
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
const searchKeyword = computed(() => normalizeSearchValue(searchText.value))
const homeStatCards = computed(() => [
  { label: '可预约座位', value: roomStats.value.free, note: '空闲' },
  { label: '今日预约', value: historyRows.value.length, note: bookingStatus.value },
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
      (currentFilter.value === 'openLate' && room.hours.endsWith('23:00')) ||
      (currentFilter.value === 'power' && room.facilities.includes('插座'))
    return matchesKeyword && matchesFilter
  })
})
const filteredSeats = computed(() =>
  seats.value.filter((seat) => matchesSearch([seat.id, seat.status, seatStatusLabel(seat.status)])),
)
const filteredHistoryRows = computed(() =>
  historyRows.value.filter((row) => matchesSearch([row.date, row.room, row.seat, row.time, row.status])),
)
const filteredViolations = computed(() =>
  violations.value.filter((item) => matchesSearch([item.date, item.type, item.reason, item.status])),
)
const filteredAdminModules = computed(() =>
  adminModules.filter((item) => matchesSearch([item.title, item.text])),
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
const selectedTimeSlot = computed(() => `${selectedStartTime.value}-${selectedEndTime.value}`)
const selectedSlotLabel = computed(() => `${selectedDate.value} ${selectedTimeSlot.value}`)

function normalizeSearchValue(value) {
  return String(value ?? '').trim().toLowerCase()
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

function getViolationScoreChange(item) {
  if (Number.isFinite(Number(item.scoreChange))) return Number(item.scoreChange)
  if (item.type.includes('爽约')) return -12
  if (item.type.includes('取消')) return -5
  if (item.type.includes('占座')) return -6
  if (item.type.includes('迟到')) return -5
  return 0
}

function showToast(message) {
  toastMessage.value = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
  }, 2200)
}

async function loadRooms() {
  const payload = await apiRequest('/rooms')
  rooms.value = payload.rooms
  if (payload.rooms[0] && !rooms.value.some((room) => room.id === selectedRoomId.value)) {
    selectedRoomId.value = payload.rooms[0].id
  }
}

async function loadSeats(roomId = selectedRoomId.value) {
  const payload = await apiRequest(`/rooms/${roomId}/seats`)
  seats.value = payload.seats
  const firstFreeSeat = payload.seats.find((seat) => seat.status === 'free')
  if (firstFreeSeat && !payload.seats.some((seat) => seat.id === selectedSeatId.value && seat.status === 'free')) {
    selectedSeatId.value = firstFreeSeat.id
  }
}

async function loadBookings(userId = currentUser.value?.id) {
  if (!userId) return

  const payload = await apiRequest(`/bookings/${userId}`)
  historyRows.value = payload.bookings.map((row) => ({
    ...row,
    status: normalizeStatus(row.status),
  }))
  bookingStatus.value = activeBooking.value?.status || '暂无预约'
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

async function loadAppData(role = userRole.value) {
  try {
    await loadRooms()
    await loadSeats()
    if (role === 'admin') {
      await loadAdminStats()
    } else {
      await Promise.all([loadBookings(), loadViolations()])
    }
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    showToast(`数据库未连接，当前使用演示数据：${error.message}`)
  }
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
        phone: registerForm.value.phone,
        className: registerForm.value.className,
        password: registerForm.value.password,
      },
    })
    currentUser.value = payload.user
    apiOnline.value = true
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
  await loadAppData(role)
  showToast(role === 'admin' ? '管理员登录成功' : mode === 'register' ? '注册成功，已进入系统' : '登录成功，欢迎回来')
}

function logout() {
  profileMenuOpen.value = false
  currentUser.value = null
  userRole.value = 'student'
  loginRole.value = 'student'
  authMode.value = 'login'
  currentPage.value = 'home'
}

function switchAccount() {
  profileMenuOpen.value = false
  currentUser.value = null
  userRole.value = 'student'
  loginRole.value = 'student'
  authMode.value = 'login'
  currentPage.value = 'home'
  showToast('已切换到登录界面')
}

function goPage(page) {
  if (isAdmin.value) {
    currentPage.value = 'admin'
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
  bookingStatus.value = '待签到'
  ensureValidTimeRange()
  if (!selectedStartTime.value || !selectedEndTime.value) {
    showToast('当前日期已无可预约时段')
    return
  }
  const range = toDateTimeRange(selectedDate.value, selectedStartTime.value, selectedEndTime.value)
  try {
    const payload = await apiRequest('/bookings', {
      method: 'POST',
      body: {
        userId: currentUser.value?.id,
        roomId: selectedRoom.value.id,
        seatNo: selectedSeat.value.id,
        startTime: range.startTime,
        endTime: range.endTime,
      },
    })
    await Promise.all([loadBookings(), loadRooms(), loadSeats(selectedRoom.value.id)])
    bookingStatus.value = normalizeStatus(payload.status)
    apiOnline.value = true
  } catch (error) {
    apiOnline.value = false
    historyRows.value[0] = {
      ...historyRows.value[0],
      id: historyRows.value[0]?.id,
      date: selectedDate.value,
      room: selectedRoom.value.name,
      seat: selectedSeat.value.id,
      time: selectedTimeSlot.value,
      status: '待签到',
    }
  }
  currentPage.value = 'booking'
  showToast(`已预约 ${selectedRoom.value.name} ${selectedSeat.value.id}`)
}

async function updateBookingStatus(status) {
  bookingStatus.value = status
  const bookingId = activeBooking.value?.id

  if (bookingId) {
    try {
      const payload = await apiRequest(`/bookings/${bookingId}/status`, {
        method: 'PATCH',
        body: { status: toApiBookingStatus(status) },
      })
      bookingStatus.value = normalizeStatus(payload.status)
      await Promise.all([loadBookings(), loadViolations(), loadRooms(), loadSeats(selectedRoomId.value)])
      apiOnline.value = true
      if (payload.violation) {
        showToast(`${payload.violation.type}，信用分 ${payload.violation.scoreChange}`)
        return
      }
    } catch (error) {
      apiOnline.value = false
      showToast(`数据库更新失败，已先更新页面状态：${error.message}`)
    }
  }

  const activeIndex = historyRows.value.findIndex((item) => item.id === bookingId)
  if (activeIndex >= 0) {
    historyRows.value[activeIndex] = { ...historyRows.value[activeIndex], status: bookingStatus.value }
  }
  showToast(`预约状态已更新为：${status}`)
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
  showToast('签退成功，当前暂无预约')
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
  await updateBookingStatus('已取消')
  bookingStatus.value = '暂无预约'
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
})

watch(selectedDate, () => {
  ensureValidSelectedDate()
  ensureValidTimeRange()
})

watch(currentPage, () => {
  if (!showSearchBox.value) {
    searchText.value = ''
  }
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
                  : '请输入学号和密码进入系统'
            }}
          </p>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="authMode === 'login' ? loginAs(loginRole) : registerAccount()">
        <label>
          <span>{{ loginRole === 'admin' && authMode === 'login' ? '管理员账号' : '学号' }}</span>
          <input
            v-model="loginForm.account"
            v-if="authMode === 'login'"
            autocomplete="off"
            :placeholder="loginRole === 'admin' ? '请输入管理员账号' : '请输入学号'"
          />
          <input v-model="registerForm.account" v-else />
        </label>
        <label v-if="authMode === 'register'">
          <span>姓名</span>
          <input v-model="registerForm.name" />
        </label>
        <label v-if="authMode === 'register'">
          <span>手机号</span>
          <input v-model="registerForm.phone" />
        </label>
        <label v-if="authMode === 'register'">
          <span>学院 / 班级</span>
          <input v-model="registerForm.className" />
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
          <input v-model="registerForm.password" v-else type="password" />
        </label>
        <label v-if="authMode === 'register'">
          <span>确认密码</span>
          <input v-model="registerForm.confirmPassword" type="password" />
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
            <span>{{ isAdmin ? '管' : '林' }}</span>
            <b>{{ isAdmin ? `管理员 ${currentProfile.id}` : `学生 ${currentProfile.id}` }}</b>
          </button>
          <transition name="menu-pop">
            <section v-if="profileMenuOpen" class="profile-menu" role="menu">
              <div class="profile-menu__head">
                <span>{{ isAdmin ? '管' : '林' }}</span>
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
                  <dt>手机号</dt>
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
                  {{ selectedStartTime || '今日已无可选' }}
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
                  <span v-if="startTimeOptions.length === 0">今日已无可预约时段</span>
                </div>
              </div>
            </label>
            <label>
              <span>结束时间</span>
              <div class="time-picker" @click.stop>
                <button class="time-picker__button" type="button" @click="toggleTimePicker('rooms-end')">
                  {{ selectedEndTime || '请选择' }}
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
                          {{ selectedStartTime || '今日已无可选' }}
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
                          <span v-if="startTimeOptions.length === 0">今日已无可预约时段</span>
                        </div>
                      </div>
                      <div class="time-picker" @click.stop>
                        <button class="time-picker__button" type="button" @click="toggleTimePicker('detail-end')">
                          {{ selectedEndTime || '请选择' }}
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
                  :class="[activeBooking.status === '已签到' ? 'secondary-action' : 'primary-action', 'compact']"
                  @click="handleCheckIn"
                >
                  <CheckCircle2 />
                  签到
                </button>
                <button
                  :class="[activeBooking.status === '已签到' ? 'primary-action' : 'secondary-action', 'compact']"
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
              <div v-for="row in filteredHistoryRows" :key="`${row.date}-${row.seat}`" class="table-row">
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
                </div>
                <span>{{ item.date }}</span>
                <b>{{ getViolationScoreChange(item) }}分</b>
                <em>{{ item.status }}</em>
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
              <button class="secondary-action compact">管理</button>
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
            <button class="primary-action compact">去处理</button>
          </article>
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
