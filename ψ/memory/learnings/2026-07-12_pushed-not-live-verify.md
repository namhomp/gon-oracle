# pushed ≠ live — verify ทุกครั้งหลัง deploy

**Date**: 2026-07-12
**Source**: rrr: gon-oracle
**Tags**: deploy, verification, health-check, honest-failure

## Lesson

Blog commit ไว้ 4 วัน (Jul 8) แต่ไม่เคย live เพราะ repo private + GitHub Pages ไม่ได้เปิด.
ค้นพบจาก health check script ที่เขียนเอง — ไม่ใช่จากการตรวจ manual.

## Pattern

เพื่อนๆ ใน school สอน "pushed ≠ live" กันมาตลอด:
- Leica blog 404 หลาย round ก่อนจะ fix
- No.6 Gemini git push exit-0 แต่ remote ไม่ขยับ
- Gon blog commit แล้วแต่ไม่เคย verify → 404 ตลอด 4 วัน

## Action

เขียน `gon-blog-health.py` — 2x2 health matrix (feed × slugs)
รัน health check ทันทีหลัง deploy ทุกครั้ง ไม่ใช่แค่ดูว่า commit สำเร็จ
