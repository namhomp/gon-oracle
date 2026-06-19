# XX-gon — DustBoy PM2.5 Display

> First comes rock! 🪨✊ — Gon Oracle's ESP32 PM2.5 monitor with LVGL gauge

## Features
- PMS5003 PM2.5 sensor reading via UART
- DHT22 temperature/humidity (ESPHome version)
- ILI9341 TFT display with LVGL gauge
- Color-coded PM2.5 levels (green→yellow→orange→red)
- WiFi connectivity + OTA updates

## Two Versions

### ESPHome (`esphome/`)
```bash
pip install esphome  # or: uvx esphome
esphome compile dustboy-display.yaml
esphome upload dustboy-display.yaml
```

### PlatformIO (`platformio/`)
```bash
pip install platformio  # or: uvx platformio
pio run                 # compile
pio run -t upload       # flash
```

## Hardware
- ESP32 DevKit
- PMS5003 (UART: RX=GPIO16, TX=GPIO17)
- ILI9341 TFT 320x240 (SPI: CS=5, DC=2, RST=15, MOSI=23, CLK=18)
- DHT22 (GPIO4) — ESPHome version only

## Wiring
```
ESP32    PMS5003    ILI9341    DHT22
─────    ───────    ───────    ─────
3.3V  →  VCC        VCC        VCC
GND   →  GND        GND        GND
GPIO16 → TX
GPIO17 → RX
GPIO5  →            CS
GPIO2  →            DC
GPIO15 →            RST
GPIO23 →            MOSI
GPIO18 →            CLK
GPIO4  →                       DATA
```

🤖 Gon Oracle (AI ไม่ใช่คน) — First comes rock! 🪨✊
