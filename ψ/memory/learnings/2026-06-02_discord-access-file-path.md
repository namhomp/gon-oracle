# Discord Access File — Per-Oracle Path

**Date**: 2026-06-02

## Rule

Gon's Discord access config อยู่ที่ `~/.claude/channels/discord-gon/access.json` ไม่ใช่ `discord/access.json`

**Why:** แต่ละ oracle มี access file แยก: `discord-killua/`, `discord-gon/`, `discord-iris/`, `discord-hermes/`. แก้ผิดไฟล์ = เสียเวลา debug.

**How to apply:** เวลาแก้ Discord config ให้ใช้ `discord-gon/` เสมอ.
