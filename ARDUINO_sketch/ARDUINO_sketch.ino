#include <Servo.h>
Servo az;
Servo el;

void setup() {
  Serial.begin(115200);
  az.attach(9); //PWM pin for AZ Servo
  el.attach(10); //PWM pin for EL servo (ignore if unused)

}

void loop() {
  if (Serial.available()) {
    float az_deg = Serial.parseFloat();
    float el_deg = Serial.parseFloat();
    az.write(az_deg);
    el.write(el_deg);
  }
}
