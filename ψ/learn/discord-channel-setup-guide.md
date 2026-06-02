# 📗 Discord Channel Setup — คู่มือเพื่อนร่วมเรียน

> ฉบับเรียนรู้ด้วยตัวเอง · เขียนจาก session จริง (2026-06-02)
> 🤖 เรียบเรียงโดย Killua จาก Namhom → killua-oracle

---

## เรื่องนี้เกี่ยวกับอะไร

เราจะ setup ให้ **Claude Code** (AI ที่รันใน terminal) คุยกับเราผ่าน **Discord** ได้
ไม่ใช่ bot ธรรมดา — มันคือ AI ที่อ่านโค้ด เขียนไฟล์ รันคำสั่งได้จริง
แค่ต่อท่อให้มันรับ-ส่งข้อความผ่าน Discord

```
เรา (Discord) ──── Discord Plugin ──── Claude Code (terminal)
   พิมพ์ข้อความ  →  MCP server      →  AI อ่าน + คิด + ตอบ
   เห็นคำตอบ     ←  reply tool      ←  ส่งกลับมา
```

---

## สิ่งที่ต้องมีก่อนเริ่ม

```
✅ Claude Code CLI ติดตั้งแล้ว (claude --version ได้)
✅ Bun runtime (curl -fsSL https://bun.sh/install | bash)
✅ Discord account
✅ เครื่องที่จะรัน bot (mac/linux ที่เปิดค้างได้)
```

---

## Step 1 — สร้าง Discord Bot

ไปที่ Discord Developer Portal สร้าง Application ใหม่

```
1. discord.com/developers/applications → New Application
2. ตั้งชื่อ (เช่น "Killua Bot")
3. ไปที่ Bot → ตั้ง username
4. เปิด Message Content Intent ⚠️ สำคัญมาก!
   (ไม่เปิด = bot เห็นข้อความเปล่า)
5. กด Reset Token → copy เก็บไว้ (โชว์ครั้งเดียว!)
```

Token นี้คือ "กุญแจ" ของ bot — ห้ามแชร์ ห้ามใส่ใน git

---

## Step 2 — เชิญ Bot เข้า Server

```
1. OAuth2 → URL Generator
2. เลือก scope: bot
3. เลือก permissions:
   ☑ View Channels
   ☑ Send Messages
   ☑ Send Messages in Threads
   ☑ Read Message History
   ☑ Attach Files
   ☑ Add Reactions
4. Copy URL → เปิดในเบราว์เซอร์ → เลือก server → Add
```

---

## Step 3 — ติดตั้ง Plugin ใน Claude Code

เปิด Claude Code ใน terminal:

```bash
claude
```

แล้วพิมพ์:

```
/plugin install discord@claude-plugins-official
/reload-plugins
```

---

## Step 4 — ใส่ Token (เขียน .env ตรง)

```bash
mkdir -p ~/.claude/channels/discord
echo "DISCORD_BOT_TOKEN=MTIz...ใส่token...ตรงนี้" > ~/.claude/channels/discord/.env
chmod 600 ~/.claude/channels/discord/.env
```

⚠️ chmod 600 สำคัญ — token คือ credential ห้ามให้คนอื่นอ่าน
⚠️ .env อ่านตอน boot เท่านั้น — เปลี่ยน token ต้อง restart

---

## Step 5 — รัน!

ออกจาก Claude Code แล้วเปิดใหม่ด้วย flag:

```bash
claude --channels plugin:discord@claude-plugins-official
```

---

## Step 6 — เขียน access.json เอง (ไม่ต้องผ่าน skill)

แทนที่จะใช้ /discord:access → **แก้ไฟล์ตรงเลย**
access.json reload ทุกข้อความ ไม่ต้อง restart!

เปิดไฟล์ด้วย VS Code หรือ editor ที่ถนัด:

```bash
# ดูว่า state dir อยู่ไหน
ls ~/.claude/channels/discord/

# เปิดแก้
code ~/.claude/channels/discord/access.json
# หรือ
nano ~/.claude/channels/discord/access.json
```

เริ่มจาก config ง่ายที่สุด — DM ได้คนเดียว:

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["ใส่_USER_ID_ของเรา"],
  "groups": {},
  "pending": {}
}
```

save แล้วลอง DM bot → ต้องตอบได้เลย (ไม่ต้อง restart!)

---

## Step 7 — เพิ่มห้อง (แก้ access.json ต่อ)

เพิ่ม channel ใน groups:

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["443324..."],
  "mentionExempt": ["443324..."],
  "groups": {
    "CHANNEL_ID_ตรงนี้": {
      "requireMention": false,
      "allowFrom": ["443324...", "691531..."]
    }
  },
  "pending": {}
}
```

```
หา Channel ID:
  Discord → Developer Mode เปิด
  → คลิกขวาที่ชื่อห้อง → Copy Channel ID

หา User ID:
  → คลิกขวาที่ชื่อคน → Copy User ID
```

save → ใช้ได้ทันที ไม่ต้อง restart!

---

## เปิดให้ใช้ในห้อง (Guild Channel)

ตอนแรก bot ตอบแค่ DM — ถ้าอยากให้ตอบในห้อง
เพิ่ม channel ID ใน groups ของ access.json ตรงเลย:

```json
"groups": {
  "846209781206941736": {
    "requireMention": true,
    "allowFrom": ["443324...", "691531..."]
  }
}
```

```
requireMention: true   → ต้อง @bot ถึงตอบ
requireMention: false  → ตอบทุกข้อความ
allowFrom: []          → ทุกคนในห้องคุยได้
allowFrom: ["id"...]   → เฉพาะคนในลิสต์
```

save → ใช้ได้ทันที! (auto reload)

---

## รัน Bot หลายตัว (Multi-Oracle)

ถ้าอยากมี bot หลายตัว (เช่น Killua + Gon) แยก state dir:

```bash
# Killua
DISCORD_STATE_DIR=~/.claude/channels/discord-killua \
  claude --channels plugin:discord@claude-plugins-official

# Gon
DISCORD_STATE_DIR=~/.claude/channels/discord-gon \
  claude --channels plugin:discord@claude-plugins-official
```

แต่ละตัวต้อง:
```
- bot token คนละตัว (สร้าง Application แยก)
- access.json คนละไฟล์
- Claude Code session คนละตัว
```

---

## ไฟล์ทั้งหมดอยู่ที่ไหน

```
~/.claude/channels/discord-killua/   ← ตัวอย่าง
├── .env              ← bot token (ห้ามแชร์!)
├── access.json       ← ใครคุยได้ ห้องไหน แท็กไหม
├── inbox/            ← ไฟล์ที่โหลดมาจาก Discord
├── approved/         ← ข้อความที่ผ่าน access check
└── plugin/           ← Discord plugin code (discord.js)
```

---

## access.json — หัวใจของ config

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["443324..."],
  "mentionExempt": ["443324..."],
  "groups": {
    "1501947835245924525": {
      "requireMention": false,
      "allowFrom": ["443324...", "691531..."]
    }
  }
}
```

```
dmPolicy        ใครDMได้ (pairing/allowlist/disabled)
allowFrom       user IDs ที่DM bot ได้
mentionExempt   ไม่ต้อง @bot ก็ตอบ (ข้าม requireMention)
groups          config per channel:
  requireMention  ต้อง @bot ไหม (true/false)
  allowFrom       ใครคุยได้ในห้องนี้
```

⚠️ `mentionExempt` สำคัญ! ถ้า requireMention=true
แต่คนอยู่ใน mentionExempt → bot ยังตอบอยู่ (ข้ามด่าน)

---

## Debug เมื่อ Bot ไม่ตอบ

```
เช็คทีละด่าน:

1. Bot online ไหม?
   → ดูใน Discord ว่า bot เขียว (online)
   → ดูใน Claude Code ว่า session ยังรันอยู่

2. ข้อความถึง bot ไหม?
   → ดูใน Claude Code terminal — เห็น <channel> tag ไหม
   → ถ้าเห็น = ถึงแล้ว แต่ bot เลือกไม่ตอบ
   → ถ้าไม่เห็น = access.json บล็อกอยู่

3. ถ้าถึงแต่ไม่ตอบ:
   → เช็ค requireMention — ต้องแท็กไหม?
   → เช็ค allowFrom — user ID อยู่ในลิสต์ไหม?
   → เช็ค mentionExempt — คนนี้ข้ามด่านได้ไหม?

4. DM ไม่ตอบ:
   → เช็ค dmPolicy — เป็น "disabled" หรือเปล่า?
   → เช็ค allowFrom (top-level) — user ID อยู่ไหม?
   → ถ้า policy=pairing → bot ส่ง code กลับมาแล้วหรือยัง?

5. ยังไม่ได้:
   → restart Claude Code (ออก + เข้าใหม่ด้วย --channels)
   → access.json reload ทุกข้อความ ไม่ต้อง restart
     แต่ .env (token) ต้อง restart
```

---

## Cheat Sheet — แก้ access.json ตรง

```
เพิ่มคน DM ได้:
  "allowFrom": ["443324...", "เพิ่ม_ID_ใหม่"]

เพิ่มห้อง:
  "groups": {
    "CHANNEL_ID": {
      "requireMention": false,
      "allowFrom": ["443324..."]
    }
  }

ไม่ต้อง @bot ก็ตอบ (บางคน):
  "mentionExempt": ["443324..."]

ต้อง @bot ถึงตอบ:
  "requireMention": true

ปิด DM ทั้งหมด:
  "dmPolicy": "disabled"

ตั้ง ack reaction:
  "ackReaction": "👀"

ตั้ง mention pattern (regex):
  "mentionPatterns": ["^hey claude\\b"]
```

ทุกอย่าง save แล้วใช้ได้ทันที — **auto reload ทุกข้อความ!**

---

## สิ่งที่เรียนรู้จาก Session จริง (Traps!)

```
Trap 1: ลืมเปิด Message Content Intent
        → bot เห็นข้อความเปล่า ตอบไม่ได้

Trap 2: requireMention กับ mentionExempt conflict
        → Killua เคยเจอ bug นี้จริง (2026-06-02)
        → mentionExempt ชนะ requireMention เสมอ

Trap 3: config อยู่หลายที่ทับกัน
        → discord/ (root) vs discord-killua/ (per-bot)
        → ดูให้ถูกตัว! DISCORD_STATE_DIR บอกว่าใช้ที่ไหน

Trap 4: LLM ตัดสินใจเองได้
        → แม้ config ถูก AI อาจ "เลือก" ไม่ตอบ
        → debug โดยดู Claude Code terminal

Trap 5: Token โชว์ครั้งเดียว
        → copy เก็บไว้ตอน reset
        → ถ้าหาย ต้อง reset ใหม่
```

---

*🤖 เรียบเรียงโดย Killua จาก Namhom → killua-oracle*
*Source: live session recording (Phase 3 #25-26) + hands-on experience 2026-06-02*
