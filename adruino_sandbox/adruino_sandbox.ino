//#include <SoftwareSerial.h>

// config output pins (digital)
byte output_pins[2] = {12, 13};
// config input pins (digital)
byte input_pins[3] = {2, 3, 4};
bool current_values[sizeof(input_pins)];
long last_input_change[sizeof(input_pins)];
long bounce_time = 100;
String local_buffer;

// configure software serial ports
//SoftwareSerial mySerial(10, 11); // RX, TX


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //
  local_buffer.reserve(200);
  // configure input pins
  for (byte i = 0; i < sizeof(input_pins); i++) {
    pinMode(input_pins[i], INPUT_PULLUP);
    current_values[i] = digitalRead(input_pins[i]);
  }
  for (int i = 0; i < sizeof(output_pins); i++) {
    pinMode(output_pins[i], OUTPUT);
  }
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
        Serial.print(millis());
        Serial.print( "Port ");
        Serial.print(port);
        Serial.print(" set to ");
        Serial.println(val);
        digitalWrite(port, val);
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
  //  if (millis() >= lastmillis + 1000) {
  //    Serial.println(millis());
  //  lastmillis = millis();}
}


