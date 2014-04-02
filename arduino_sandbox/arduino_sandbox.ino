//#include <SoftwareSerial.h>

// config output pins (digital)
byte output_pins[2] = {12, 13};
//byte output_pins[2] = {12, 13};
// config input pins (digital)
byte input_pins[3] = {2, 3, 4};
bool current_values[sizeof(input_pins)];
long last_input_change[sizeof(input_pins)];
long bounce_time = 100;
String local_buffer;

byte pulse_mode = 1; // specify whether arduino should worry about pulse  0==off; 1==on if trigger is active; 2==on regardless of trigger
bool pulse_on = 0;     // specifies whether pulse is running at any time
byte pulse_trigger_pin = 10;  //
byte pulse_output_pin = 11;   // pulse output pin
long pulse_period = 100;      // pulse period in ms (1000/f)
long pulse_width = 50;        // pulse width in ms


// configure software serial ports
//SoftwareSerial mySerial(10, 11); // RX, TX


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  //
  local_buffer.reserve(200);
  // configure input pins
  for (byte i = 0; i < sizeof(input_pins); i++) {
    pinMode(input_pins[i], INPUT_PULLUP);
    current_values[i] = digitalRead(input_pins[i]);
  }
  for (int i = 0; i < sizeof(output_pins); i++) {
    pinMode(output_pins[i], OUTPUT);
    digitalWrite(output_pins[i], 0);
  }
  pinMode(pulse_output_pin, OUTPUT);
  digitalWrite(pulse_output_pin, 0);
  pinMode(pulse_trigger_pin, INPUT_PULLUP);
}

//
void checkInputs() {
  bool val;
  for (byte i = 0; i < sizeof(input_pins); i++) {
    val = digitalRead(input_pins[i]);
    if (val != current_values[i] && millis() - last_input_change[i] > bounce_time) {
      Serial.print('<');
      Serial.print(millis());
      Serial.print('-');
      Serial.print(input_pins[i]);
      Serial.print('-');
      Serial.print(val);
      Serial.println('>');
      current_values[i] = val;
      last_input_change[i] = millis();
    }
  }
}

void checkSerial() {
  if (Serial.available() > 0) {
    char character;
    while (Serial.available() > 0) {
      character = Serial.read();
      local_buffer.concat(character);
    }
  }
}

void checkBuffer() {
  long idx1 = local_buffer.indexOf('<');
  long idx2 = local_buffer.indexOf('>');
  if (idx1 >= 0 && idx2 > 0) {
    String chunk = local_buffer.substring(idx1, idx2 + 1);
    local_buffer = local_buffer.substring(idx2 + 1);
    evalChunk(chunk);
  }
  else if (idx1 >= 0) {
    local_buffer = local_buffer.substring(idx1);
  }
  else {
    local_buffer = "";
  }
}

void evalChunk(String chunk) {
  int eq_idx = chunk.indexOf('=');
  if (chunk.startsWith("<") && chunk.endsWith(">"))
  {
    if (eq_idx > 0) {
      if (chunk.substring(1, 2).equalsIgnoreCase("o")) {
        // if chunk indicades change to an output
        byte port = byte(chunk.substring(2, eq_idx).toInt());
        byte val = byte(chunk.substring(eq_idx + 1).toInt());
        //        Serial.print(millis());
        //        Serial.print( "Port ");
        //        Serial.print(port);
        //        Serial.print(" set to ");
        //        Serial.println(val);
        digitalWrite(port, val);
      }
      else if (chunk.substring(1, 2).equalsIgnoreCase("p")) {
        // if chunk indicades change to an output
        byte val = byte(chunk.substring(eq_idx + 1).toInt());
        pulse_mode = val;
      }
      else if (chunk.substring(1, 2).equalsIgnoreCase("w")) {
        // if chunk indicades change to an output
        pulse_width = long(chunk.substring(eq_idx + 1).toInt());
      }
      else if (chunk.substring(1, 2).equalsIgnoreCase("l")) {
        // if chunk indicades change to an output
        pulse_period = long(chunk.substring(eq_idx + 1).toInt());

      }
    }
    else if (chunk.equals("<sync>")) {
      Serial.print("<");
      Serial.print(millis());
      Serial.println("-sync>");
    }
  }
}

//long lastmillis = 0;
void loop() {
  // put your main code here, to run repeatedly:
  checkInputs();
  checkSerial();
  checkBuffer();
  checkPulse();
//   if (millis() >= lastmillis + 1000) {
//   Serial.println(millis());
//   lastmillis = millis();}

}



// do pulse related opperations
bool checkPulse() {
  if (pulse_mode == 1) {
    check_pulse_input();
  }
  else if (pulse_mode == 2) {
    if (pulse_on) {
      run_pulse();
    }
    else {
        start_pulse();
        run_pulse();
      }
  }
  else if (pulse_mode == 0) {
    if (pulse_on) {
      stop_pulse();
    }
  }
}

// run flicker
bool pulse_trigger_value = 0;
void check_pulse_input() {
  pulse_trigger_value = digitalRead(pulse_trigger_pin);
  if (pulse_on) {
    if (pulse_trigger_value == 0) {
      stop_pulse();
    }
    else {
      run_pulse();
    }
  }
  else {
    if (pulse_trigger_value == 1) {
      start_pulse();
    }
  }
}

bool pulseout_state = 0;
long last_up = 0;
void start_pulse() {
  pulse_on = 1;
  last_up = micros();
  digitalWrite(pulse_output_pin, 1);
  pulseout_state = 1;
}
void stop_pulse() {
  pulse_on = 0;
  digitalWrite(pulse_output_pin, 0);
  pulseout_state = 0;
}
void run_pulse() {
  long current_time = micros();
  if (pulseout_state == 1) {
    if (current_time >= last_up + pulse_width*1000) {
      digitalWrite(pulse_output_pin, 0);
      pulseout_state = 0;
    }
  }
  else {
    if (current_time >= last_up + pulse_period*1000) {
      digitalWrite(pulse_output_pin, 1);
      pulseout_state = 1;
      //last_up = last_up + pulse_period;
      last_up = current_time;
    }
  }
}

