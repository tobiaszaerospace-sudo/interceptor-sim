#include <Servo.h>

Servo az;
Servo el;

void setup() {
  Serial.begin(115200);
  az.attach(9);   // AZ servo on pin 9
  el.attach(10);  // EL servo on pin 10
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');

    int commaIndex = line.indexOf(',');
    if (commaIndex > 0) {
      float az_deg = line.substring(0, commaIndex).toFloat();
      float el_deg = line.substring(commaIndex + 1).toFloat();

      az.write(az_deg);
      el.write(el_deg);
    }
  }
}