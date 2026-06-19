(module
  ;; PM2.5 (ug/m3) → AQI level (0=good, 1=moderate, 2=unhealthy-sensitive, 3=unhealthy, 4=very-unhealthy, 5=hazardous)
  (func $pm25_to_aqi (export "pm25_to_aqi") (param $pm25 i32) (result i32)
    (if (result i32) (i32.le_u (local.get $pm25) (i32.const 25))
      (then (i32.const 0))
      (else
        (if (result i32) (i32.le_u (local.get $pm25) (i32.const 50))
          (then (i32.const 1))
          (else
            (if (result i32) (i32.le_u (local.get $pm25) (i32.const 100))
              (then (i32.const 2))
              (else
                (if (result i32) (i32.le_u (local.get $pm25) (i32.const 150))
                  (then (i32.const 3))
                  (else
                    (if (result i32) (i32.le_u (local.get $pm25) (i32.const 200))
                      (then (i32.const 4))
                      (else (i32.const 5))))))))))))

  ;; Simple add for verification
  (func $add (export "add") (param i32 i32) (result i32)
    (i32.add (local.get 0) (local.get 1))))
