"""Execute `python -m projeto_ia.damas.train` para repetir o treinamento."""

from .modeling import treinar


def main():
    metricas = treinar()
    print(f"Modelo: {metricas['modelo_escolhido']}")
    print(f"Teste: acurácia {metricas['modelo_teste']['acuracia']:.2%}; F1 macro {metricas['modelo_teste']['f1_macro']:.2%}")
    print(f"Baseline: acurácia {metricas['baseline_teste']['acuracia']:.2%}; F1 macro {metricas['baseline_teste']['f1_macro']:.2%}")


if __name__ == "__main__":
    main()
