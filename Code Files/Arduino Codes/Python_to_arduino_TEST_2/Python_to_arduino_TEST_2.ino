String myCmd;

void setup() {
  
  Serial.begin(9600);
  pinMode(13, OUTPUT);
}

void loop() {
  while(Serial.available()==0){
    
  }

  myCmd = Serial.readStringUntil('\r');
  
  if(myCmd == "ON"){
    digitalWrite(13, HIGH);
  }
  if(myCmd == "OFF"){
    digitalWrite(13, LOW);
  }

}
