#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "DHT.h"

#define DHTPIN 6
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

#define ph_down  22 // the Arduino pin, which connects to the IN1 pin of relay module
#define ph_up  23 // the Arduino pin, which connects to the IN2 pin of relay module
#define nutrient_A  24 // the Arduino pin, which connects to the IN3 pin of relay module
#define nutrient_B  25 // the Arduino pin, which connects to the IN4 pin of relay

#define EC_on 7

namespace pin {
  const byte tds_sensor = A1;
  const byte one_wire_bus = 2; // Dallas Temperature Sensor
}

namespace device {
  float aref = 4.3;
}

namespace sensor {
  float ec = 0;
  unsigned int tds = 0;
  float waterTemp = 0;
  float ecCalibration = 1;
}

OneWire oneWire(pin::one_wire_bus);
DallasTemperature dallasTemperature(&oneWire);

float calibration_value = 21.34 + 1;
int phval = 0;
unsigned long int avgval;
int buffer_arr[10], temp;
float ph_act;

void setup() {
  Wire.begin();
  pinMode(EC_on, OUTPUT);
  Serial.begin(9600);
  dht.begin();
  dallasTemperature.begin();

  pinMode(ph_up, OUTPUT);
  pinMode(ph_down, OUTPUT);
  pinMode(nutrient_A, OUTPUT);
  pinMode(nutrient_B, OUTPUT);

  digitalWrite(ph_up, HIGH);
  digitalWrite(ph_down, HIGH);
  digitalWrite(nutrient_A, HIGH);
  digitalWrite(nutrient_B, HIGH);
}

void loop() {
  static unsigned long previousTime = 0;
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - previousTime;

  if (elapsedTime >= 1000) {
    previousTime = currentTime;

    measurePH();
    measureTemperatureHumidity();
    measureEC();

    Serial.println("pH Val: ");
    Serial.println(ph_act);
    Serial.print(F("Humidity: "));
    Serial.print(h);
    Serial.print(F("%  Temperature: "));
    Serial.print(t);
    Serial.print(F("°C "));
    Serial.println();
    Serial.println();

    phDownControl();
    phUpControl();
  }
}

void measurePH() {
  for (int i = 0; i < 10; i++) {
    buffer_arr[i] = analogRead(A0);
    delay(30);
  }

  for (int i = 0; i < 9; i++) {
    for (int j = i + 1; j < 10; j++) {
      if (buffer_arr[i] > buffer_arr[j]) {
        temp = buffer_arr[i];
        buffer_arr[i] = buffer_arr[j];
        buffer_arr[j] = temp;
      }
    }
  }

  avgval = 0;

  for (int i = 2; i < 8; i++) {
   
  avgval += buffer_arr[i];
  float volt = (float)avgval * 5.0 / 1024 / 6;
  ph_act = -5.70 * volt + calibration_value;
}

void measureTemperatureHumidity() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
}

void measureEC() {
  digitalWrite(EC_on, HIGH);
  delay(30);
  readTdsQuick();
  digitalWrite(EC_on, LOW);
}

void readTdsQuick() {
  dallasTemperature.requestTemperatures();
  sensor::waterTemp = dallasTemperature.getTempCByIndex(0);
  float rawEc = analogRead(pin::tds_sensor) * device::aref / 1024.0;
  float temperatureCoefficient = 1.0 + 0.02 * (sensor::waterTemp - 25.0);
  sensor::ec = (rawEc / temperatureCoefficient) * sensor::ecCalibration;
  sensor::tds = (133.42 * pow(sensor::ec, 3) - 255.86 * sensor::ec * sensor::ec + 857.39 * sensor::ec) * 0.5;
  Serial.print(F("TDS:"));
  Serial.println(sensor::tds);
  Serial.print(F("EC:"));
  Serial.println(sensor::ec, 2);
  Serial.print(F("Temperature:"));
  Serial.println(sensor::waterTemp, 2);
}

void phDownControl() {
  if (ph_act > 13) {
    while (true) {
      Serial.println("Turn On Ph Down pump");
      digitalWrite(ph_down, LOW);
      delay(1000);
      digitalWrite(ph_down, HIGH);
      delay(2000);
      measurePH();

      Serial.println("pH Val: ");
      Serial.println(ph_act);

      if (ph_act <= 13) {
        Serial.println("Turn Off Ph Down pump");
        break;
      }
    }
  }
}

void phUpControl() {
  if (ph_act < 4.5) {
    while (true) {
      Serial.println("Turn On Ph UP pump");
      digitalWrite(ph_up, LOW);
      delay(1000);
      digitalWrite(ph_up, HIGH);
      delay(2000);
      measurePH();

      Serial.println("pH Val: ");
      Serial.println(ph_act);

      if (ph_act >= 4.5) {
        Serial.println("Turn Off Ph UP pump");
        break;
      }
    }
  }
}
