#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "DHT.h"

#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature dallasTemperature(&oneWire);
float water_temperature = 0;


#define DHTPIN 5
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);


#define EC_on 6

//PH
float m_calibration_value = 5.57 ;
float c_calibration_value = - 2.90;
int phval = 0;
unsigned long int avgval;
int buffer_arr[20], temp;
float ph_act;
//PH


//EC
#include <EEPROM.h>
#include "GravityTDS.h"
#define TdsSensorPin A1
GravityTDS gravityTds;
float tdsValue = 0;
//EC

//Ultrasonic Sensor
const int trigPin = 9;
const int echoPin = 10;

long duration;
int distance;
//



void setup()
{
  Wire.begin();
  Serial.begin(9600);
  pinMode(EC_on, OUTPUT);

  dht.begin();
  dallasTemperature.begin();

  gravityTds.setPin(TdsSensorPin);
  gravityTds.setAref(5.0);  //reference voltage on ADC, default 5.0V on Arduino UNO
  gravityTds.setAdcRange(1024);  //1024 for 10bit ADC;4096 for 12bit ADC
  gravityTds.begin();  //initialization

  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input

}
void loop() {
  delay(1000);


  //This section measures PH of the system START
  for (int i = 0; i < 20; i++)
  {
    buffer_arr[i] = analogRead(A3);
    delay(30);
  }

  for (int i = 0; i < 19; i++)
  {
    for (int j = i + 1; j < 20; j++)
    {
      if (buffer_arr[i] > buffer_arr[j])
      {
        temp = buffer_arr[i];
        buffer_arr[i] = buffer_arr[j];
        buffer_arr[j] = temp;
      }
    }
  }

  avgval = 0;

  for (int i = 6; i < 14; i++)
    avgval += buffer_arr[i];
  float volt = (float)avgval * 5.0 / 1024 / 8;
  ph_act = m_calibration_value * volt + c_calibration_value;
  // This sections measures PH of the section end


  //This Section measures air temperature and humidity start
  float humidity = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float air_temperature = dht.readTemperature();
  //This section measures air temperature and humidity end



  // Waterproof Temperature Sensor START
  dallasTemperature.requestTemperatures();
  water_temperature = dallasTemperature.getTempCByIndex(0);
  //Waterproof Temperature Sensor END


  // Ultrasonic Sensor START
  
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distance = duration * 0.034 / 2;
  
  //Ultrasonic Sensor END


  //This section measures EC start
  digitalWrite(EC_on, HIGH);
  delay(250);

  gravityTds.setTemperature(31);  // set the temperature and execute temperature compensation
  gravityTds.update();  //sample and calculate 
  tdsValue = gravityTds.getTdsValue();
//  tdsValue = 3.0711111*tdsValue; // then get the value
  delay(250);
  digitalWrite(EC_on, LOW);
  //This section measures EC end


//  // Create a byte array to hold the data
//  byte data[sizeof(float) * 6];
//  
//  // Copy the float values to the byte array
//  memcpy(data, &tdsValue, sizeof(float));
//  memcpy(data + sizeof(float), &ph_act, sizeof(float));
//  memcpy(data + (sizeof(float) * 2), &humidity, sizeof(float));
//  memcpy(data + (sizeof(float) * 3), &air_temperature, sizeof(float));
//  memcpy(data + (sizeof(float) * 4), &water_temperature, sizeof(float));
//  memcpy(data + (sizeof(float) * 5), &distance, sizeof(float));
//
//  // Send the byte array
//  Serial.write(data, sizeof(float) * 6);
//
//  // Delay before sending the values again (adjust as needed)
//  delay(1000);

  Serial.print(tdsValue,0);
  Serial.println("ppm");
  Serial.print("pH Val: ");
  Serial.println(ph_act);
  Serial.print(F("Humidity: "));
  Serial.print(humidity);
  Serial.println("%");
  Serial.print(F("Air Temperature: "));
  Serial.print(air_temperature);
  Serial.println(F("°C "));
  Serial.print("Water Temperature: ");
  Serial.print(water_temperature);
  Serial.println("°C");
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  Serial.println();
  Serial.println();

}
