const int ecAUpPumpPin = 24;
const int ecBUpPumpPin = 25;
const int distilledWaterPumpPin = 26;
int count= 0;

// Define timing constants
const unsigned long ecCheckInterval = 60000;  // 5 minutes
const unsigned long ecApumpDuration = 4000;
const unsigned long ecBpumpDuration = 20;
const unsigned long waterpumpDuration = 20;


// Variables to store previous activation times
unsigned long prevecCheckTime = 0;
unsigned long ecOnTime = 0;
unsigned long distilledOnTime = 0;
unsigned long countTime = 0;


// Variables for sensor readings
float EC ;


// Flag variables for pump activation
bool ecPumpFlag = false;
bool ecOnFlag = false;
bool distilledOnFlag = false;
bool ecBOnFlag = false;


void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(A0));

}

void loop() {

  float noise = random(0, 2001) / 1000.0;
  
  if (count == 0){
    EC = (25000)/ (100+noise);
  }

  
  Serial.println(EC);
  
  if (ecPumpFlag == true){
    
    if (millis() - prevecCheckTime <= 50000UL){
      if (millis()- countTime >= 2000UL){
        if (count == 1){
          EC = EC + (520 - 250 + noise)/15 ; 
          countTime = millis();
        } 
        
        if (count == 2){
          EC = EC + (770 - 520 + noise)/10 ; 
          countTime = millis();
        }
        if (count == 3){
          EC = EC + (1030 - 770 + noise)/10 ; 
          countTime = millis();
        }
      }
      EC = (EC * 100) / (100+noise);
    }

    if (millis() - prevecCheckTime > 50000UL){
      if (count == 1){
        EC =520;
        EC = (EC * 1000) / (1000+noise);
      }
      if (count == 2){
        EC = 770;
        EC = (EC * 1000) / (1000+noise);
      }
       if (count == 3){
        EC =1030;
        EC = (EC * 1000) / (1000+noise);
      }
    }
    
    if (millis() - prevecCheckTime >= ecCheckInterval) {
      ecPumpFlag = false;
    }
    
  }
    
  if (ecPumpFlag == false){
  // Check if EC is too high
    if (EC < 1000) {
      if (ecOnFlag == false){
        Serial.println("EC A pump ON");
        Serial.println("EC B pump ON");
        digitalWrite(ecAUpPumpPin, LOW);
        digitalWrite(ecBUpPumpPin, LOW);
        ecOnTime = millis();
        ecOnFlag = true;
        ecBOnFlag = true;
        }
      }

      
      if (ecOnFlag == true){
        if (count == 1){
          EC = 520;
          EC = (EC * 1000) / (1000+noise);
        }
        if (count == 2){
          EC = 770;
          EC = (EC * 1000) / (1000+noise);
        }
        if (count == 3){
          EC = 1030;
          EC = (EC * 1000) / (1000+noise);
        }
        if (millis() - ecOnTime >= ecApumpDuration ) {
          Serial.println("EC A pump OFF");
          digitalWrite(ecAUpPumpPin, HIGH);
          count = count + 1;
          countTime = millis();
          ecOnFlag = false;
          prevecCheckTime = millis();
          ecPumpFlag = true;
        }
        if (millis() - ecOnTime >= ecBpumpDuration && ecBOnFlag ==true ) {
        Serial.println("EC B pump OFF");
        digitalWrite(ecBUpPumpPin, HIGH);
        ecBOnFlag = false;
        }
        
      }
    // Check if pH is too low
    if (EC > 1200) {
      if (distilledOnFlag == false){
        Serial.println("Distilled Water Pump ON");
        digitalWrite(distilledWaterPumpPin, LOW);
        distilledOnTime = millis();
        distilledOnFlag = true;
        
        }     
      }

      if (distilledOnFlag == true){
          if (millis() - distilledOnTime >= waterpumpDuration ) {
          Serial.println("Distilled Water Pump OFF");
          digitalWrite(distilledWaterPumpPin, HIGH);
          distilledOnFlag = false;
          prevecCheckTime = millis();
          ecPumpFlag = true;
        }
      }
      if (EC > 1020 && EC < 1200){
      EC = 1030;
      EC = (EC * 1000) / (1000+noise); 
    }
    }


delay(1000);
}
