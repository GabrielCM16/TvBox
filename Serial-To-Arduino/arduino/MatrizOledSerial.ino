#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// =====================
// CONFIGURAÇÕES HARDWARE
// =====================
#define PIN_NEO A3
#define NUM_PIXELS 64
#define MATRIX_SIZE 8

#define LARGURA_OLED 128 
#define ALTURA_OLED 64 

// Objetos
Adafruit_NeoPixel strip(NUM_PIXELS, PIN_NEO, NEO_GRB + NEO_KHZ800);
Adafruit_SSD1306 display(LARGURA_OLED, ALTURA_OLED, &Wire, -1);

// Buffer Serial
char cmd[20];
uint8_t cmdIdx = 0;

// =====================
// UTILITÁRIOS MATRIZ
// =====================
uint8_t aplicarIntensidade(uint8_t v, int i) {
  return (v * i) / 9;
}

int mapXY(int l, int c) {
  if (l % 2 == 0) {
    return l * MATRIX_SIZE + c;
  } else {
    return l * MATRIX_SIZE + (MATRIX_SIZE - 1 - c);
  }
}

// =====================
// LÓGICA DO OLED
// =====================
void atualizarOLED(char *p_cmd) {
  if (strlen(p_cmd) < 9) {
    Serial.println("OLED_DATA_ERR");
    return;
  }

  char lvl[3] = {p_cmd[1], p_cmd[2], '\0'};
  int vidas = p_cmd[3] - '0';
  char rec[6] = {p_cmd[4], p_cmd[5], p_cmd[6], p_cmd[7], p_cmd[8], '\0'};

  display.clearDisplay();
  display.setTextColor(WHITE);

  // --- CABEÇALHO (Com margens) ---
  display.setTextSize(2);
  display.setCursor(4, 5); // Afastado da borda esquerda e do topo
  display.print("LEVEL:");
  
  display.setTextSize(2);
  display.setCursor(75, 5); // Centralizado mais abaixo
  display.print(lvl);

  // Linha divisória (agora um pouco mais abaixo para dar espaço)
  display.drawFastHLine(0, 25, 128, WHITE);

  // Vidas
  display.setTextSize(1);
  display.setCursor(4, 35); // Margem esquerda de 4px
  display.print("VIDAS:");
  for(int i = 0; i < vidas; i++) {
    display.fillRect(55 + (i * 12), 35, 7, 7, WHITE); // Espaçamento maior entre vidas
  }

  // Recorde
  display.setCursor(4, 52); // Margem esquerda de 4px
  display.print("HI-SCORE: ");
  display.print(rec);

  display.display();
  Serial.println("OLED_UPDATED");
}

// =====================
// PROCESSAMENTO SERIAL
// =====================
void processarComando(char *p_cmd) {
  char prefixo = p_cmd[0];

  // --- COMANDO PARA OLED ---
  if (prefixo == 'O') {
    atualizarOLED(p_cmd);
    return;
  }

  // --- COMANDO PARA MATRIZ ---
  if (prefixo == 'M') {
    char *sub = &p_cmd[1]; // Remove o 'M' para usar sua lógica original
    int len = strlen(sub);

    if (strcmp(sub, "CL") == 0) {
      strip.clear();
      strip.show();
      Serial.println("MATRIZ_CLEARED");
      return;
    }

    // LIGAR LED (LCRRRGGGBBB[I]) - Agora sem o 'M' inicial no cálculo
    if (len == 11 || len == 12) {
      int l = sub[0] - '0';
      int c = sub[1] - '0';
      int r = (sub[2]-'0')*100 + (sub[3]-'0')*10 + (sub[4]-'0');
      int g = (sub[5]-'0')*100 + (sub[6]-'0')*10 + (sub[7]-'0');
      int b = (sub[8]-'0')*100 + (sub[9]-'0')*10 + (sub[10]-'0');
      
      int intensidade = 9;
      if (len == 12) intensidade = constrain(sub[11] - '0', 1, 9);

      r = aplicarIntensidade(constrain(r, 0, 255), intensidade);
      g = aplicarIntensidade(constrain(g, 0, 255), intensidade);
      b = aplicarIntensidade(constrain(b, 0, 255), intensidade);

      strip.setPixelColor(mapXY(l, c), strip.Color(r, g, b));
      strip.show();
      Serial.println("MATRIZ_ON_OK");
      return;
    }
  }

  Serial.println("CMD_INVALID");
}

// =====================
// SETUP & LOOP
// =====================
void setup() {
  // 1. Prioridade absoluta: I2C e OLED
  Wire.begin(); 
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    // Se falhar aqui, o problema é puramente elétrico ou de endereço
    for(;;); 
  }
  display.clearDisplay();
  display.display();

  // 2. Só depois, iniciamos a Matriz
  strip.begin();
  strip.clear();
  strip.show();

  // 3. Serial por último
  Serial.begin(115200);
  Serial.println("READY_SYSTEM");
}

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