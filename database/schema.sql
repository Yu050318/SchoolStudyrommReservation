create database if not exists SchoolStudyroomReservation
  default character set utf8mb4
  default collate utf8mb4_0900_ai_ci;

use SchoolStudyroomReservation;

drop table if exists violations;
drop table if exists bookings;
drop table if exists seats;
drop table if exists rooms;
drop table if exists users;

create table users (
  id int primary key auto_increment,
  account varchar(32) not null unique,
  password varchar(100) not null,
  name varchar(40) not null,
  role enum('student', 'admin') not null default 'student',
  college varchar(80) not null,
  class_name varchar(80) not null,
  phone varchar(30) not null default '',
  credit_score int not null default 100,
  created_at timestamp not null default current_timestamp
);

create table rooms (
  id varchar(40) primary key,
  name varchar(80) not null,
  location varchar(120) not null,
  open_hours varchar(40) not null,
  facilities json not null,
  sort_order int not null default 0
);

create table seats (
  id int primary key auto_increment,
  room_id varchar(40) not null,
  seat_no varchar(12) not null,
  status enum('free', 'used', 'booked', 'maintenance') not null default 'free',
  position_note varchar(80) not null,
  config varchar(120) not null,
  unique key uniq_room_seat (room_id, seat_no),
  constraint fk_seats_room foreign key (room_id) references rooms(id)
);

create table bookings (
  id int primary key auto_increment,
  user_id int not null,
  room_id varchar(40) not null,
  seat_id int not null,
  start_time datetime not null,
  end_time datetime not null,
  status enum('pending', 'checked_in', 'completed', 'canceled') not null default 'pending',
  created_at timestamp not null default current_timestamp,
  constraint fk_bookings_user foreign key (user_id) references users(id),
  constraint fk_bookings_room foreign key (room_id) references rooms(id),
  constraint fk_bookings_seat foreign key (seat_id) references seats(id)
);

create table violations (
  id int primary key auto_increment,
  user_id int not null,
  type varchar(40) not null,
  reason varchar(200) not null,
  score_change int not null default 0,
  status varchar(20) not null default '已处理',
  happened_at datetime not null,
  constraint fk_violations_user foreign key (user_id) references users(id)
);

insert into users (account, password, name, role, college, class_name, phone) values
('20230218', '123456', '林同学', 'student', '软件工程学院', '软件工程 2301', '13800000000'),
('20230219', '123456', '王同学', 'student', '计算机科学与技术学院', '计科 2302', '13800000001'),
('20230220', '123456', '陈同学', 'student', '信息管理学院', '信管 2301', '13800000002'),
('admin001', 'admin123', '管理员', 'admin', '教务管理中心', '自习室管理组', '010-88880000'),
('admin002', 'admin123', '值班管理员', 'admin', '图书馆管理中心', '自习室值班组', '010-88880001');

insert into rooms (id, name, location, open_hours, facilities, sort_order) values
('taishan-branch', '泰山区图书馆分馆', '泰山区图书馆分馆二楼', '07:30-22:30', json_array('插座', '台灯', '靠窗区', '饮水点'), 1),
('main-library-1f', '总图书馆一楼', '总图书馆一楼东侧', '07:00-23:00', json_array('插座', '大桌区', '自助借还'), 2),
('main-library-2f', '总图书馆二楼', '总图书馆二楼南侧', '07:00-23:00', json_array('插座', '阅读灯', '安静区'), 3),
('main-library-3f', '总图书馆三楼', '总图书馆三楼北侧', '07:00-23:00', json_array('插座', '考研专区', '储物柜'), 4),
('main-library-4f', '总图书馆四楼', '总图书馆四楼西侧', '07:30-22:00', json_array('阅览区', '空调', '静音区'), 5);

insert into seats (room_id, seat_no, status, position_note, config) values
('taishan-branch', 'A01', 'free', '靠窗第 1 排', '插座 / 台灯'),
('taishan-branch', 'A02', 'used', '靠窗第 1 排', '插座 / 台灯'),
('taishan-branch', 'A03', 'booked', '靠窗第 1 排', '插座 / 台灯'),
('taishan-branch', 'A04', 'free', '靠窗第 1 排', '插座 / 台灯'),
('taishan-branch', 'A05', 'maintenance', '中区第 1 排', '台灯维修中'),
('taishan-branch', 'A06', 'free', '中区第 1 排', '插座 / 台灯'),
('taishan-branch', 'A07', 'used', '中区第 1 排', '插座 / 台灯'),
('taishan-branch', 'A08', 'free', '中区第 1 排', '插座 / 台灯'),
('taishan-branch', 'B01', 'free', '靠窗第 2 排', '插座 / 台灯'),
('taishan-branch', 'B02', 'used', '靠窗第 2 排', '插座 / 台灯'),
('taishan-branch', 'B03', 'free', '靠窗第 2 排', '插座 / 台灯'),
('taishan-branch', 'B04', 'free', '靠窗第 2 排', '插座 / 台灯'),
('taishan-branch', 'B05', 'booked', '中区第 2 排', '插座 / 台灯'),
('taishan-branch', 'B06', 'used', '中区第 2 排', '插座 / 台灯'),
('taishan-branch', 'B07', 'free', '中区第 2 排', '插座 / 台灯'),
('taishan-branch', 'B08', 'free', '中区第 2 排', '插座 / 台灯'),
('taishan-branch', 'C01', 'maintenance', '靠窗第 3 排', '座椅维修中'),
('taishan-branch', 'C02', 'free', '靠窗第 3 排', '插座 / 台灯'),
('taishan-branch', 'C03', 'used', '靠窗第 3 排', '插座 / 台灯'),
('taishan-branch', 'C04', 'free', '靠窗第 3 排', '插座 / 台灯'),
('taishan-branch', 'C05', 'free', '中区第 3 排', '插座 / 台灯'),
('taishan-branch', 'C06', 'used', '中区第 3 排', '插座 / 台灯'),
('taishan-branch', 'C07', 'booked', '中区第 3 排', '插座 / 台灯'),
('taishan-branch', 'C08', 'free', '中区第 3 排', '插座 / 台灯'),
('taishan-branch', 'D01', 'maintenance', '靠窗第 4 排', '插座维修中'),
('taishan-branch', 'D02', 'free', '靠窗第 4 排', '插座 / 台灯'),
('taishan-branch', 'D03', 'free', '靠窗第 4 排', '插座 / 台灯'),
('taishan-branch', 'D04', 'used', '靠窗第 4 排', '插座 / 台灯'),
('taishan-branch', 'D05', 'free', '中区第 4 排', '插座 / 台灯'),
('taishan-branch', 'D06', 'free', '中区第 4 排', '插座 / 台灯'),
('taishan-branch', 'D07', 'booked', '中区第 4 排', '插座 / 台灯'),
('taishan-branch', 'D08', 'free', '中区第 4 排', '插座 / 台灯'),
('taishan-branch', 'E01', 'free', '靠窗第 5 排', '插座 / 台灯'),
('taishan-branch', 'E02', 'used', '靠窗第 5 排', '插座 / 台灯'),
('taishan-branch', 'E03', 'free', '靠窗第 5 排', '插座 / 台灯'),
('taishan-branch', 'E04', 'free', '靠窗第 5 排', '插座 / 台灯'),
('taishan-branch', 'E05', 'free', '中区第 5 排', '插座 / 台灯'),
('taishan-branch', 'E06', 'used', '中区第 5 排', '插座 / 台灯'),
('taishan-branch', 'E07', 'maintenance', '中区第 5 排', '台灯维修中'),
('taishan-branch', 'E08', 'free', '中区第 5 排', '插座 / 台灯'),
('taishan-branch', 'F01', 'free', '靠窗第 6 排', '插座 / 台灯'),
('taishan-branch', 'F02', 'used', '靠窗第 6 排', '插座 / 台灯'),
('taishan-branch', 'F03', 'free', '靠窗第 6 排', '插座 / 台灯'),
('taishan-branch', 'F04', 'free', '靠窗第 6 排', '插座 / 台灯'),
('taishan-branch', 'F05', 'free', '中区第 6 排', '插座 / 台灯'),
('taishan-branch', 'F06', 'booked', '中区第 6 排', '插座 / 台灯'),
('taishan-branch', 'F07', 'used', '中区第 6 排', '插座 / 台灯'),
('taishan-branch', 'F08', 'free', '中区第 6 排', '插座 / 台灯');

insert into seats (room_id, seat_no, status, position_note, config)
select 'main-library-1f', seat_no,
  case
    when status = 'maintenance' then 'free'
    when seat_no in ('A01', 'A02', 'B01', 'B02') then 'maintenance'
    else status
  end,
  replace(position_note, '中区', '大桌区'),
  '插座 / 大桌'
from seats
where room_id = 'taishan-branch';

insert into seats (room_id, seat_no, status, position_note, config)
select 'main-library-2f', seat_no,
  case
    when seat_no in ('E07', 'F07', 'F08') then 'maintenance'
    when status = 'booked' then 'free'
    else status
  end,
  replace(position_note, '靠窗', '阅览区'),
  '插座 / 阅读灯'
from seats
where room_id = 'taishan-branch';

insert into seats (room_id, seat_no, status, position_note, config)
select 'main-library-3f', seat_no,
  case
    when seat_no in ('A05', 'B05', 'C05', 'D05') then 'maintenance'
    when status = 'free' and seat_no in ('A06', 'B07', 'C08', 'D08', 'E08') then 'used'
    else status
  end,
  replace(position_note, '中区', '考研区'),
  '插座 / 储物柜'
from seats
where room_id = 'taishan-branch';

insert into seats (room_id, seat_no, status, position_note, config)
select 'main-library-4f', seat_no,
  case
    when status = 'booked' then 'used'
    when seat_no in ('A08', 'B08', 'C08', 'D08') then 'maintenance'
    else status
  end,
  replace(position_note, '靠窗', '静音区'),
  '阅读灯 / 空调'
from seats
where room_id = 'taishan-branch';

insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
select 1, 'taishan-branch', id, '2026-06-05 19:00:00', '2026-06-05 21:00:00', 'pending'
from seats where room_id = 'taishan-branch' and seat_no = 'A03';

insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
select 2, 'main-library-2f', id, '2026-06-04 14:00:00', '2026-06-04 17:00:00', 'completed'
from seats where room_id = 'main-library-2f' and seat_no = 'C04';

insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
select 3, 'main-library-1f', id, '2026-06-03 09:00:00', '2026-06-03 11:00:00', 'canceled'
from seats where room_id = 'main-library-1f' and seat_no = 'B08';

insert into bookings (user_id, room_id, seat_id, start_time, end_time, status)
select 1, 'main-library-3f', id, '2026-06-02 18:30:00', '2026-06-02 21:30:00', 'checked_in'
from seats where room_id = 'main-library-3f' and seat_no = 'F06';

insert into violations (user_id, type, reason, score_change, status, happened_at) values
(1, '迟到签到', '预约开始后 22 分钟签到', -5, '已处理', '2026-05-18 19:22:00'),
(1, '取消超时', '开始前 10 分钟取消预约', -5, '已处理', '2026-04-26 13:50:00'),
(2, '爽约', '预约后未按时签到', -12, '已处理', '2026-03-12 09:30:00'),
(3, '占座超时', '签退后物品未及时带离', -6, '待处理', '2026-06-03 21:20:00');
