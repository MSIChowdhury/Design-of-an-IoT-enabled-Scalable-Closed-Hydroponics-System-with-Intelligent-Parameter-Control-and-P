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


//EC
#define address 100              //default I2C ID number for EZO EC Circuit.

char computerdata[32];           //we make a 32 byte character array to hold incoming data from a pc/mac/other.
byte code = 0;                   //used to hold the I2C response code.
char ec_data[32];                //we make a 32 byte character array to hold incoming data from the EC circuit.
byte in_char = 0;                //used as a 1 byte buffer to store inbound bytes from the EC Circuit.
byte i = 0;                      //counter used for ec_data array.

float EC;
float Test_EC=0;  //float var used to hold the float value of the conductivity.

//EC

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

void loop() {

////PH
//while(sensor_string_complete == false){
//  if (myserial.available() > 0) {                     //if we see that the Atlas Scientific product has sent a character
//    char inchar = (char)myserial.read();              //get the char we just received
//    sensorstring += inchar;                           //add the char to the var called sensorstring
//    if (inchar == '\r') {                             //if the incoming character is a <CR>
//      sensor_string_complete = true;                  //set the flag
//    }
//  }
//}
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
//// PH



////EC
//    Wire.beginTransmission(address);                                            //call the circuit by its ID number.
//    Wire.write("r");                                                   //transmit the command that was sent through the serial port.
//    Wire.endTransmission();                                                     //end the I2C data transmission.
//
//    delay(570);                                                             //wait the correct amount of time for the circuit to complete its instruction.
//    Wire.requestFrom(address, 32, 1);                                         //call the circuit and request 32 bytes (this could be too small, but it is the max i2c buffer size for an Arduino)
//    code = Wire.read();                                                       //the first byte is the response code, we read this separately.
//
//    while (Wire.available()) {                 //are there bytes to receive.
//      in_char = Wire.read();                   //receive a byte.
//      ec_data[i] = in_char;                    //load this byte into our array.
//      i += 1;                                  //incur the counter for the array element.
//      if (in_char == 0) {                      //if we see that we have been sent a null command.
//        i = 0;                                 //reset the counter i to 0.
//        break;                                 //exit the while loop.
//      }
//    }
//    
//    EC=atof(ec_data);
//
//////EC


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

  EC = 1023;
  pH = 7.05;
  humidity = 90;
  air_temperature = 30.0;
  water_temperature = 25.0;
  distance = 10;

 
  Serial.print(EC);
  Serial.print(",");
  Serial.print(pH);
  Serial.print(",");

  Serial.print(humidity);
  Serial.print(",");

  Serial.print(air_temperature);
  Serial.print(",");

  Serial.print(water_temperature);
  Serial.print(",");
  
  Serial.print(distance);
  Serial.println();

 
//  Serial.print("EC:");
//  Serial.print(EC);
//  Serial.println("  micro-siemens/cm");
//  Serial.print("pH Val: ");
//  Serial.println(pH);
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
