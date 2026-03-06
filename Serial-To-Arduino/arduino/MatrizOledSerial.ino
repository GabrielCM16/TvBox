#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ctype.h>

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

// Buffer serial otimizado
char cmd[16];
uint8_t cmdIdx = 0;

// =====================
// UTILITÁRIOS MATRIZ
// =====================
uint8_t aplicarIntensidade(uint8_t v, uint8_t i) {
  return (v * i) / 9;
}

uint8_t mapXY(uint8_t l, uint8_t c) {
  if (l % 2 == 0) {
    return l * MATRIX_SIZE + c;
  } else {
    return l * MATRIX_SIZE + (MATRIX_SIZE - 1 - c);
  }
}

// =====================
// OLED
// =====================
void atualizarOLED(char *p_cmd) {

  if (strlen(p_cmd) < 9) {
    Serial.println(F("OLED_DATA_ERR"));
    return;
  }

  uint8_t vidas = p_cmd[3] - '0';

  display.clearDisplay();
  display.setTextColor(WHITE);

  display.setTextSize(2);
  display.setCursor(4,5);
  display.print(F("LEVEL:"));

  display.setCursor(75,5);
  display.print(p_cmd[1]);
  display.print(p_cmd[2]);

  display.drawFastHLine(0,25,128,WHITE);

  display.setTextSize(1);
  display.setCursor(4,35);
  display.print(F("VIDAS:"));

  for(uint8_t i=0;i<vidas;i++){
    display.fillRect(55+(i*12),35,7,7,WHITE);
  }

  display.setCursor(4,52);
  display.print(F("HI-SCORE: "));
  display.print(&p_cmd[4]);

  display.display();

  Serial.println(F("OLED_UPDATED"));
}

// =====================
// SERIAL COMMAND
// =====================
void processarComando(char *p_cmd) {

  char prefixo = p_cmd[0];

  // OLED
  if(prefixo=='O'){
    atualizarOLED(p_cmd);
    return;
  }

  // MATRIZ
  if(prefixo=='M'){

    char *sub=&p_cmd[1];
    uint8_t len=strlen(sub);

    // limpar matriz
    if(strcmp(sub,"CL")==0){
      strip.clear();
      strip.show();
      Serial.println(F("MATRIZ_CLEARED"));
      return;
    }

    // apagar led (LC)
    if(len==2 && isdigit(sub[0]) && isdigit(sub[1])){

      uint8_t l=sub[0]-'0';
      uint8_t c=sub[1]-'0';

      if(l<MATRIX_SIZE && c<MATRIX_SIZE){
        strip.setPixelColor(mapXY(l,c),0);
        strip.show();
        Serial.println(F("LED_OFF_OK"));
      }else{
        Serial.println(F("POS_INVALID"));
      }

      return;
    }

    // ligar led
    if(len==11 || len==12){

      uint8_t l=sub[0]-'0';
      uint8_t c=sub[1]-'0';

      uint16_t r=(sub[2]-'0')*100+(sub[3]-'0')*10+(sub[4]-'0');
      uint16_t g=(sub[5]-'0')*100+(sub[6]-'0')*10+(sub[7]-'0');
      uint16_t b=(sub[8]-'0')*100+(sub[9]-'0')*10+(sub[10]-'0');

      uint8_t intensidade=9;
      if(len==12) intensidade=constrain(sub[11]-'0',1,9);

      r=aplicarIntensidade(constrain(r,0,255),intensidade);
      g=aplicarIntensidade(constrain(g,0,255),intensidade);
      b=aplicarIntensidade(constrain(b,0,255),intensidade);

      strip.setPixelColor(mapXY(l,c),strip.Color(r,g,b));
      strip.show();

      Serial.println(F("LED_ON_OK"));

      return;
    }
  }

  Serial.println(F("CMD_INVALID"));
}

// =====================
// SETUP
// =====================
void setup() {

  Serial.begin(115200);
  Serial.println(F("BOOT_START"));

  Wire.begin();

  if(!display.begin(SSD1306_SWITCHCAPVCC,0x3C)){
    Serial.println(F("OLED_FAIL"));
    for(;;);
  }

  display.clearDisplay();
  display.display();

  strip.begin();
  strip.setBrightness(40);
  strip.clear();
  strip.show();

  Serial.println(F("READY_SYSTEM"));
}

// =====================
// LOOP
// =====================
void loop(){

  while(Serial.available()){

    char ch=Serial.read();

    if(ch=='\n'){

      cmd[cmdIdx]='\0';
      processarComando(cmd);
      cmdIdx=0;

    }else if(cmdIdx<sizeof(cmd)-1){

      cmd[cmdIdx++]=ch;

    }

  }

}