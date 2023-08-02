/* sunrobotronics technologies 
 *  if any help then contact me - sunrobotronics@gmail.com
 */
#include <LiquidCrystal.h>
 LiquidCrystal lcd(8, 9, 10, 11,12,13);//RS,EN,D4,D5,D6,D7 
const int analogInPin = A0; 
int sensorValue = 0; 
unsigned long int avgValue; 
float b;
int buf[10],temp=0;

void setup() 
{
 Serial.begin(9600);

lcd.begin(16, 2);
lcd.setCursor(0,0);
lcd.print("Measure Ph ");
lcd.setCursor(0,1);    
lcd.print("Value ....... ");
delay(2000);
lcd.clear();
lcd.setCursor(0,0);
lcd.print("SUBSCRIBE MY   ");
lcd.setCursor(0,1);    
lcd.print("YOUTUBE CHANNEL");
delay(2000);
lcd.clear();
lcd.setCursor(0,0);
lcd.print(" SUNROBOTRONICS  ");
lcd.setCursor(0,1);    
lcd.print("  TECHNOLOGIES   ");
delay(2000);  
lcd.clear();
}
 
void loop() 
{
 for(int i=0;i<10;i++) 
 { 
  buf[i]=analogRead(analogInPin);
  delay(10);
 }
 for(int i=0;i<9;i++)
 {
  for(int j=i+1;j<10;j++)
  {
   if(buf[i]>buf[j])
   {
    temp=buf[i];
    buf[i]=buf[j];
    buf[j]=temp;
   }
  }
 }
 avgValue=0;
 for(int i=2;i<8;i++)
 avgValue+=buf[i];
 
 float pHVol=(float)avgValue*5.0/1024/4.3;
 float phValue = -5.70 * pHVol + 22.8;
 phValue=14.2-phValue;
 //float phValue = -3.0 * pHVol+17.5;
 Serial.print("sensor = ");
 Serial.println(phValue);
 lcd.clear();
 lcd.setCursor(0,0);  
 lcd.print("pH Value");
 lcd.setCursor(3,1);  
 lcd.print(phValue);
 delay(900);
}
