// Define pin numbers for pumps and relays
const int phUpPumpPin = 22;
const int phDownPumpPin = 23;
const int ecAUpPumpPin = 24;
const int ecBUpPumpPin = 25;
const int distilledWaterPumpPin = 26;
const int waterTemperaturePeltierRelayPin = 28;
const int waterTemperaturePump = 29;
const int airTemperaturePeltierRelayPin = 30;
const int airTemperatureFanPin = 31;
int count= 0;
int temperatureCount = 0;

// Define timing constants
const unsigned long pHCheckInterval = 120000;  // 1 minutes
const unsigned long ecCheckInterval = 60000;  // 1 minutes
const unsigned long phUppumpDuration = 8000;// 

const unsigned long phDownpumpDuration = 1150;
const unsigned long ecApumpDuration = 2000;
const unsigned long ecBpumpDuration = 1000;
const unsigned long waterpumpDuration = 20;
const unsigned long peltierDuration = 8000;   // 30 seconds
const unsigned long fanDuration = 20000;       // 20 seconds

// Variables to store previous activation times
unsigned long prevpHCheckTime = 0;
unsigned long prevecCheckTime = 0;
unsigned long prevWaterTempActivationTime = 0;
unsigned long prevAirTempActivationTime = 0;
unsigned long ecOnTime = 0;
unsigned long phUpOnTime = 0;
unsigned long phDownOnTime = 0;
unsigned long distilledOnTime = 0;
unsigned long countTime = 0;
unsigned long temperatureCountTime = 0;


// Variables for sensor readings
float EC ;
float EC1 ;
float pH ;
float airTemperature ;
float waterTemperature ;
float waterTemperature1 ;
float waterLevel ;
float humidity ;
float waterLevel1;

// Flag variables for pump activation
bool phPumpFlag = false;
bool ecPumpFlag = false;
bool waterTemperatureFlag = false;
bool ecOnFlag = false;
bool distilledOnFlag = false;
bool ecBOnFlag = false;
bool phUpOnFlag = false;
bool phDownOnFlag = false;



void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(100);
  // Initialize pump and relay pins as OUTPUT
  pinMode(phUpPumpPin, OUTPUT);
  pinMode(phDownPumpPin, OUTPUT);
  pinMode(ecAUpPumpPin, OUTPUT);
  pinMode(ecBUpPumpPin, OUTPUT);
  randomSeed(analogRead(A0));
  pinMode(distilledWaterPumpPin, OUTPUT);
  pinMode(waterTemperaturePeltierRelayPin, OUTPUT);
  pinMode(waterTemperaturePump, OUTPUT);
  pinMode(airTemperaturePeltierRelayPin, OUTPUT);
  pinMode(airTemperatureFanPin, OUTPUT);
  temperatureCountTime = millis();

  digitalWrite(phUpPumpPin, HIGH);
  digitalWrite(phDownPumpPin, HIGH);
  digitalWrite(ecAUpPumpPin, HIGH);
  digitalWrite(ecBUpPumpPin, HIGH);
  float noise = random(0, 2001) / 1000.0;
  EC = (25000)/ (100+noise);
  digitalWrite(distilledWaterPumpPin, HIGH);
  digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
  digitalWrite(waterTemperaturePump, HIGH);
  digitalWrite(airTemperaturePeltierRelayPin, HIGH);
  digitalWrite(airTemperatureFanPin, HIGH);
  delay(3000);
}

void loop() {

//Reading Sensor Values
  if (Serial1.available() >= sizeof(float) * 6) {
    // Create a byte array to hold the received data
    byte data[sizeof(float) * 6];

    // Read the byte array from the serial input
    Serial1.readBytes(data, sizeof(float) * 6);

    // Copy the bytes back to the float variables
    memcpy(&EC1, data, sizeof(float));
    memcpy(&pH, data + sizeof(float), sizeof(float));
    memcpy(&humidity, data + (sizeof(float) * 2), sizeof(float));
    memcpy(&airTemperature, data + (sizeof(float) * 3), sizeof(float));
    memcpy(&waterTemperature1, data + (sizeof(float) * 4), sizeof(float));
    memcpy(&waterLevel1, data + (sizeof(float) * 5), sizeof(float));
  }

  // if (pH < 2 || pH > 14){
  //   pH =8;
  // }
  // if (waterTemperature < 0 || pH > 100){
  //   waterTemperature =29.5;
  // }

// waterLevel = waterLevel1 + 2;

// if (temperatureCount == 0){
//   waterTemperature = waterTemperature1;
// }

// if (millis() - temperatureCountTime > 120000){
//   waterTemperature = waterTemperature1 - ( temperatureCount * 0.06);
//   temperatureCountTime = millis();
//   temperatureCount += 1;
// }

    // Serial.print("EC: ");
    // Serial.print(EC);
    // Serial.println("  micro-siemens/cm");
    // Serial.print("pH: ");
    // Serial.println(pH);
    // Serial.print(F("Humidity: "));
    // Serial.print(humidity);
    // Serial.println("%");
    Serial.print("Water Temperature: ");
    Serial.print(waterTemperature1);
    Serial.println("°C");
    // Serial.print("Water Level ");
    // Serial.print(waterLevel);
    // Serial.println(" cm");
    Serial.print(F("Air Temperature: "));
    Serial.print(airTemperature);
    // Serial.println(F("°C "));
    Serial.println();
    Serial.println();
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
//      if (phDownOnFlag == false){
//        Serial.println("!!! ph Down pump ON !!!!");
//        digitalWrite(phDownPumpPin, LOW);
//        phDownOnTime = millis();
//        phDownOnFlag = true;  
//        }
//      }
//
//    if (phDownOnFlag == true){
//      if (millis() - phDownOnTime >= phDownpumpDuration) {
//        Serial.println("!!!! pH Down Pump OFF !!!!");
//        digitalWrite(phDownPumpPin, HIGH);
//        prevpHCheckTime = millis();
//        phPumpFlag = true;
//        }
//    }
//    // Check if pH is too low
//    if (pH < 5.5) {
//        if (phUpOnFlag == false){
//        Serial.println("!!!!! ph Up pump ON !!!!! ");
//        digitalWrite(phUpPumpPin, LOW);
//        phUpOnTime = millis();
//        phUpOnFlag = true;  
//        }
//      }
//
//    if (phUpOnFlag == true){
//      if (millis() - phUpOnTime >= phUppumpDuration) {
//        Serial.println("!!!!! pH Up Pump OFF!!!!! ");
//        digitalWrite(phUpPumpPin, HIGH);
//        prevpHCheckTime = millis();
//        phPumpFlag = true;
//        }
//      }
//    }

//
//Check EC

  // float noise = random(0, 2001) / 1000.0;
  
  // if (count == 0){
  //   EC = (25000)/ (100+noise);
  // }

  
//  Serial.print("EC: ");
//  Serial.print(EC);
//  Serial.println("  micro-siemens/cm");
//  Serial.println();
//  Serial.println();
  
//   if (ecPumpFlag == true){
    
//     if (millis() - prevecCheckTime <= 50000UL){
//       if (millis()- countTime >= 2000UL){
//         if (count == 1){
//           EC = EC + (520 - 250 + noise)/15 ; 
//           countTime = millis();
//         } 
        
//         if (count == 2){
//           EC = EC + (770 - 520 + noise)/10 ; 
//           countTime = millis();
//         }
//         if (count == 3){
//           EC = EC + (1030 - 770 + noise)/10 ; 
//           countTime = millis();
//         }
//       }
//       EC = (EC * 100) / (100+noise);
//     }

//     if (millis() - prevecCheckTime > 50000UL){
//       if (count == 1){
//         EC =520;
//         EC = (EC * 1000) / (1000+noise);
//       }
//       if (count == 2){
//         EC = 770;
//         EC = (EC * 1000) / (1000+noise);
//       }
//        if (count == 3){
//         EC =1030;
//         EC = (EC * 1000) / (1000+noise);
//       }
//     }
    
//     if (millis() - prevecCheckTime >= ecCheckInterval) {
//       ecPumpFlag = false;
//     }
    
//   }
    
//   if (ecPumpFlag == false){
//   // Check if EC is too high
//     if (EC < 1000) {
//       if (ecOnFlag == false){
//         Serial.println("!!!! EC A pump ON !!!!");
//         Serial.println("!!!! EC B pump ON !!!!");
//         digitalWrite(ecAUpPumpPin, LOW);
//         digitalWrite(ecBUpPumpPin, LOW);
//         ecOnTime = millis();
//         ecOnFlag = true;
//         ecBOnFlag = true;
//         }
//       }

      
//       if (ecOnFlag == true){
//         if (count == 1){
//           EC = 520;
//           EC = (EC * 1000) / (1000+noise);
//         }
//         if (count == 2){
//           EC = 770;
//           EC = (EC * 1000) / (1000+noise);
//         }
//         if (count == 3){
//           EC = 1030;
//           EC = (EC * 1000) / (1000+noise);
//         }
//         if (millis() - ecOnTime >= ecApumpDuration ) {
//           Serial.println("!!!! EC A pump OFF !!!!");
//           digitalWrite(ecAUpPumpPin, HIGH);
//           count = count + 1;
//           countTime = millis();
//           ecOnFlag = false;
//           prevecCheckTime = millis();
//           ecPumpFlag = true;
//         }
//         if (millis() - ecOnTime >= ecBpumpDuration && ecBOnFlag ==true ) {
//         Serial.println("EC B pump OFF");
//         digitalWrite(ecBUpPumpPin, HIGH);
//         ecBOnFlag = false;
//         }
        
//       }
//     // Check if pH is too low
//     if (EC > 1200) {
//       if (distilledOnFlag == false){
//         Serial.println("!!!! Distilled Water Pump ON !!!!");
//         digitalWrite(distilledWaterPumpPin, LOW);
//         distilledOnTime = millis();
//         distilledOnFlag = true;
        
//         }     
//       }

//       if (distilledOnFlag == true){
//           if (millis() - distilledOnTime >= waterpumpDuration ) {
//           Serial.println("!!!! Distilled Water Pump OFF !!!!");
//           digitalWrite(distilledWaterPumpPin, HIGH);
//           distilledOnFlag = false;
//           prevecCheckTime = millis();
//           ecPumpFlag = true;
//         }
//       }
//       if (EC > 1020 && EC < 1200){
//       EC = 1030;
//       EC = (EC * 1000) / (1000+noise); 
//     }
//     }



// //Controlling pH
//   if (phPumpFlag == true){
//     if (millis() - prevpHCheckTime >= pHCheckInterval) {
//       phPumpFlag = false;
//     }
//   }

//   if (phPumpFlag == false && ecOnFlag == false){
//   // Check if pH is too high
//     if (pH > 6.5) {
//       if (phDownOnFlag == false){
//         Serial.println("!!!! ph Down pump ON !!!!");
//         digitalWrite(phDownPumpPin, LOW);
//         phDownOnTime = millis();
//         phDownOnFlag = true;  
//         }
//       }

//     if (phDownOnFlag == true){
//       if (millis() - phDownOnTime >= phDownpumpDuration) {
//         Serial.println("!!!! pH Down Pump OFF !!!!");
//         digitalWrite(phDownPumpPin, HIGH);
//         prevpHCheckTime = millis();
//         phPumpFlag = true;
//         phDownOnFlag = false;
//         }
//     }
//     // Check if pH is too low
//     if (pH < 5.5) {
//         if (phUpOnFlag == false){
//         Serial.println("!!!! ph Up pump ON !!!!");
//         digitalWrite(phUpPumpPin, LOW);
//         phUpOnTime = millis();
//         phUpOnFlag = true;  
//         }
//       }

//     if (phUpOnFlag == true){
//       if (millis() - phUpOnTime >= phUppumpDuration) {
//         Serial.println("!!!! pH Up Pump OFF !!!!");
//         digitalWrite(phUpPumpPin, HIGH);
//         prevpHCheckTime = millis();
//         phPumpFlag = true;
//         }
//       }
//     }



//
//
////Water Temperature

  // if (waterTemperature > 22.0){
  //   digitalWrite(waterTemperaturePeltierRelayPin, LOW);
  //   digitalWrite(waterTemperaturePump, LOW);
  // }
  
  // if (waterTemperature < 18.0){
  //   digitalWrite(waterTemperaturePump, HIGH);
  //   digitalWrite(waterTemperaturePeltierRelayPin, HIGH);
  // }
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
