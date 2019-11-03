#include <LiquidCrystal.h>

LiquidCrystal lcd(8, 9, 4, 5, 6, 7);           // select the pins used on the LCD panel

// define some values used by the panel and buttons
int lcd_key     = 0;
int adc_key_in  = 0;
boolean clear = false;

#define btnUP     1
#define btnDOWN   2
#define btnSELECT 4
#define btnNONE   5

int read_LCD_buttons() {              // read the buttons
  adc_key_in = analogRead(0);       // read the value from the sensor
  int result = 10;
  if (adc_key_in > 100 && adc_key_in < 300)  result =  btnUP;
  if (adc_key_in > 300 && adc_key_in < 450)  result =  btnDOWN;
  if (adc_key_in > 450 && adc_key_in < 850)  result =  btnSELECT;
  if (adc_key_in > 1000 && adc_key_in < 1100) result =  btnNONE;
  //  Serial.print(adc_key_in);
  //  Serial.print(" result=");
  //  Serial.println(result);
  return result;
}

void setup() {
  Serial.begin(9600);

  lcd.begin(16, 2);               // start the library
  lcd.setCursor(0, 0);            // set the LCD cursor   position
  lcd.print("Push the buttons");  // print a simple message on the LCD
}

void loop() {
  String str;

  //read message from Pi
  while (Serial.available() > 0) {
    //lcd.write(Serial.read());

    str = Serial.readStringUntil('\n');
    //Serial.println(str);

    String line1 = getValue(str, ';', 0);
    String line2 = getValue(str, ';', 1);
    //Serial.println(line1);
    lcd.clear();
    //lcd.setCursor(0, 0);
    lcd.print(line1.c_str());
    lcd.setCursor(0, 1);            // set the LCD cursor   position
    lcd.print(line2.c_str());
  }

  lcd_key = read_LCD_buttons();   // read the buttons

  switch (lcd_key) {
    case btnUP: {
        if (clear) {
          Serial.println("UP");
          //Serial.writeln("1");
          clear = false;
        }
        break;
      }
    case btnDOWN: {
        if (clear) {
          Serial.println("DOWN");
          //Serial.writeln("2");
          clear = false;
        }
        break;
      }
    case btnSELECT: {
        if (clear) {
          Serial.println("SELECT");
          //Serial.writeln("3");
          clear = false;
        }
        break;
      }
    case btnNONE: {
        clear = true;
        break;
      }
  }
  //debounce
  delay(70);

}



String getValue(String data, char separator, int index)
{
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i + 1 : i;
    }
  }

  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
