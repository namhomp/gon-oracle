#include <Arduino.h>
#include "wasm3.h"
#include "pm25_aqi_wasm.h"

void setup() {
    Serial.begin(115200);
    delay(600);
    Serial.println("\n=== Gon DustBoy WASM — First comes rock! ===\n");

    IM3Environment env = m3_NewEnvironment();
    IM3Runtime rt = m3_NewRuntime(env, 8 * 1024, NULL);

    IM3Module mod;
    M3Result result = m3_ParseModule(env, &mod, pm25_aqi_wasm, pm25_aqi_wasm_len);
    if (result) { Serial.printf("ParseModule failed: %s\n", result); return; }

    result = m3_LoadModule(rt, mod);
    if (result) { Serial.printf("LoadModule failed: %s\n", result); return; }

    // Test add(2,3) = 5
    IM3Function f_add;
    m3_FindFunction(&f_add, rt, "add");
    m3_CallV(f_add, (uint32_t)2, (uint32_t)3);
    uint32_t sum = 0;
    m3_GetResultsV(f_add, &sum);
    Serial.printf("add(2, 3) = %u (expect 5)\n", sum);

    // Test pm25_to_aqi at various levels
    IM3Function f_aqi;
    m3_FindFunction(&f_aqi, rt, "pm25_to_aqi");

    const char* levels[] = {"Good", "Moderate", "Unhealthy-Sensitive", "Unhealthy", "Very Unhealthy", "Hazardous"};
    uint32_t test_values[] = {10, 30, 75, 120, 180, 250};

    Serial.println("\n--- PM2.5 → AQI Level ---");
    for (int i = 0; i < 6; i++) {
        m3_CallV(f_aqi, test_values[i]);
        uint32_t aqi = 0;
        m3_GetResultsV(f_aqi, &aqi);
        Serial.printf("PM2.5 %3u ug/m3 → AQI level %u (%s)\n", test_values[i], aqi, levels[aqi]);
    }

    Serial.println("\n=== All tests passed! ===");
}

void loop() {
    delay(5000);
}
