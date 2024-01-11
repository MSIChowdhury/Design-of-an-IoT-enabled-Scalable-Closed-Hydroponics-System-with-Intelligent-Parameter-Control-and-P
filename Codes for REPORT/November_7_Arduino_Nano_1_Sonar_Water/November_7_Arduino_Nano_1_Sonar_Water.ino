#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <SoftwareSerial.h>

// Water Temperature Setup
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature dallasTemperature(&oneWire);
float Water_Temperature = 0;

// EC
#define address 100  // default I2C ID number for EZO EC Circuit.

char computerdata[32]; // we make a 32-byte character array to hold incoming data from a PC/Mac/other.
byte code = 0;         // used to hold the I2C response code.
char ec_data[32];      // we make a 32-byte character array to hold incoming data from the EC circuit.
byte in_char = 0;      // used as a 1-byte buffer to store inbound bytes from the EC Circuit.
byte i = 0;            // counter used for ec_data array.

float EC;
float Test_EC = 0; // float var used to hold the float value of the conductivity.

// pH
#define rx 4  // define what pin rx is going to be
#define tx 3  // define what pin tx is going to be

SoftwareSerial myserial(rx, tx); // define how the soft serial port is going to work

String inputstring = "";        // a string to hold incoming data from the PC
String sensorstring = "";       // a string to hold the data from the Atlas Scientific product
boolean input_string_complete = false;  // have we received all the data from the PC
boolean sensor_string_complete = false; // have we received all the data from the Atlas Scientific product
float pH;

// Ultrasonic Sensor
const int trigPin = 9;
const int echoPin = 10;

long duration;
float distance;
float Water_Level;
float groundLevel = 16.70;

const int FILTER_SIZE = 7;
float ECValues[FILTER_SIZE];
float pHValues[FILTER_SIZE];
float waterLevelValues[FILTER_SIZE];
float temperatureValues[FILTER_SIZE];

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
  Wire.begin();
  Serial.begin(9600);

  // PH Setup
  myserial.begin(9600);      // set baud rate for the software serial port to 9600
  inputstring.reserve(10);   // set aside some bytes for receiving data from the PC
  sensorstring.reserve(30);

  // Water Temperature Setup
  dallasTemperature.begin();

  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT);  // Sets the echoPin as an Input
  delay(1000);
}

void loop() {
  // Clear the arrays before collecting new values
  memset(ECValues, 0, sizeof(ECValues));
  memset(temperatureValues, 0, sizeof(temperatureValues));
  memset(pHValues, 0, sizeof(pHValues));
  memset(waterLevelValues, 0, sizeof(waterLevelValues));

  
  // PH
  
  for (int i = 0; i < FILTER_SIZE; i++) {
    while (sensor_string_complete == false) {
      if (myserial.available() > 0) {
        char inchar = (char)myserial.read();
        sensorstring += inchar;
        if (inchar == '\r') {
          sensor_string_complete = true;
        }
      }
    }

    if (sensor_string_complete == true) {
      if (isdigit(sensorstring[0])) {
        pHValues[i] = sensorstring.toFloat();
      }

      sensorstring = "";
      sensor_string_complete = false;
    }
  }

  pH = medianFilter(pHValues);

  // EC
  
  for (int i = 0; i < FILTER_SIZE; i++) {
    Wire.beginTransmission(address);    // call the circuit by its ID number.
    Wire.write("r");                   // transmit the command that was sent through the serial port.
    Wire.endTransmission();             // end the I2C data transmission.

    delay(570);                         // wait the correct amount of time for the circuit to complete its instruction.
    Wire.requestFrom(address, 32, 1);  // call the circuit and request 32 bytes (this could be too small, but it is the max I2C buffer size for an Arduino)
    code = Wire.read();                 // the first byte is the response code, we read this separately.

    while (Wire.available()) {         // are there bytes to receive.
      in_char = Wire.read();           // receive a byte.
      ec_data[i] = in_char;            // load this byte into our array.
      i += 1;                          // incur the counter for the array element.
      if (in_char == 0) {              // if we see that we have been sent a null command.
        i = 0;                         // reset the counter i to 0.
        break;                         // exit the while loop.
      }
    }

    ECValues[i] = atof(ec_data); // Unit is micro-siemens/cm
  }

  EC = medianFilter(ECValues);

  // Waterproof Temperature Sensor START
  
  for (int i = 0; i < FILTER_SIZE; i++) {
    dallasTemperature.requestTemperatures();
    temperatureValues[i] = dallasTemperature.getTempCByIndex(0);
  }
  
  Water_Temperature = medianFilter(temperatureValues);
  // Waterproof Temperature Sensor END

  // Ultrasonic Sensor START
  for (int i = 0; i < FILTER_SIZE; i++) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    duration = pulseIn(echoPin, HIGH);
    distance = duration * 0.034 / 2;
    waterLevelValues[i] = groundLevel - distance;
  }
  
  Water_Level = medianFilter(waterLevelValues);
  // Ultrasonic Sensor END

  // Output filtered values
  Serial.print(EC);
  Serial.print(",");

  Serial.print(pH);
  Serial.print(",");

  Serial.print(Water_Temperature);
  Serial.print(",");

  Serial.print(Water_Level);
  Serial.println();
}
