//This code will work on an Arduino Uno and Mega
//This code was written to be easy to understand.
//Modify this code as you see fit.
//This code will output data to the Arduino serial monitor.
//Type commands into the Arduino serial monitor to control the EZO EC Circuit.
//This code was written in the Arduino 2.0 IDE
//This code was last tested 10/2022


#include <Wire.h>                //enable I2C.
#define address 100              //default I2C ID number for EZO EC Circuit.



char computerdata[32];           //we make a 32 byte character array to hold incoming data from a pc/mac/other.
byte code = 0;                   //used to hold the I2C response code.
char ec_data[32];                //we make a 32 byte character array to hold incoming data from the EC circuit.
byte in_char = 0;                //used as a 1 byte buffer to store inbound bytes from the EC Circuit.
byte i = 0;                      //counter used for ec_data array.


float EC;                  //float var used to hold the float value of the conductivity.


void setup()                     //hardware initialization.
{
  Serial.begin(9600);            //enable serial port.
  Wire.begin();                  //enable I2C port.
}



void loop() {                                                                     //the main loop.                                                            //if any other command has been sent we wait only 250ms 
    Wire.beginTransmission(address);                                            //call the circuit by its ID number.
    Wire.write("r");                                                   //transmit the command that was sent through the serial port.
    Wire.endTransmission();                                                     //end the I2C data transmission.

    delay(570);                                                             //wait the correct amount of time for the circuit to complete its instruction.
    Wire.requestFrom(address, 32, 1);                                         //call the circuit and request 32 bytes (this could be too small, but it is the max i2c buffer size for an Arduino)
    code = Wire.read();                                                       //the first byte is the response code, we read this separately.

    while (Wire.available()) {                 //are there bytes to receive.
      in_char = Wire.read();                   //receive a byte.
      ec_data[i] = in_char;                    //load this byte into our array.
      i += 1;                                  //incur the counter for the array element.
      if (in_char == 0) {                      //if we see that we have been sent a null command.
        i = 0;                                 //reset the counter i to 0.
        break;                                 //exit the while loop.
      }
    }
    EC=atof(ec_data);
    Serial.println(EC);                  //print the data.
    Serial.println();                         //this just makes the output easier to read by adding an extra blank line 
}
  
