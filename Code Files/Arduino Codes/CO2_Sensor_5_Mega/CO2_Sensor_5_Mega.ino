#include <Arduino.h>
#include "MHZ19.h"                                        

MHZ19 myMHZ19;                                             // Constructor for library

unsigned long getDataTimer = 0;
int CO2;

void setup()
{
    Serial.begin(9600);                                     // Device to serial monitor feedback
    Serial1.begin(9600);
   
    myMHZ19.begin(Serial1);                                // *Serial(Stream) refence must be passed to library begin(). 

    myMHZ19.autoCalibration(false);                              // Turn auto calibration ON (OFF autoCalibration(false))
    delay(1000);
    
    for(int j=0; j<=5; j++){
      CO2 = myMHZ19.getCO2();
      delay(1000);
    }
    
}

void loop()
{
    if (millis() - getDataTimer >= 2000)
    {
        Serial.println("Hola");
        int CO2; 

        /* note: getCO2() default is command "CO2 Unlimited". This returns the correct CO2 reading even 
        if below background CO2 levels or above range (useful to validate sensor). You can use the 
        usual documented command with getCO2(false) */

        CO2 = myMHZ19.getCO2();                             // Request CO2 (as ppm)
        
//        Serial.print("CO2 (ppm): ");                      
        Serial.println(CO2);
//        Serial.print(",");                                

        int8_t Temp;
        Temp = myMHZ19.getTemperature();                     // Request Temperature (as Celsius)
//        Serial.print("Temperature (C): ");                  
//        Serial.println(Temp);                               

        getDataTimer = millis();
    }
}
