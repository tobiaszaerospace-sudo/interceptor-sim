#include <Servo.h>

Servo az;
Servo el;

float current_az = 0.0;
float current_el = 0.0;

void setup() {
  Serial.begin(115200);
  az.attach(9);   // AZ servo on pin 9
  el.attach(10);  // EL servo on pin 10
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // -----------------------------------------
    // If Python requests angles: "GET"
    // -----------------------------------------
    if (line == "GET") {
      Serial.print(current_az);
      Serial.print(" ");
      Serial.println(current_el);
      return;
    }

    // -----------------------------------------
    // Otherwise treat it as "az,el" command
    // -----------------------------------------
    int commaIndex = line.indexOf(',');
    if (commaIndex > 0) {
      float az_deg = line.substring(0, commaIndex).toFloat();
      float el_deg = line.substring(commaIndex + 1).toFloat();

      current_az = az_deg;
      current_el = el_deg;

      az.write(az_deg);
      el.write(el_deg);
    }
  }
}