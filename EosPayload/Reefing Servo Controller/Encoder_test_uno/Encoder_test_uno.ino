

const int enc_A = 7;
const int enc_B = 6;

volatile long count = 0;
volatile byte lastState = 0;

long nextTime = millis() + 200;

void setup() {
  // put your setup code here, to run once:
  cli();

  //set up interrupts:
  PCICR = 0b00000100; //enables pin change interrupts on port D
  PCMSK2 = 0b11000000; //enable pin change interrupts on arduino pins D7, D6

  //Start serial monitor
  Serial.begin(115200);
  
  sei();
}

void loop() {
  // put your main code here, to run repeatedly:

  //Print out encoder count every 200 ms
  if(millis() > nextTime) {
    Serial.println(count);
    nextTime = millis() + 200;
  }
  
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
