#include <Arduino.h>
#include "MHZ19.h"

MHZ19 myMHZ19;

unsigned long getDataTimer = 0;
unsigned long lastTimestamp = 0;

void setup()
{
    Serial.begin(9600);
    Serial1.begin(9600);
    myMHZ19.begin(Serial1);
    myMHZ19.autoCalibration(false);
    delay(1000);
}

void loop()
{
    if (millis() - getDataTimer >= 2000)
    {
        int CO2 = myMHZ19.getCO2();
        int8_t Temp = myMHZ19.getTemperature();
        getDataTimer = millis();

        // Calculate the elapsed time and convert it to a more human-readable timestamp
        unsigned long elapsedSeconds = (getDataTimer - lastTimestamp) / 1000;
        lastTimestamp = getDataTimer;

        // Send the data over the serial connection
        Serial.print(getFormattedTime(elapsedSeconds));
        Serial.print(",");
        Serial.println(CO2);
    }
}

String getFormattedTime(unsigned long elapsedSeconds)
{
    // Calculate hours, minutes, and seconds
    unsigned long hours = elapsedSeconds / 3600;
    unsigned long minutes = (elapsedSeconds % 3600) / 60;
    unsigned long seconds = elapsedSeconds % 60;

    // Create a formatted timestamp string
    String timestamp = String(hours) + ":" + String(minutes) + ":" + String(seconds);
    return timestamp;
}
