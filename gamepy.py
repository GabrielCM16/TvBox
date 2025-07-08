import pygame

# Inicialização
pygame.init()
pygame.joystick.init()

# Verifica se há controle
if pygame.joystick.get_count() == 0:
    print("Nenhum controle detectado.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Controle conectado: {joystick.get_name()}")

# Mapeamento de botões (pode variar)
botoes_map = {
    0: "X",
    1: "Bolinha",
    2: "Quadrado",
    3: "Triângulo",
    4: "L1",
    5: "R1",
    6: "L2",
    7: "R2",
    8: "Select",
    9: "Start",
    10: "L3 (analógico esquerdo)",
    11: "R3 (analógico direito)"
}

# Estado anterior
botoes_anteriores = [False] * joystick.get_numbuttons()
analogs_anteriores = [0.0] * joystick.get_numaxes()

zona_morta = 0.3

while True:
    pygame.event.pump()

    # Verifica botões pressionados (apenas no momento do clique)
    for i in range(joystick.get_numbuttons()):
        pressionado = joystick.get_button(i)
        if pressionado and not botoes_anteriores[i]:
            nome = botoes_map.get(i, f"Botão {i}")
            print(f"[BOTÃO] {nome} pressionado")
        botoes_anteriores[i] = pressionado

    # Verifica movimentação dos analógicos (movimento significativo e novo)
    for i in range(joystick.get_numaxes()):
        valor = joystick.get_axis(i)
        if abs(valor) > zona_morta and abs(analogs_anteriores[i]) <= zona_morta:
            if i == 0:
                direcao = "direita" if valor > 0 else "esquerda"
                print(f"[ANALÓGICO ESQ HORIZONTAL] Movimento para {direcao}")
            elif i == 1:
                direcao = "baixo" if valor > 0 else "cima"
                print(f"[ANALÓGICO ESQ VERTICAL] Movimento para {direcao}")
            # Adicione i == 2, i == 3 se quiser considerar o analógico direito
        analogs_anteriores[i] = valor
