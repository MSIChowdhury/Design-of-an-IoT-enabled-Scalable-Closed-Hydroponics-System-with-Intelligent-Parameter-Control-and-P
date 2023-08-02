// Define pin numbers for pumps and relays
const int phUpPumpPin = 2;
const int phDownPumpPin = 3;
const int ecUpPumpPin = 4;
const int distilledWaterPumpPin = 5;
const int waterTemperaturePeltierRelayPin = 6;
const int airTemperaturePeltierRelayPin = 7;
const int airTemperatureFanPin = 8;

// Define timing constants
const unsigned long pHCheckInterval = 300000;  // 5 minutes
const unsigned long ecCheckInterval = 300000;  // 5 minutes
const unsigned long phpumpDuration = 20; // 20 milliseconds
const unsigned long ecpumpDuration = 20;
const unsigned long peltierDuration = 30000;   // 30 seconds
const unsigned long fanDuration = 20000;       // 20 seconds

// Variables to store previous activation times
unsigned long prevpHCheckTime = 0;
unsigned long prevecCheckTime = 0;
unsigned long prevWaterTempActivationTime = 0;
unsigned long prevAirTempActivationTime = 0;

// Variables for sensor readings
float EC = 0.0;
float pH = 0.0;
float airTemperature = 0.0;
float waterTemperature = 0.0;
float waterLevel = 0.0;
float humidity = 0.0;

// Flag variables for pump activation
bool phPumpFlag = false;
bool ecPumpFlag = false;
bool waterTemperatureFlag = false;

void setup() {
  // Initialize pump and relay pins as OUTPUT
  pinMode(phUpPumpPin, OUTPUT);
  pinMode(phDownPumpPin, OUTPUT);
  pinMode(ecUpPumpPin, OUTPUT);
  pinMode(distilledWaterPumpPin, OUTPUT);
  pinMode(waterTemperaturePeltierRelayPin, OUTPUT);
  pinMode(waterTemperaturePump, OUTPUT);
  pinMode(airTemperaturePeltierRelayPin, OUTPUT);
  pinMode(airTemperatureFanPin, OUTPUT);

  digitalWrite(phUpPumpPin, HIGH);
  digitalWrite(phDownPumpPin, HIGH);
  digitalWrite(ecUpPumpPin, HIGH);
  digitalWrite(distilledWaterPumpPin, HIGH);
  digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
  digitalWrite(waterTemperaturePump, HIGH);
  digitalWrite(airTemperaturePeltierRelayPin, HIGH);
  digitalWrite(airTemperatureFanPin, HIGH);
}

void loop() {
  // Read sensor values
  EC = readEC();
  pH = readpH();
  airTemperature = readAirTemperature();
  waterTemperature = readWaterTemperature();
  waterLevel = readWaterLevel();

  if (phPumpFlag == true){
    if (millis() - prevpHCheckTime >= pHCheckInterval) {
      phPumpFlag = false;
    }
  }

  if (phPumpFlag == false){
  // Check if pH is too high
    if (pH > 6.8) {
      digitalWrite(phDownPumpPin, LOW);
      delay(phpumpDuration);
      digitalWrite(phDownPumpPin, HIGH);
      
      prevpHCheckTime = millis();
      phPumpFlag = true;
      }
    // Check if pH is too low
    else if (pH < 5.5) {
      digitalWrite(phUpPumpPin, LOW);
      delay(phpumpDuration);
      digitalWrite(phUpPumpPin, HIGH);
      
      prevpHCheckTime = millis();
      phPumpFlag = true;
      }
    }


//Check EC

  if (ecPumpFlag == true){
    if (millis() - prevecCheckTime >= ecCheckInterval) {
      ecPumpFlag = false;
    }
  }

  if (ecPumpFlag == false){
  // Check if pH is too high
    if (EC < 1000) {
      digitalWrite(ecUpPumpPin, LOW);
      delay(ecpumpDuration);
      digitalWrite(ecUpPumpPin, HIGH);
      
      prevecCheckTime = millis();
      ecPumpFlag = true;
      }
    // Check if pH is too low
    else if (EC > 1300) {
      digitalWrite(distilledWaterPumpPin, LOW);
      delay(ecpumpDuration);
      digitalWrite(distilledWaterPumpPin, HIGH);
      
      prevecCheckTime = millis();
      ecPumpFlag = true;
      }
    }



//Water Temperature

  if (waterTemperature > 22.0){
    if (waterTemperatureFlag == false) {
      digitalWrite(waterTemperaturePeltierRelayPin, LOW);
      prevWaterTempActivationTime = millis();
      waterTemperatureFlag = true;
    }
    if (waterTemperatureFlag == true){
      if (millis() - prevWaterTempActivationTime >= peltierDuration) {
        digitalWrite(waterTemperaturePump, LOW);
        
      }
    }
  }
  
  if (waterTemperature < 18.0){
    digitalWrite(waterTemperaturePump, HIGH);
    digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
    waterTemperatureFlag = false;
  }


//Air Temperature
  if (airTemperature > 24.0){
    digitalWrite(airTemperaturePeltierRelayPin, LOW);
    //Air Pletier Fan have to connected with this relay. So they would turn on together
    }

  if (airTemperature < 18.0){
    digitalWrite(airTemperaturePeltierRelayPin, HIGH);
  }


}


// Functions to read sensor values (replace with actual sensor reading functions)
float readEC() {
  return 0.0;  // Replace with actual EC reading
}

float readpH() {
  return 0.0;  // Replace with actual pH reading
}

float readAirTemperature() {
  return 0.0;  // Replace with actual air temperature reading
}

float readWaterTemperature() {
  return 0.0;  // Replace with actual water temperature reading
}

float readWaterLevel() {
  return 0.0;  // Replace with actual water level reading
}
