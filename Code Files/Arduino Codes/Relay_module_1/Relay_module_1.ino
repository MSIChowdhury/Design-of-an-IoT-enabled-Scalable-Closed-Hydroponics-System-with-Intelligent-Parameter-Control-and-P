#define PIN_RELAY_1  22 // the Arduino pin, which connects to the IN1 pin of relay module
#define PIN_RELAY_2  23 // the Arduino pin, which connects to the IN2 pin of relay module
#define PIN_RELAY_3  24 // the Arduino pin, which connects to the IN3 pin of relay module
#define PIN_RELAY_4  25 // the Arduino pin, which connects to the IN4 pin of relay module

void setup() {
  Serial.begin(9600);

  pinMode(PIN_RELAY_1, OUTPUT);
  pinMode(PIN_RELAY_2, OUTPUT);
  pinMode(PIN_RELAY_3, OUTPUT);
  pinMode(PIN_RELAY_4, OUTPUT);
 
  digitalWrite(PIN_RELAY_1, HIGH);
  digitalWrite(PIN_RELAY_2, HIGH);
  digitalWrite(PIN_RELAY_3, HIGH);
  digitalWrite(PIN_RELAY_4, HIGH);
}

void loop() {
  Serial.println("Loop"); 
  digitalWrite(PIN_RELAY_1, LOW);
  delay(1000);
  digitalWrite(PIN_RELAY_1, HIGH);
  delay(500);
  digitalWrite(PIN_RELAY_2, LOW);
  delay(1000);
  digitalWrite(PIN_RELAY_2, HIGH);
  delay(500);
  digitalWrite(PIN_RELAY_3, LOW);
  delay(1000);
  digitalWrite(PIN_RELAY_3, HIGH);
  delay(500);
  digitalWrite(PIN_RELAY_4, LOW);
  delay(1000);
  digitalWrite(PIN_RELAY_4, HIGH);
  delay(500);
}
