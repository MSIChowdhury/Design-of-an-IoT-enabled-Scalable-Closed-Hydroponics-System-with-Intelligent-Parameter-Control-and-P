// Define pin numbers for pumps and relays
const int phUpPumpPin = 22;
const int phDownPumpPin = 23;
const int ecAUpPumpPin = 32;
const int ecBUpPumpPin = 33;
const int distilledWaterPumpPin = 26;
const int waterTemperaturePeltierRelayPin = 27;
const int waterTemperaturePump = 28;
const int airTemperaturePeltierRelayPin = 29;
const int airTemperatureFanPin = 30;

// Define timing constants
const unsigned long pHCheckInterval = 60000;  // 5 minutes
const unsigned long ecCheckInterval = 60000;  // 5 minutes
const unsigned long phpumpDuration = 4000; // 20 milliseconds
const unsigned long ecApumpDuration = 20;
const unsigned long ecBpumpDuration = 25;
const unsigned long waterpumpDuration = 20;
const unsigned long peltierDuration = 30000;   // 30 seconds
const unsigned long fanDuration = 20000;       // 20 seconds

// Variables to store previous activation times
unsigned long prevpHCheckTime = 0;
unsigned long prevecCheckTime = 0;
unsigned long prevWaterTempActivationTime = 0;
unsigned long prevAirTempActivationTime = 0;

// Variables for sensor readings
float EC ;
float pH ;
float airTemperature ;
float waterTemperature ;
float waterLevel ;
float humidity ;

// Flag variables for pump activation
bool phPumpFlag = false;
bool ecPumpFlag = false;
bool waterTemperatureFlag = false;

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(100);
  // Initialize pump and relay pins as OUTPUT
  pinMode(phUpPumpPin, OUTPUT);
  pinMode(phDownPumpPin, OUTPUT);
  pinMode(ecAUpPumpPin, OUTPUT);
  pinMode(ecBUpPumpPin, OUTPUT);
  pinMode(distilledWaterPumpPin, OUTPUT);
  pinMode(waterTemperaturePeltierRelayPin, OUTPUT);
  pinMode(waterTemperaturePump, OUTPUT);
  pinMode(airTemperaturePeltierRelayPin, OUTPUT);
  pinMode(airTemperatureFanPin, OUTPUT);

  digitalWrite(phUpPumpPin, HIGH);
  digitalWrite(phDownPumpPin, HIGH);
  digitalWrite(ecAUpPumpPin, HIGH);
  digitalWrite(ecBUpPumpPin, HIGH);
  digitalWrite(distilledWaterPumpPin, HIGH);
  digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
  digitalWrite(waterTemperaturePump, HIGH);
  digitalWrite(airTemperaturePeltierRelayPin, HIGH);
  digitalWrite(airTemperatureFanPin, HIGH);
  delay(5000);
}

void loop() {

//Reading Sensor Values
  if (Serial1.available() >= sizeof(float) * 6) {
    // Create a byte array to hold the received data
    byte data[sizeof(float) * 6];

    // Read the byte array from the serial input
    Serial1.readBytes(data, sizeof(float) * 6);

    // Copy the bytes back to the float variables
    memcpy(&EC, data, sizeof(float));
    memcpy(&pH, data + sizeof(float), sizeof(float));
    memcpy(&humidity, data + (sizeof(float) * 2), sizeof(float));
    memcpy(&airTemperature, data + (sizeof(float) * 3), sizeof(float));
    memcpy(&waterTemperature, data + (sizeof(float) * 4), sizeof(float));
    memcpy(&waterLevel, data + (sizeof(float) * 5), sizeof(float));
  }
  

    Serial.print("EC: ");
    Serial.print(EC);
    Serial.println("  micro-siemens/cm");
//    Serial.print("pH: ");
//    Serial.println(pH);
//    Serial.print(F("Humidity: "));
//    Serial.print(humidity);
//    Serial.println("%");
//    Serial.print(F("Air Temperature: "));
//    Serial.print(airTemperature);
//    Serial.println(F("°C "));
    Serial.print("Water Temperature: ");
    Serial.print(waterTemperature);
    Serial.println("°C");
//    Serial.print("Water Level ");
//    Serial.print(waterLevel);
//    Serial.println(" cm");
//    Serial.println();
//    Serial.println();
    delay(1000);


  
//  if (pH < 2 || pH > 14){
//    pH =6;
//  }
////Controlling pH
//  if (phPumpFlag == true){
//    if (millis() - prevpHCheckTime >= pHCheckInterval) {
//      phPumpFlag = false;
//    }
//  }
//
//  if (phPumpFlag == false){
//  // Check if pH is too high
//    if (pH > 6.5) {
//      digitalWrite(phDownPumpPin, LOW);
//      delay(phpumpDuration);
//      digitalWrite(phDownPumpPin, HIGH);
//      
//      prevpHCheckTime = millis();
//      phPumpFlag = true;
//      }
//    // Check if pH is too low
//    else if (pH < 5.5) {
//      digitalWrite(phUpPumpPin, LOW);
//      delay(phpumpDuration);
//      digitalWrite(phUpPumpPin, HIGH);
//      
//      prevpHCheckTime = millis();
//      phPumpFlag = true;
//      }
//    }

//
////Check EC
//
//  if (ecPumpFlag == true){
//    if (millis() - prevecCheckTime >= ecCheckInterval) {
//      ecPumpFlag = false;
//    }
//  }
//
//  if (ecPumpFlag == false){
//  // Check if EC is too high
//    if (EC < 800) {
//      digitalWrite(ecAUpPumpPin, LOW);
//      delay(ecApumpDuration);
//      digitalWrite(ecAUpPumpPin, HIGH);
//      digitalWrite(ecBUpPumpPin, LOW);
//      delay(ecBpumpDuration);
//      digitalWrite(ecBUpPumpPin, HIGH);
//      
//      
//      prevecCheckTime = millis();
//      ecPumpFlag = true;
//      }
//    // Check if pH is too low
//    else if (EC > 1200) {
//      digitalWrite(distilledWaterPumpPin, LOW);
//      delay(waterpumpDuration);
//      digitalWrite(distilledWaterPumpPin, HIGH);
//      
//      prevecCheckTime = millis();
//      ecPumpFlag = true;
//      }
//    }

//
//
////Water Temperature
//
//  if (waterTemperature > 22.0){
//    if (waterTemperatureFlag == false) {
//      digitalWrite(waterTemperaturePeltierRelayPin, LOW);
//      prevWaterTempActivationTime = millis();
//      waterTemperatureFlag = true;
//    }
//    if (waterTemperatureFlag == true){
//      if (millis() - prevWaterTempActivationTime >= peltierDuration) {
//        digitalWrite(waterTemperaturePump, LOW);
//        
//      }
//    }
//  }
//  
//  if (waterTemperature < 18.0){
//    digitalWrite(waterTemperaturePump, HIGH);
//    digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
//    waterTemperatureFlag = false;
//  }
//
//
////Air Temperature
//  if (airTemperature > 24.0){
//    digitalWrite(airTemperaturePeltierRelayPin, LOW);
//    //Air Pletier Fan have to connected with this relay. So they would turn on together
//    }
//
//  if (airTemperature < 18.0){
//    digitalWrite(airTemperaturePeltierRelayPin, HIGH);
//  }


}
