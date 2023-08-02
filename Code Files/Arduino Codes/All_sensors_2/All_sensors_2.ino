#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#include "DHT.h"

#define DHTPIN 6  

#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

//
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
//

float calibration_value = 21.34 + 1;
int phval = 0; 
unsigned long int avgval; 
int buffer_arr[10],temp;

float ph_act;

void setup() 
{
  Wire.begin();
  pinMode(7,OUTPUT);
  Serial.begin(9600);
  dht.begin();
  dallasTemperature.begin();

}
void loop() {
 delay(1000);
 

 //This section measures PH of the system start
 for(int i=0;i<10;i++) 
 { 
 buffer_arr[i]=analogRead(A0);
 delay(30);
 }
 
 for(int i=0;i<9;i++)
 {
  for(int j=i+1;j<10;j++)
   {
      if(buffer_arr[i]>buffer_arr[j])
    {
 temp=buffer_arr[i];
 buffer_arr[i]=buffer_arr[j];
 buffer_arr[j]=temp;
    }
    }
 }
 
 avgval=0;
 
 for(int i=2;i<8;i++)
 avgval+=buffer_arr[i];
 float volt=(float)avgval*5.0/1024/6; 
 ph_act = -5.70 * volt + calibration_value;
// This sections measures PH of the section end

//This Section measures air temperature and humidity start
 float h = dht.readHumidity();
 // Read temperature as Celsius (the default)
 float t = dht.readTemperature();
 // Check if any reads failed and exit early (to try again).
// if (isnan(h) || isnan(t)) {
//   Serial.println(F("Failed to read from DHT sensor!"));
//   return;
// }
 //This section measures air temperature and humidity end



//This section measures EC start
 digitalWrite(7, HIGH);
 delay(30);                          
 readTdsQuick();
 digitalWrite(7, LOW);   
//This section measures EC end


 Serial.println("pH Val: ");
 Serial.println(ph_act);
 Serial.print(F("Humidity: "));
 Serial.print(h);
 Serial.print(F("%  Temperature: "));
 Serial.print(t);
 Serial.print(F("°C "));
 Serial.println();
 
}

void readTdsQuick() {
  delay(1000);
  dallasTemperature.requestTemperatures();
  sensor::waterTemp = dallasTemperature.getTempCByIndex(0);
  float rawEc = analogRead(pin::tds_sensor) * device::aref / 1024.0; // read the analog value more stable by the median filtering algorithm, and convert to voltage value
  float temperatureCoefficient = 1.0 + 0.02 * (sensor::waterTemp - 25.0); // temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0));
  sensor::ec = (rawEc / temperatureCoefficient) * sensor::ecCalibration; // temperature and calibration compensation
  sensor::tds = (133.42 * pow(sensor::ec, 3) - 255.86 * sensor::ec * sensor::ec + 857.39 * sensor::ec) * 0.5; //convert voltage value to tds value
  Serial.print(F("TDS:")); 
  Serial.println(sensor::tds);
  Serial.print(F("EC:")); 
  Serial.println(sensor::ec, 2);
  Serial.print(F("Temperature:")); 
  Serial.println(sensor::waterTemp,2);  
}
