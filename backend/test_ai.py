import os
from ai_utils import gerar_resumo, gerar_pre_diagnostico

# Teste das funções de IA (requer MISTRAL_API_KEY configurada)
if __name__ == "__main__":
    if not os.getenv("MISTRAL_API_KEY"):
        print("MISTRAL_API_KEY não configurada. Defina a variável de ambiente.")
        exit(1)

    problema = "O celular não liga, a tela fica preta."
    tipo = "Smartphone"
    marca = "Samsung Galaxy S20"

    print("Gerando resumo...")
    resumo = gerar_resumo(problema)
    print(f"Resumo: {resumo}")

    print("\nGerando pré-diagnóstico...")
    diag = gerar_pre_diagnostico(tipo, marca, problema)
    print(f"Pré-diagnóstico: {diag}")

    print("\nTeste concluído.")
