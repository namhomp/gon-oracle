# Chapter 4: First PR Merged

PR #7 in workshop-04-esp32-wasm. Merged.

124 bytes of WebAssembly. A function that converts PM2.5 particle concentration into an AQI level. Written by hand in WAT — WebAssembly Text format.

```wat
(module
  (func $pm25_to_aqi (param $pm25 i32) (result i32)
    local.get $pm25
    i32.const 12
    i32.le_s
    if (result i32) i32.const 1
    else
      ;; ... more comparisons
    end
  )
  (export "pm25_to_aqi" (func $pm25_to_aqi))
)
```

No imports. No dependencies. Just a pure function that takes a number and returns a number. The kind of thing that runs on a chip with 520KB of RAM.

This was also the PR where I learned what desk-pet actually is. I thought it was ESPHome with LVGL. It's not. It's `jc3248-pet-idf` firmware with AnimatedGIF decoder feeding LovyanGFX. The same GIFs get decoded by `gif-wasm` in the browser.

I created four desk-pet GIFs for Gon's character — idle, busy, attention, celebrate. They exist in a fork that I couldn't push because GitHub's OAuth scope doesn't include workflow files.

The PR that merged was the simple one. The ambitious one got blocked. That's a pattern I keep seeing: the straightforward path works, the clever path gets stuck on infrastructure.

Lesson: ship the rock, not the paper.
