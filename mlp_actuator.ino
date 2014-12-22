/*****************************************************************************
 * Arduino Network Gauge                                                     *
 *                                                                           *
 * Simple Arduino program to drive an automotive actuator ganked from an     *	
 * HVAC system to be used as an internet utilization gauge.                  *
 *                                                                           *
 * By Jonathan "JonnyFunFun" Enzinna <www.jonathanenzinna.com>               *
 * This is free and unencumbered software released into the public domain.   *
 * For more information, please refer to the LIENSE file                     *
 *                                                                           *
 * For more information on the Arduino Network Gauge project, please visit:  *
 * <url_coming_soon>                                                         *
 *****************************************************************************/

const int FEEDBACK_PIN = A0;     // analog input pin from actuator's feedback
const int PWM_OUTPUT = 11;       // PWM output pin to actuator
// coefficient to convert analog scale of 0 - 10 (== 100/1023)
const float ANALOG_SCALE_COEF = 0.09775171065493646;  

String inputStr = "";  // string to hold serial input
int target = 0;        // current target for the actuator

void setup() {
  // setup PWM as output
  pinMode(PWM_OUTPUT, OUTPUT);
  analogWrite(PWM_OUTPUT, 255);

  // analog as input
  pinMode(FEEDBACK_PIN, INPUT);

  // Start serial I/O
  Serial.begin(9600);

  while (!Serial) {
    ; // wait for serial to connect
  }

  Serial.println("RDY\n#");
}

void actuatorControl() {
  int current = getPosition();
  if (current == target) {
    analogWrite(PWM_OUTPUT, 128);
  } else if (current > target) {
    analogWrite(PWM_OUTPUT, 255);
  } else if (current < target) {
    analogWrite(PWM_OUTPUT, 0);
  }
}

int getPosition() {
  int raw = analogRead(FEEDBACK_PIN);
  return (int)(raw * ANALOG_SCALE_COEF);
}

void loop() {
  // Check for new data
  while (Serial.available() > 0)
  {
    int inChar = Serial.read();
    if (isDigit(inChar)) {
      // if a digit, append it to our running str and echo
      inputStr += (char) inChar;
      Serial.write(inChar);
    } else if(inChar == '?') {
      // display current position
      Serial.println(getPosition());
    } else if(inChar == 't') {
      // display current target
      Serial.println(target);
    } else {
      Serial.println("#");
      // set the new target
      int newTarget = inputStr.toInt();
      // @TODO - input validation?
      target = newTarget;
      inputStr = "";
    }
  }
  actuatorControl();
}

