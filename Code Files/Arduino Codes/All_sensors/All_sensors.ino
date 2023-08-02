#include <Wire.h>
#include "DHT.h"

#define DHTPIN 6  

#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

float calibration_value = 21.34 + 1;
int phval = 0; 
unsigned long int avgval; 
int buffer_arr[10],temp;

float ph_act;

void setup() 
{
  Wire.begin();
  Serial.begin(9600);
  dht.begin();

}
void loop() {
 delay(2000);

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
 if (isnan(h) || isnan(t)) {
   Serial.println(F("Failed to read from DHT sensor!"));
   return;
 }
 //This section measures air temperature and humidity end



 Serial.println("pH Val: ");
 Serial.println(ph_act);
 Serial.print(F("Humidity: "));
 Serial.print(h);
 Serial.print(F("%  Temperature: "));
 Serial.print(t);
 Serial.print(F("°C "));
 Serial.println();
 
}
