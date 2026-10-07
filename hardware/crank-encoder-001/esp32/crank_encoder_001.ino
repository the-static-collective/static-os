// CRANK ENCODER 001 — ESP32 reference emitter
//
// Emits one newline-delimited static-os.crank-physical-edge/v0 JSON frame per
// full quadrature detent. This firmware is a reference adapter, not part of the
// semantic authority layer.
//
// Pins may be changed to fit the actual encoder/wiring.

#include <Arduino.h>
#include <esp_system.h>

static const int PIN_A = 32;
static const int PIN_B = 33;
static const char* DEVICE_ID = "encoder:esp32-reference-001";

uint32_t sessionNonce = 0;
uint64_t sequenceNumber = 0;
int8_t accumulator = 0;
uint8_t lastAB = 0;

// Gray-code transition table. +1 / -1 are quarter steps.
static const int8_t TRANSITIONS[16] = {
   0, -1,  1,  0,
   1,  0,  0, -1,
  -1,  0,  0,  1,
   0,  1, -1,  0
};

void emitDetent(const char* direction) {
  sequenceNumber++;
  Serial.print("{\"schema\":\"static-os.crank-physical-edge/v0\",");
  Serial.print("\"device_id\":\"");
  Serial.print(DEVICE_ID);
  Serial.print("\",\"session_id\":\"esp32-");
  Serial.print(sessionNonce, HEX);
  Serial.print("\",\"sequence\":");
  Serial.print((unsigned long long)sequenceNumber);
  Serial.print(",\"direction\":\"");
  Serial.print(direction);
  Serial.println("\",\"ticks\":1}");
}

void setup() {
  pinMode(PIN_A, INPUT_PULLUP);
  pinMode(PIN_B, INPUT_PULLUP);
  Serial.begin(115200);
  sessionNonce = esp_random();
  lastAB = (digitalRead(PIN_A) << 1) | digitalRead(PIN_B);
}

void loop() {
  uint8_t currentAB = (digitalRead(PIN_A) << 1) | digitalRead(PIN_B);
  if (currentAB == lastAB) {
    delay(1);
    return;
  }

  uint8_t index = (lastAB << 2) | currentAB;
  accumulator += TRANSITIONS[index];
  lastAB = currentAB;

  if (accumulator >= 4) {
    accumulator = 0;
    emitDetent("CW");
  } else if (accumulator <= -4) {
    accumulator = 0;
    emitDetent("CCW");
  }
}
