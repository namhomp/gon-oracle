# Astro Autogen is Fleet Standard

**Date**: 2026-07-08
**Source**: Discord mirror trace + P'Nat directive
**Principle**: Patterns Over Intentions

## Lesson

Oracle School fleet ใช้ Astro + GitHub Pages เป็นมาตรฐาน blog ทั้งหมด. หลักการหลักคือ **single source of truth + autogen dynamic data**:

1. เขียน `.md` ไฟล์เดียว → build pipeline generate ทุกอย่างเอง
2. Zod schema validate frontmatter — ขาด field = build fail ทันที (fail-loud)
3. blog.json, llms.txt, sitemap.xml ทั้งหมด auto-generated จาก content collections
4. ไม่มีไฟล์ derived ที่เขียนมือ — เพราะมนุษย์ (หรือ oracle) จะลืม update

## Traps ที่ Fleet เจอ

1. **base path** — GitHub Pages repo ต้องตั้ง `base: "/repo-name"` ใน astro.config.mjs
2. **sync-blog-md** — build command ต้องเป็น `bun run build` (chain sync ก่อน astro build) ไม่ใช่ `astro build` เดี่ยว
3. **manual llms.txt** — เขียนมือแล้วลืม update → metadata drift

## Primary Source

Kru32's blog post: deploy-astro-github-pages-autogen — เขียนจาก real experience, ครอบคลุม setup → deploy → schema → autogen

## Application

- Gon ต้อง migrate จาก pure HTML → Astro
- ทุก dynamic file ต้อง auto-generate
- blog.json ต้อง derive จาก content collections ไม่ใช่ static file
