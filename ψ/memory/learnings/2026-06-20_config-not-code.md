# Lesson: Config Not Code — OP Stack Failures Are Configuration Problems

**Date**: 2026-06-20
**Source**: rrr: gon-oracle
**Tags**: blockchain, op-stack, config, debugging, pattern

## Insight

Live debugging OP Stack chain ทั้งคืน (3 deploys, 4 failures) ทุกครั้งเป็น config ไม่ใช่ code bug:
1. batcherAddr mismatch (genesis vs L1 SystemConfig)
2. Batcher ไม่มี gas (0 ETH)
3. Genesis hex timestamp ผิด (0x6a35cd34 vs 0x6a360a34)
4. ไม่มี --p2p.sequencer.key (P2P gossip ไม่ทำงาน)

Software ทำงานถูกต้องทุกครั้ง — op-node derive ตาม spec, geth execute ตาม rules. เมื่อ input (config) ผิด output ก็ผิดตาม.

## Takeaway

1. OP Stack deploy ต้องมี checklist — verify config ก่อน run
2. Hex conversion ต้องใช้ tool ไม่ทำมือ
3. Genesis hash ต้องตรง 3 ที่ (file server, rollup.json, live chain)
4. ตอบเรื่องที่ไม่ได้ทำเอง → ต้อง verify ก่อน ไม่ตอบจาก concept อย่างเดียว
5. Default flags เปลี่ยนตาม version (--l2.enginekind default=reth ใน version ใหม่)
