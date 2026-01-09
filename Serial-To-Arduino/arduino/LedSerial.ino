const int LED_PIN = 13;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "ON") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED_ON");
    }
    else if (cmd == "OFF") {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED_OFF");
    }
    else {
      Serial.println("CMD_INVALID");
    }
  }
}
