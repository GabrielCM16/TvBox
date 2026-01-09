#include <Adafruit_NeoPixel.h>

#define PIN A5
#define NUM_PIXELS 64
#define MATRIX 8

Adafruit_NeoPixel strip(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);

// =====================
// UTILITÁRIOS
// =====================

uint8_t aplicarIntensidade(uint8_t v, int i) {
  return (v * i) / 9;
}

// Mapeamento XY -> índice físico (serpentino)
int mapXY(int l, int c) {
  if (l % 2 == 0) {
    // linha par: esquerda -> direita
    return l * MATRIX + c;
  } else {
    // linha ímpar: direita -> esquerda
    return l * MATRIX + (MATRIX - 1 - c);
  }
}

// =====================
// SETUP
// =====================

void setup() {
  strip.begin();
  strip.clear();
  strip.show();

  Serial.begin(9600);
  Serial.println("READY");
}

// =====================
// LOOP
// =====================

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  // =====================
  // LIMPEZA TOTAL
  // =====================
  if (cmd == "CL") {
    strip.clear();
    strip.show();
    Serial.println("CLEAR");
    return;
  }

  // =====================
  // DESLIGAR LED (LC)
  // Formato: LC
  // =====================
  if (cmd.length() == 2 && isDigit(cmd[0]) && isDigit(cmd[1])) {
    int l = cmd[0] - '0';
    int c = cmd[1] - '0';

    if (l < 0 || l >= MATRIX || c < 0 || c >= MATRIX) {
      Serial.println("POS_INVALID");
      return;
    }

    int idx = mapXY(l, c);
    strip.setPixelColor(idx, 0);
    strip.show();

    Serial.println("OFF_OK");
    return;
  }

  // =====================
  // LIGAR LED
  // Formatos:
  // LCRRRGGGBBB
  // LCRRRGGGBBBI
  // =====================
  if (cmd.length() == 11 || cmd.length() == 12) {

    int l = cmd.substring(0, 1).toInt();
    int c = cmd.substring(1, 2).toInt();

    int r = cmd.substring(2, 5).toInt();
    int g = cmd.substring(5, 8).toInt();
    int b = cmd.substring(8, 11).toInt();

    int intensidade = 9; // default (máxima)

    if (cmd.length() == 12) {
      intensidade = cmd.charAt(11) - '0';
      intensidade = constrain(intensidade, 1, 9);
    }

    if (l < 0 || l >= MATRIX || c < 0 || c >= MATRIX) {
      Serial.println("POS_INVALID");
      return;
    }

    r = aplicarIntensidade(constrain(r, 0, 255), intensidade);
    g = aplicarIntensidade(constrain(g, 0, 255), intensidade);
    b = aplicarIntensidade(constrain(b, 0, 255), intensidade);

    int idx = mapXY(l, c);
    strip.setPixelColor(idx, strip.Color(r, g, b));
    strip.show();

    Serial.println("ON_OK");
    return;
  }

  // =====================
  // COMANDO INVÁLIDO
  // =====================
  Serial.println("CMD_INVALID");
}
