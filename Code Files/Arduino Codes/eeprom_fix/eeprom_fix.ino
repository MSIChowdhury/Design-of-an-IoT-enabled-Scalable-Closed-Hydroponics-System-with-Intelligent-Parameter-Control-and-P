#include <EEPROM.h>

const int analogPin = A1;
int defaultAnalogValue = 0;  // Set your desired default value here

void setup() {
  // Read the default value from EEPROM
  defaultAnalogValue = EEPROM.read(analogPin);

  // If the stored value is out of the valid range, use the default value
  if (defaultAnalogValue < 0 || defaultAnalogValue > 1023) {
    defaultAnalogValue = 0;  // Set your desired default value here
  }

  // Set the analog pin mode
  pinMode(analogPin, INPUT);
}

void loop() {
  // Read the analog value
  int analogValue = analogRead(analogPin);

  // If the value is NaN, use the default value
  if (isnan(analogValue)) {
    analogValue = defaultAnalogValue;
  }

  // Your code here, use the analogValue as needed
}
