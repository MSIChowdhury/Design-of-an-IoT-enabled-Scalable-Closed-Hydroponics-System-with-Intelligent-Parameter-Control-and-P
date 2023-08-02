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
const unsigned long pumpDuration = 20;         // 20 milliseconds
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
bool activatePhUpPump = false;
bool activatePhDownPump = false;
bool activateECUpPump = false;
bool activateDistilledWaterPump = false;
bool activateWaterTempPeltier = false;
bool activateWaterTempPump = false;
bool activateAirTempPeltier = false;
bool activateAirTempFan = false;

void setup() {
  // Initialize pump and relay pins as OUTPUT
  pinMode(phUpPumpPin, OUTPUT);
  pinMode(phDownPumpPin, OUTPUT);
  pinMode(ecUpPumpPin, OUTPUT);
  pinMode(distilledWaterPumpPin, OUTPUT);
  pinMode(waterTemperaturePeltierRelayPin, OUTPUT);
  pinMode(airTemperaturePeltierRelayPin, OUTPUT);
  pinMode(airTemperatureFanPin, OUTPUT);
}

void loop() {
  // Read sensor values
  EC = readEC();
  pH = readpH();
  airTemperature = readAirTemperature();
  waterTemperature = readWaterTemperature();
  waterLevel = readWaterLevel();

  // Check pH every pHCheckInterval milliseconds
  if (millis() - prevpHCheckTime >= pHCheckInterval) {
    // Check if pH is too high
    if (pH > 6.8) {
      activatePhDownPump = true;
    }
    // Check if pH is too low
    else if (pH < 5.5) {
      activatePhUpPump = true;
    }
    prevpHCheckTime = millis();  // Update previous pH check time
  }

  // Check EC every ecCheckInterval milliseconds
  if (millis() - prevecCheckTime >= ecCheckInterval) {
    // Check if EC is too low
    if (EC < 1000) {
      activateECUpPump = true;
    }
    // Check if EC is too high
    else if (EC > 1400) {
      activateDistilledWaterPump = true;
    }
    prevecCheckTime = millis();  // Update previous EC check time
  }

  // Check water temperature
  if (waterTemperature > 22) {
    activateWaterTempPeltier = true;
    if (millis() - prevWaterTempActivationTime >= peltierDuration) {
      activateWaterTempPump = true;
    }
    // Check if water temperature has reached 18
    if (waterTemperature <= 18) {
      activateWaterTempPeltier = false;
      activateWaterTempPump = false;
    }
  }

  // Check air temperature
  if (airTemperature > 24) {
    activateAirTempPeltier = true;
    if (millis() - prevAirTempActivationTime >= peltierDuration) {
      activateAirTempFan = true;
    }
    // Check if air temperature has reached 18
    if (airTemperature <= 18) {
      activateAirTempPeltier = false;
      activateAirTempFan = false;
    }
  }

  // Control pumps and relays
  controlPumps();
  controlRelays();
}

// Function to control pumps based on the activation flags
void controlPumps() {
  // Ph Up pump
  if (activatePhUpPump) {
    digitalWrite(phUpPumpPin, HIGH);
    delay(pumpDuration);
    digitalWrite(phUpPumpPin, LOW);
    activatePhUpPump = false;
    prevpHCheckTime = millis();  // Reset pH check time
  }

  // Ph Down pump
  if (activatePhDownPump) {
    digitalWrite(phDownPumpPin, HIGH);
    delay(pumpDuration);
    digitalWrite(phDownPumpPin, LOW);
    activatePhDownPump = false;
    prevpHCheckTime = millis();  // Reset pH check time
  }

  // EC Up pump
  if (activateECUpPump) {
    digitalWrite(ecUpPumpPin, HIGH);
    delay(pumpDuration);
    digitalWrite(ecUpPumpPin, LOW);
    activateECUpPump = false;
    prevecCheckTime = millis();  // Reset EC check time
  }

  // Distilled water pump
  if (activateDistilledWaterPump) {
    digitalWrite(distilledWaterPumpPin, HIGH);
    delay(pumpDuration);
    digitalWrite(distilledWaterPumpPin, LOW);
    activateDistilledWaterPump = false;
    prevecCheckTime = millis();  // Reset EC check time
  }

  // Water temperature pump
  if (activateWaterTempPump) {
    digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
    delay(pumpDuration);
    digitalWrite(waterTemperaturePeltierRelayPin, LOW);
    activateWaterTempPump = false;
    prevWaterTempActivationTime = millis();  // Reset water temperature activation time
  }
}

// Function to control relays based on the activation flags
void controlRelays() {
  // Water temperature peltier module relay
  if (activateWaterTempPeltier) {
    digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
  } else {
    digitalWrite(waterTemperaturePeltierRelayPin, LOW);
  }

  // Air temperature peltier module relay
  if (activateAirTempPeltier) {
    digitalWrite(airTemperaturePeltierRelayPin, HIGH);
  } else {
    digitalWrite(airTemperaturePeltierRelayPin, LOW);
  }

  // Air temperature fan
  if (activateAirTempFan) {
    digitalWrite(airTemperatureFanPin, HIGH);
  } else {
    digitalWrite(airTemperatureFanPin, LOW);
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
