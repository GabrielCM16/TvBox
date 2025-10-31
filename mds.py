import sys
import board

print("--- Iniciando Diagnóstico Blinka ---")
print("Versão do Python:", sys.version)
print("Plataforma:", sys.platform)

try:
    # Tenta obter o ID da placa que a Blinka detectou
    board_id = board.board_id
    print(f"SUCESSO: Blinka detectou a placa com ID: '{board_id}'")
    print("\nOs pinos disponíveis que você pode usar são:")
    # Lista todos os pinos disponíveis no objeto 'board'
    print(dir(board))

except AttributeError:
    print("\nFALHA: Blinka não conseguiu identificar a sua placa (board.board_id não encontrado).")
    print("Isso significa que sua TV Box provavelmente não é suportada nativamente.")

except Exception as e:
    print(f"\nERRO INESPERADO: Ocorreu um erro ao importar a biblioteca 'board': {e}")
    print("Isso pode indicar um problema na instalação da Blinka ou falta de permissões.")

print("--- Fim do Diagnóstico ---")
