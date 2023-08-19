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

//pH
#include <SoftwareSerial.h>                           //we have to include the SoftwareSerial library, or else we can't use it
#define rx 4                                          //define what pin rx is going to be
#define tx 3                                          //define what pin tx is going to be

SoftwareSerial myserial(rx, tx);                      //define how the soft serial port is going to work


String inputstring = "";                              //a string to hold incoming data from the PC
String sensorstring = "";                             //a string to hold the data from the Atlas Scientific product
boolean input_string_complete = false;                //have we received all the data from the PC
boolean sensor_string_complete = false;               //have we received all the data from the Atlas Scientific product
float pH;
//pH


//EC

#define rx2 12                                          //define what pin rx is going to be
#define tx2 13                                          //define what pin tx is going to be
float EC;
SoftwareSerial myserial2(rx2, tx2);                      //define how the soft serial port is going to work


String inputstring2 = "";                              //a string to hold incoming data from the PC
String sensorstring2 = "";                             //a string to hold the data from the Atlas Scientific product
boolean input_string_complete2 = false;                //have we received all the data from the PC
boolean sensor_string_complete2 = false;               //have we received all the data from the Atlas Scientific product

//EC


//Ultrasonic Sensor
const int trigPin = 9;
const int echoPin = 10;

long duration;
int distance;
float waterLevel;
float groundLevel= 13;
//



void setup()
{
  Wire.begin();
  Serial.begin(9600);
  myserial.begin(9600);                               //set baud rate for the software serial port to 9600
  inputstring.reserve(10);                            //set aside some bytes for receiving data from the PC
  sensorstring.reserve(30);  

  myserial2.begin(9600);                               //set baud rate for the software serial port to 9600
  inputstring2.reserve(10);                            //set aside some bytes for receiving data from the PC
  sensorstring2.reserve(30);                           //set aside some bytes for receiving data from Atlas Scientific product
  
  pinMode(EC_on, OUTPUT);

  dht.begin();
  dallasTemperature.begin();

  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  delay(1000);

}

void serialEvent() {                                  //if the hardware serial port_0 receives a char
  inputstring = Serial.readStringUntil(13);           //read the string until we see a <CR>
  input_string_complete = true;                       //set the flag used to tell if we have received a completed string from the PC
}

void serialEvent2() {                                  //if the hardware serial port_0 receives a char
  inputstring2 = Serial.readStringUntil(13);           //read the string until we see a <CR>
  input_string_complete2 = true;                       //set the flag used to tell if we have received a completed string from the PC
}

void loop() {

////PH
//  if (myserial.available() > 0) {                     //if we see that the Atlas Scientific product has sent a character
//    char inchar = (char)myserial.read();              //get the char we just received
//    sensorstring += inchar;                           //add the char to the var called sensorstring
//    if (inchar == '\r') {                             //if the incoming character is a <CR>
//      sensor_string_complete = true;                  //set the flag
//    }
//  }
//
//
//  if (sensor_string_complete == true) {               //if a string from the Atlas Scientific product has been received in its entirety
////    Serial.println(sensorstring);                     //send that string to the PC's serial monitor
//    
//                                              //uncomment this section to see how to convert the pH reading from a string to a float 
//    if (isdigit(sensorstring[0])) {                   //if the first character in the string is a digit
//      pH = sensorstring.toFloat();                    //convert the string to a floating point number so it can be evaluated by the Arduino
//    }
//
//    sensorstring = "";                                //clear the string
//    sensor_string_complete = false;                   //reset the flag used to tell if we have received a completed string from the Atlas Scientific product
//  }
//
//// This section measure pH END


//EC
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
//EC


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
  waterLevel = groundLevel - distance;
  
  //Ultrasonic Sensor END



//  // Create a byte array to hold the data
//  byte data[sizeof(float) * 6];
//  
//  // Copy the float values to the byte array
//  memcpy(data, &EC, sizeof(float));
//  memcpy(data + sizeof(float), &pH, sizeof(float));
//  memcpy(data + (sizeof(float) * 2), &humidity, sizeof(float));
//  memcpy(data + (sizeof(float) * 3), &air_temperature, sizeof(float));
//  memcpy(data + (sizeof(float) * 4), &water_temperature, sizeof(float));
//  memcpy(data + (sizeof(float) * 5), &waterLevel, sizeof(float));
//
//  // Send the byte array
//  Serial.write(data, sizeof(float) * 6);
//
//  // Delay before sending the values again (adjust as needed)
//  delay(20);

  
  Serial.print("EC:");
  Serial.print(EC);
  Serial.println("  micro-siemens/cm");
//  Serial.print("pH Val: ");
//  Serial.println(ph_act);
//  Serial.print(F("Humidity: "));
//  Serial.print(humidity);
//  Serial.println("%");
//  Serial.print(F("Air Temperature: "));
//  Serial.print(air_temperature);
//  Serial.println(F("°C "));
//  Serial.print("Water Temperature: ");
//  Serial.print(water_temperature);
//  Serial.println("°C");
//  Serial.print("Distance: ");
//  Serial.print(distance);
//  Serial.println(" cm");
//  Serial.println();
//  Serial.println();

}
