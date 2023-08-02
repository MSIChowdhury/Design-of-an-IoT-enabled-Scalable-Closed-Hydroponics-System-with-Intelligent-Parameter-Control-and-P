float EC;
int count = 0;
int new_count ;
int old_count;
bool countFlag = false;

void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(A0)); 
}

void loop() {
  float noise = random(-1000, 1001) / 1000.0;
  EC = (25000)/ (100+noise);

  old_count = count;
  new_count = count + 1; 

  if (countFlag = false){
    
  }
  
  
  Serial.println(EC); 
  delay(1000); 
}
