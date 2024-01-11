#include <Arduino.h>
#include "MHZ19.h"

// Air Temperature and Humidity Sensor
#include "DHT.h"
#define DHTPIN 5
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

MHZ19 myMHZ19; // Constructor for the library

unsigned long getDataTimer = 0;
int CO2;

// Write on Mega from Python
const int bufferSize = 4;      // Adjust this according to your needs
char inputString[bufferSize];   // A character array to store the incoming string
char *token;                    // A pointer to help with parsing
int pinNumber, pinState;

const int FILTER_SIZE = 7;

float CO2Values[FILTER_SIZE];
float airTemperatureValues[FILTER_SIZE];
float humidityValues[FILTER_SIZE];

float medianFilter(float values[FILTER_SIZE]) {
  // Sort the array in ascending order
  for (int i = 0; i < FILTER_SIZE - 1; i++) {
    for (int j = 0; j < FILTER_SIZE - i - 1; j++) {
      if (values[j] > values[j + 1]) {
        // Swap values
        float temp = values[j];
        values[j] = values[j + 1];
        values[j + 1] = temp;
      }
    }
  }

  // Return the median value
  return values[(FILTER_SIZE-1) / 2];
}

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);

  pinMode(50, OUTPUT);
  pinMode(48, OUTPUT);
  pinMode(46, OUTPUT);
  pinMode(44, OUTPUT);
  pinMode(42, OUTPUT);
  pinMode(40, OUTPUT);
  pinMode(38, OUTPUT);
  pinMode(36, OUTPUT);
  pinMode(34, OUTPUT);

  digitalWrite(50, HIGH);
  digitalWrite(48, HIGH);
  digitalWrite(46, HIGH);
  digitalWrite(44, HIGH);
  digitalWrite(42, HIGH);
  digitalWrite(40, HIGH);
  digitalWrite(38, HIGH);
  digitalWrite(36, HIGH);
  digitalWrite(34, HIGH);

  // Air Temperature and Humidity Sensor
  dht.begin();

  myMHZ19.begin(Serial1); // *Serial(Stream) reference must be passed to library begin().
  myMHZ19.autoCalibration(false); // Turn auto calibration ON (OFF autoCalibration(false))
  delay(1000);

  for (int j = 0; j <= 5; j++) {
    CO2 = myMHZ19.getCO2();
    delay(100);
  }
}

void loop() {

  if (millis() - getDataTimer >= 60000) {
    // Clear the array before collecting new values
    memset(CO2Values, 0, sizeof(CO2Values));
    memset(airTemperatureValues, 0, sizeof(airTemperatureValues));
    memset(humidityValues, 0, sizeof(humidityValues));

    // Collect multiple values for filtering
    for (int i = 0; i < FILTER_SIZE; i++) {
      CO2Values[i] = myMHZ19.getCO2();
      delay(100);
      humidityValues[i] = dht.readHumidity();
      airTemperatureValues[i] = dht.readTemperature();
      delay(100);
    }

    getDataTimer = millis();

    float CO2 = medianFilter(CO2Values);
    float AirTemperature = medianFilter(airTemperatureValues);
    float Humidity = medianFilter(humidityValues);

    Serial.print(CO2);
    Serial.print(",");

    Serial.print(AirTemperature);
    Serial.print(",");

    Serial.print(Humidity);
    Serial.println();
  }

  if (Serial.available() != 0) {
    Serial.readBytesUntil('\n', inputString, bufferSize);

    // Parse the inputString using strtok to split it into tokens
    token = strtok(inputString, ",");

    // Check if the token is not null (indicating that it found a comma)
    if (token != NULL) {
      // Convert the first token (pin number) to an integer
      pinNumber = atoi(token);

      // Move to the next token
      token = strtok(NULL, ",");

      // Check if the second token is not null (indicating that it found another comma)
      if (token != NULL) {
        // Convert the second token (pin state) to an integer
        pinState = atoi(token);

        // Now, you have pinNumber and pinState as separate variables
        // You can use them in your Arduino code as needed
        // For example, you can digitalWrite(pinNumber, pinState) to set the pin state
        digitalWrite(pinNumber, pinState);
      }
    }
  }
}
