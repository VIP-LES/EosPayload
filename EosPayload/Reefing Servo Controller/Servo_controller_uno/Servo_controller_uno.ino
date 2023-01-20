#include <Servo.h>

#define enc_A 7
#define enc_B 6
#define ctrl_in A0
#define servo_ctrl 9

#define PPR 1024 
#define MAX_POSITION 4139
#define MID_POSITION 2070
#define DEADBAND 20

#define KP 3
#define KI 0.01

volatile long count = 0;
volatile byte lastState = 0;

long nextLogTime = millis() + 200;
long lastCtrlTime = millis();

int integralError = 0;

Servo contServo;

void setup() {
  // put your setup code here, to run once:
  cli();

  //set up interrupts:
  PCICR = 0b00000100; //enables pin change interrupts on port D
  PCMSK2 = 0b11000000; //enable pin change interrupts on arduino pins D7, D6

  //Pin setup
  pinMode(enc_A, INPUT);
  pinMode(enc_B, INPUT);
  pinMode(ctrl_in, INPUT);

  pinMode(A3, OUTPUT);
  digitalWrite(A3, LOW);//Just an extra ground point for the RC filter

  //Servo setup
  contServo.attach(servo_ctrl,800,2200);

  //Start serial monitor
  Serial.begin(115200);
  
  sei();
}

void loop() {
  // put your main code here, to run repeatedly:
  
  //Print out encoder count every 200 ms
  if(millis() > nextLogTime) {
    Serial.println(count);
    nextLogTime = millis() + 200;
  }

  //map analog input onto range for target
  int analogTarget = analogRead(ctrl_in);
  long target = 0;
  if(analogTarget < (1024/20)) {
    target = 0;
  } else {
    target = map(analogTarget, 0, 1024, MID_POSITION, MAX_POSITION); //This is pin PB4, which is ADC2
  }

  //Determine servo output pulse length: 1.5 center, 1.0 most negative, 2.0 most positive (milliseconds)
  long error = target - count;

  int pulseLength = 1500; //microseconds
  
//Janky semi-proportional control, works pretty well surprisingly  
  if(error > PPR) {
    pulseLength = 2000;
  } else if(error > 0) {
    pulseLength = 1500 + (KP * error / 4);
  } else if(error < -PPR) {
    pulseLength = 1000;
  } else if(error < 0) {
    pulseLength = 1500 + (KP * error / 4);
  }

//Trying some integral control - didn't work well.  I think the sample rate is too slow to get good integral estimation
//  integralError += KI*error*(millis() - lastCtrlTime);
//  lastCtrlTime = millis();
//  int integralPulse = map(integralError,-1000, 1000, 100, -100);
//  integralPulse = constrain(integralPulse,-100,100);
//
//  pulseLength += integralPulse;

//Bang-bang control attempt.  Doesn't really work.
//  if(error > PPR) {
//    pulseLength = 2000;
//  } else if(error > 100) {
//    pulseLength = 1800;
//  } else if(error > DEADBAND) {
//    pulseLength = 1550;
//  } else if(error < -PPR) {
//    pulseLength = 1000;
//  } else if(error < -100) {
//    pulseLength = 1200;
//  } else if(error < -DEADBAND) {
//    pulseLength = 1450;
//  }

  //write this value to the servo
  contServo.writeMicroseconds(pulseLength);
  
}

ISR(PCINT2_vect) {
  byte state = (digitalRead(enc_A) << 1) + digitalRead(enc_B);

  if(lastState == 0b00) {
    if(state == 0b10) {
      count += 1;
    } else if(state == 0b01) {
      count -= 1;
    }
  }

  else if(lastState == 0b10) {
    if(state == 0b11) {
      count += 1;
    } else if(state == 0b00) {
      count -= 1;
    }
  }

  else if(lastState == 0b11) {
    if(state == 0b01) {
      count += 1;
    } else if(state == 0b10) {
      count -= 1;
    }
  }

  else if(lastState == 0b01) {
    if(state == 0b00) {
      count += 1;
    } else if(state == 0b11) {
      count -= 1;
    }
  }

  lastState = state;
}
