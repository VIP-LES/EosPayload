#include <avr/interrupt.h>

#define PPR 1024 
#define MAX_POSITION 4139
#define MID_POSITION 2070
#define DEADBAND 10

volatile long count = 0;
long target = 0;
volatile byte lastState = 0;

void setup() {
  // put your setup code here, to run once:
  cli();
  pinMode(1, INPUT);
  pinMode(2, INPUT);
  pinMode(0, OUTPUT);
  pinMode(4, INPUT);

  pinMode(A3, OUTPUT);
  digitalWrite(A3, LOW); //Just an extra ground pin for the RC filter lol

  GIMSK = 0b00100000;  //Enable pin change interrupts
  PCMSK = 0b00000110;  //Enable pin change interrupts on PCINT1 and PCINT2
  sei();
}

void loop() {
  // put your main code here, to run repeatedly:

  //map analog input value onto range for target
  int analogTarget = analogRead(2);
  if(analogTarget < (1024/20)) {
    target = 0;
  } else {
    target = map(analogTarget, 0, 1024, MID_POSITION, MAX_POSITION);
  }

  //Determine servo output pulse length: 1.5 center, 1.0 most negative, 2.0 most positive (milliseconds)
  long error = target - count;

  int pulseLength = 1500; //microseconds
  
  if(error > PPR) {
    pulseLength = 2000;
  } else if(error > 0) {
    pulseLength = 1500 + (error / 4);
  } else if(error < -PPR) {
    pulseLength = 1000;
  } else if(error < 0) {
    pulseLength = 1500 + (error / 4);
  }

  if(analogTarget > 512) {
    pulseLength = 2000;
  } else {
    pulseLength = 1000;
  }

  //Output pulse
  long startTime = micros();
  
  while(micros() < startTime + pulseLength) { //The pulse here is low instead of high bc the output mosfet inverts this signal
    digitalWrite(0, LOW);
  }
  while(micros() < startTime + 20000) { //the entire servo pulse period should be 20 ms
    digitalWrite(0, HIGH);
  }
  
}

ISR(PCINT0_vect)  {
  //PCINT1 corresponds to pin PB1 and encoder output A
  //PCINT2 corresponds to pin PB2 and encoder output B
  byte state = (digitalRead(1) << 1) + digitalRead(2);

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
