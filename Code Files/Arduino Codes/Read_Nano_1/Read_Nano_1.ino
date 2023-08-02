// Define the float variables
float EC;
float ph_act;
float humidity;
float air_temperature;
float water_temperature;
float waterLevel;


void setup() {
  // Start the serial communication
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(500);
}

void loop() {
  if (Serial1.available() >= sizeof(float) * 6) {
    // Create a byte array to hold the received data
    byte data[sizeof(float) * 6];

    // Read the byte array from the serial input
    Serial1.readBytes(data, sizeof(float) * 6);

    // Copy the bytes back to the float variables
    memcpy(&EC, data, sizeof(float));
    memcpy(&ph_act, data + sizeof(float), sizeof(float));
    memcpy(&humidity, data + (sizeof(float) * 2), sizeof(float));
    memcpy(&air_temperature, data + (sizeof(float) * 3), sizeof(float));
    memcpy(&water_temperature, data + (sizeof(float) * 4), sizeof(float));
    memcpy(&waterLevel, data + (sizeof(float) * 5), sizeof(float));
}
    Serial.print("EC: ");
    Serial.print(EC);
    Serial.println("  micro-siemens/cm");
    Serial.print("pH Val: ");
    Serial.println(ph_act);
    Serial.print(F("Humidity: "));
    Serial.print(humidity);
    Serial.println("%");
    Serial.print(F("Air Temperature: "));
    Serial.print(air_temperature);
    Serial.println(F("°C "));
    Serial.print("Water Temperature: ");
    Serial.print(water_temperature);
    Serial.println("°C");
    Serial.print("Water Level ");
    Serial.print(waterLevel);
    Serial.println(" cm");
    Serial.println();
    Serial.println();
    delay(1000);
}
