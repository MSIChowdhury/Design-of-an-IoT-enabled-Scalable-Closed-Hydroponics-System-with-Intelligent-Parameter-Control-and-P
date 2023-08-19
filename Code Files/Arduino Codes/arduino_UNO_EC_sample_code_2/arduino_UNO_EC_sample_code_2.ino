//This code was written to be easy to understand.
//Modify this code as you see fit.
//This code will output data to the Arduino serial monitor.
//Type commands into the Arduino serial monitor to control the EC circuit.
//This code was written in the Arduino 2.0 IDE
//This code was last tested 10/2022


#include <SoftwareSerial.h>                           //we have to include the SoftwareSerial library, or else we can't use it
#define rx2 12                                          //define what pin rx is going to be
#define tx2 13                                          //define what pin tx is going to be

SoftwareSerial myserial2(rx2, tx2);                      //define how the soft serial port is going to work


String inputstring2 = "";                              //a string to hold incoming data from the PC
String sensorstring2 = "";                             //a string to hold the data from the Atlas Scientific product
boolean input_string_complete2 = false;                //have we received all the data from the PC
boolean sensor_string_complete2 = false;               //have we received all the data from the Atlas Scientific product




void setup() {                                        //set up the hardware
  Serial.begin(9600);                                 //set baud rate for the hardware serial port_0 to 9600
  myserial2.begin(9600);                               //set baud rate for the software serial port to 9600
  inputstring2.reserve(10);                            //set aside some bytes for receiving data from the PC
  sensorstring2.reserve(30);                           //set aside some bytes for receiving data from Atlas Scientific product
}


void serialEvent() {                                  //if the hardware serial port_0 receives a char
  inputstring2 = Serial.readStringUntil(13);           //read the string until we see a <CR>
  input_string_complete2 = true;                       //set the flag used to tell if we have received a completed string from the PC
}


void loop() {                                         //here we go...

  if (input_string_complete2 == true) {                //if a string from the PC has been received in its entirety
    myserial2.print(inputstring2);                      //send that string to the Atlas Scientific product
    myserial2.print('\r');                             //add a <CR> to the end of the string
    inputstring2 = "";                                 //clear the string
    input_string_complete2 = false;                    //reset the flag used to tell if we have received a completed string from the PC
  }

  if (myserial2.available() > 0) {                     //if we see that the Atlas Scientific product has sent a character
    char inchar2 = (char)myserial2.read();              //get the char we just received
    sensorstring2 += inchar2;                           //add the char to the var called sensorstring
    if (inchar2 == '\r') {                             //if the incoming character is a <CR>
      sensor_string_complete2 = true;                  //set the flag
    }
  }


  if (sensor_string_complete2 == true) {               //if a string from the Atlas Scientific product has been received in its entirety
    if (isdigit(sensorstring2[0]) == false) {          //if the first character in the string is a digit
      Serial.println(sensorstring2);                   //send that string to the PC's serial monitor
    }
    else                                              //if the first character in the string is NOT a digit
    {
      char sensorstring_array2[10];                        //we make a char array
      char *EC_char;                                           //char pointer used in string parsing
      float EC;                                         //used to hold a floating point number that is the EC
  
      sensorstring2.toCharArray(sensorstring_array2, 10);   //convert the string to a char array 
      EC_char = strtok(sensorstring_array2, ",");               //let's pars the array at each comma
      EC = atof(EC_char);
      Serial.print("EC:");                                //we now print each value we parsed separately
      Serial.println(EC);                                 //this is the EC value
    
      Serial.println();                                   //this just makes the output easier to read                                //then call this function 
    }
    sensorstring2 = "";                                //clear the string
    sensor_string_complete2 = false;                   //reset the flag used to tell if we have received a completed string from the Atlas Scientific product
  }
}
