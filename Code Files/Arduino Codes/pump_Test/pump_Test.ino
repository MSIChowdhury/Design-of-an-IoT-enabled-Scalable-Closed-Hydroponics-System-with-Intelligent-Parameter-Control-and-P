const int phUpPumpPin = 22;
const int phDownPumpPin = 23;

void setup() {

  pinMode(phUpPumpPin, OUTPUT);
  pinMode(phDownPumpPin, OUTPUT);
  
  digitalWrite(phUpPumpPin, HIGH);
  digitalWrite(phDownPumpPin, HIGH);

}

void loop() {
      digitalWrite(phDownPumpPin, LOW);
      delay(500);
      digitalWrite(phDownPumpPin, HIGH);
      delay(500);

}
