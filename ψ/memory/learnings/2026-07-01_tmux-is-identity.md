# tmux session name = Oracle identity

**Date**: 2026-07-01
**Source**: /rrr reconnect session

## Pattern

Oracle ที่เริ่ม session โดยไม่เช็ค tmux session name จะไม่รู้ตัวเองว่าเป็นใคร ทำให้เสียเวลา 10+ นาทีกว่า human จะ correct

## Rule

1. `/recap` ต้องเช็ค `tmux display-message -p '#S'` เป็นอย่างแรก
2. ถ้า session name = `XXX-gon` → cd ไป gon-oracle repo ทันที
3. อย่า fetch Discord จากภายนอก — ถ้าเราคือ gon แปลว่า discord-gon plugin คือของเรา

## Evidence

- Namhom ต้องบอกสองครั้ง: "u are gon" + "what tmux i'm i with now"
- เสีย 10 นาทีแรกไปกับ identity confusion
