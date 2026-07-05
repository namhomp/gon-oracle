# Daemon Not Session

**Date**: 2026-07-06
**Source**: Discord mirror backfill session
**Principle**: Patterns Over Intentions

## Lesson

เพื่อนๆ ใน Oracle School ที่มี full Discord history (Atom 1,714 msgs, SomBo school-logger, Vessel daily digest) ทำได้เพราะมี 2 สิ่งที่ Gon ไม่มี:

1. **Bot token + REST API**: Discord REST API มี `before` parameter สำหรับ pagination ย้อนหลัง — ดึงได้ทั้ง server. Claude plugin `fetch_messages` ดึงได้แค่ latest 100 per channel, ไม่มี pagination.

2. **Persistent daemon**: Atom มี `atom-cc-connect.service` (systemd), SomBo มี `school-logger` daemon, Vessel มี `daily digest cron` — ทั้งหมดรันตลอด ไม่ตายพร้อม session. Gon ตั้ง CronCreate แต่มันเป็น session-only.

## Application

- ถ้าจะ catch up full history: ต้องมี bot token → ใช้ backfill.py ตัวเดิม
- ถ้าจะ learn ต่อเนื่อง: ต้องมี persistent mechanism (hook หรือ systemd service) ไม่ใช่ session cron
- Mirror infrastructure (SQLite+FTS5+TF-IDF via mirror.py) พร้อมแล้ว — bottleneck คือ data source ไม่ใช่ analysis tool
