  #include <Wire.h>
//#include <SimpleTimer.h>
//
//SimpleTimer timer;

float calibration_value = -3.4259;
int phval = 0; 
unsigned long int avgval; 
int buffer_arr[30],temp;

float ph_act;

void setup() 
{
  Wire.begin();
  Serial.begin(9600);
  pinMode(A3, INPUT);

}
void loop() {
 for(int i=0;i<30;i++) 
 { 
 buffer_arr[i]=analogRead(A3);
 delay(30);
 }
 
 for(int i=0;i<29;i++)
 {
  for(int j=i+1;j<30;j++)
   {
      if(buffer_arr[i]>buffer_arr[j])
    {
 temp=buffer_arr[i];
 buffer_arr[i]=buffer_arr[j];
 buffer_arr[j]=temp;
    }
    }
 }
 
 avgval=0;
 
 for(int i=10;i<20;i++)
 avgval+=buffer_arr[i];
 float volt=(float)avgval*5.0/1024/10; 
 ph_act = 5.4644 * volt + calibration_value;

 Serial.print("Voltage: ");
 Serial.println(volt);
 Serial.print("pH Val: ");
 Serial.println(ph_act);

 
 delay(1000);
}
