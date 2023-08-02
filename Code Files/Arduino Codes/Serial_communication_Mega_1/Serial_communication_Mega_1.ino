// Define the float variables
float temperature;
float ph;
float EC;
float humidity;

void setup() {
  // Start the serial communication
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(100);
}

void loop() {
  if (Serial1.available() >= sizeof(float) * 4) {
    // Create a byte array to hold the received data
    byte data[sizeof(float) * 4];

    // Read the byte array from the serial input
    Serial1.readBytes(data, sizeof(float) * 4);

    // Copy the bytes back to the float variables
    memcpy(&temperature, data, sizeof(float));
    memcpy(&ph, data + sizeof(float), sizeof(float));
    memcpy(&EC, data + (sizeof(float) * 2), sizeof(float));
    memcpy(&humidity, data + (sizeof(float) * 3), sizeof(float));

    // Print the received values
    Serial.print("Temperature: ");
    Serial.print(temperature/2);
    Serial.print(" Celsius\t");
    Serial.print("pH: ");
    Serial.print(ph);
    Serial.print("\tEC: ");
    Serial.print(EC);
    Serial.print(" ms/cm\t");
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println("%");
  }
}
