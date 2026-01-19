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
    return l * MATRIX + c;
  } else {
    return l * MATRIX + (MATRIX - 1 - c);
  }
}

// =====================
// SERIAL BUFFER
// =====================

char cmd[16];
uint8_t cmdIdx = 0;

// =====================
// SETUP
// =====================

void setup() {
  strip.begin();
  strip.clear();
  strip.show();

  Serial.begin(115200);
  Serial.println("READY");
}

// =====================
// PROCESSAMENTO
// =====================

void processarComando(char *cmd) {
  int len = strlen(cmd);

  // LIMPAR MATRIZ
  if (strcmp(cmd, "CL") == 0) {
    strip.clear();
    strip.show();
    Serial.println("CLEAR");
    return;
  }

  // DESLIGAR LED (LC)
  if (len == 2 && isDigit(cmd[0]) && isDigit(cmd[1])) {
    int l = cmd[0] - '0';
    int c = cmd[1] - '0';

    if (l >= MATRIX || c >= MATRIX) {
      Serial.println("POS_INVALID");
      return;
    }

    strip.setPixelColor(mapXY(l, c), 0);
    strip.show();
    Serial.println("OFF_OK");
    return;
  }

  // LIGAR LED (LCRRRGGGBBB[I])
  if (len == 11 || len == 12) {
    int l = cmd[0] - '0';
    int c = cmd[1] - '0';

    int r = (cmd[2] - '0') * 100 + (cmd[3] - '0') * 10 + (cmd[4] - '0');
    int g = (cmd[5] - '0') * 100 + (cmd[6] - '0') * 10 + (cmd[7] - '0');
    int b = (cmd[8] - '0') * 100 + (cmd[9] - '0') * 10 + (cmd[10] - '0');

    int intensidade = 9;
    if (len == 12 && isDigit(cmd[11])) {
      intensidade = constrain(cmd[11] - '0', 1, 9);
    }

    if (l >= MATRIX || c >= MATRIX) {
      Serial.println("POS_INVALID");
      return;
    }

    r = aplicarIntensidade(constrain(r, 0, 255), intensidade);
    g = aplicarIntensidade(constrain(g, 0, 255), intensidade);
    b = aplicarIntensidade(constrain(b, 0, 255), intensidade);

    strip.setPixelColor(mapXY(l, c), strip.Color(r, g, b));
    strip.show();
    Serial.println("ON_OK");
    return;
  }

  Serial.println("CMD_INVALID");
}

// =====================
// LOOP PRINCIPAL
// =====================

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();

    if (ch == '\n') {
      cmd[cmdIdx] = '\0';
      processarComando(cmd);
      cmdIdx = 0;
    } else if (cmdIdx < sizeof(cmd) - 1) {
      cmd[cmdIdx++] = ch;
    }
  }
}
