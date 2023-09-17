const int bufferSize = 4; // Adjust this according to your needs
char inputString[bufferSize]; // A character array to store the incoming string
char *token; // A pointer to help with parsing
int pinNumber, pinState;

void setup() {
  Serial.begin(9600);
  pinMode(22,OUTPUT);
  pinMode(23,OUTPUT);
  pinMode(24,OUTPUT);
  pinMode(25,OUTPUT);
  pinMode(26,OUTPUT);
  pinMode(40,OUTPUT);
  pinMode(13,OUTPUT);
  pinMode(41,OUTPUT);
  pinMode(42,OUTPUT);

  digitalWrite(22, HIGH);
  digitalWrite(23, HIGH);
  digitalWrite(24, HIGH);
  digitalWrite(25, HIGH);
  digitalWrite(26, HIGH);
  digitalWrite(13, HIGH);
  digitalWrite(40, HIGH);
  digitalWrite(41, HIGH);
  digitalWrite(42, HIGH);
  
}

void loop() {
  while(Serial.available()==0)
  {    
  }
  Serial.readBytesUntil('\n', inputString, bufferSize);
  
  // Parse the inputString using strtok to split it into tokens
  token = strtok(inputString, ",");
    
  // Check if the token is not null (indicating that it found a comma)
  if (token != NULL) {
    // Convert the first token (pin number) to an integer
    pinNumber = atoi(token);
      
    // Move to the next token
    token = strtok(NULL, ",");
      
    // Check if the second token is not null (indicating that it found another comma)
    if (token != NULL) {
      // Convert the second token (pin state) to an integer
      pinState = atoi(token);
        
      // Now, you have pinNumber and pinState as separate variables
      // You can use them in your Arduino code as needed
      // For example, you can digitalWrite(pinNumber, pinState) to set the pin stat
      digitalWrite(pinNumber, pinState);
      }
    }
}
