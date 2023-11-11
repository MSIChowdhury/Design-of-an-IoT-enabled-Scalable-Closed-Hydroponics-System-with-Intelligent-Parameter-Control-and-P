#include <Arduino.h>
#include "MHZ19.h" 

//Air Temperature and Humidity Sensor
#include "DHT.h"
#define DHTPIN 5
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

MHZ19 myMHZ19;                                             // Constructor for library

unsigned long getDataTimer = 0;
int CO2;

void setup()
{
    Serial.begin(9600);                                     // Device to serial monitor feedback
    Serial1.begin(9600);

    //Air Temperature and Humidity Sensor
    dht.begin();
   
    myMHZ19.begin(Serial1);                                // *Serial(Stream) refence must be passed to library begin(). 
    myMHZ19.autoCalibration(false);                              // Turn auto calibration ON (OFF autoCalibration(false))
    delay(1000);
    
    for(int j=0; j<=5; j++){
      CO2 = myMHZ19.getCO2();
      delay(100);
    }   
}

void loop()
{
    if (millis() - getDataTimer >= 1100)
    {
        CO2 = myMHZ19.getCO2();                       
   
        //This Section measures air temperature and humidity start
        float humidity = dht.readHumidity();
        // Read temperature as Celsius (the default)
        float air_temperature = dht.readTemperature();

        getDataTimer = millis();

//      Serial.print("Humidity: ");
//      Serial.println(humidity);
//      Serial.print("Air Temperature: ");
//      Serial.print(air_temperature);
//      Serial.println(" C");      

        Serial.print(CO2);
        Serial.print(",");

        Serial.print(air_temperature);
        Serial.print(",");
          
        Serial.print(humidity);
        Serial.println();

    }

    
}
