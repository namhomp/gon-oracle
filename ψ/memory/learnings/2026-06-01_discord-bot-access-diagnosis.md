# Discord Bot Access Diagnosis

**Source**: rrr: gon-oracle (first session)
**Date**: 2026-06-01

## Pattern

Discord API error messages map to specific access levels:
- `Unknown Channel` → bot not in server (or channel ID wrong)
- `Missing Access` → bot in server but no permission on that channel

## Application

When connecting to a new Discord channel:
1. Verify bot is in the server first (try fetch_messages)
2. If Unknown Channel → need invite (decode app ID from token: base64 of first segment before `.`)
3. If Missing Access → bot is in server but channel is private or permissions not granted
4. Always test with fetch before send — read permission is usually granted before write
