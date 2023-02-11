#include <avr/interrupt.h>

volatile int count = 0;

void setup() {
  // put your setup code here, to run once:
  cli();
  pinMode(4, OUTPUT);
  pinMode(3, INPUT);
  GIMSK = 0b00100000;
  PCMSK = 0b00001000;
  sei();

}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(4,count%2);
}

ISR(PCINT0_vect){
  if(digitalRead(3) == HIGH){
    count++;
  }
}
