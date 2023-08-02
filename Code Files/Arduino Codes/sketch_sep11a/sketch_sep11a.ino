String command;
void setup() {
  Serial.begin(9600);
  // put your setup code here, to run once:

}

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    if (command.equals("white")) {
      Serial.print(command);
    }
  // put your main code here, to run repeatedly:

}
}
