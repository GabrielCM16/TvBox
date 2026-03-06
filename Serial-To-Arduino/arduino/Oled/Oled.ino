#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define LARGURA 128 
#define ALTURA 64 

// Configuração do Display
Adafruit_SSD1306 display(LARGURA, ALTURA, &Wire, -1);

// Variáveis do seu Jogo (Simulação)
int level = 5;
int vidas = 3;
long recorde = 15450;

void setup() {
  // Inicializa o display no endereço 0x3C
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    for(;;); 
  }

  desenharInterface();
}

void loop() {
  // O loop fica vazio ou você pode atualizar os dados aqui futuramente
}

void desenharInterface() {
  display.clearDisplay();
  display.setTextColor(WHITE);

  // --- CABEÇALHO: LEVEL ---
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("FASE ATUAL");
  
  display.setTextSize(3); // Level bem grande no centro
  display.setCursor(45, 15);
  display.print(level);

  // --- LINHA DIVISÓRIA ---
  display.drawFastHLine(0, 42, 128, WHITE);

  // --- RODAPÉ: VIDAS ---
  display.setTextSize(1);
  display.setCursor(0, 50);
  display.print("VIDAS:");
  
  // Desenha corações ou barras para as vidas
  for(int i = 0; i < vidas; i++) {
    display.fillRect(40 + (i * 10), 50, 7, 7, WHITE); // Quadrinhos representando vidas
  }

  // --- RODAPÉ: RECORDE ---
  display.setCursor(80, 45);
  display.print("HI-SCORE");
  display.setCursor(80, 55);
  display.print(recorde);

  display.display();
}