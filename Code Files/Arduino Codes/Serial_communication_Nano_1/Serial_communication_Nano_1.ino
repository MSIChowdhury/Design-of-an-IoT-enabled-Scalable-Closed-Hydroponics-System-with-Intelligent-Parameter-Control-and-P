// Define the float variables
float temperature = 25.10;
float ph = 7.10;
float EC = 1.2;
float humidity = 60.0;

void setup() {
  // Start the serial communication
  Serial.begin(9600);
}

void loop() {
  // Create a byte array to hold the data
  byte data[sizeof(float) * 4];
  
  // Copy the float values to the byte array
  memcpy(data, &temperature, sizeof(float));
  memcpy(data + sizeof(float), &ph, sizeof(float));
  memcpy(data + (sizeof(float) * 2), &EC, sizeof(float));
  memcpy(data + (sizeof(float) * 3), &humidity, sizeof(float));

  // Send the byte array
  Serial.write(data, sizeof(float) * 4);

  // Delay before sending the values again (adjust as needed)
  delay(1000);
}
