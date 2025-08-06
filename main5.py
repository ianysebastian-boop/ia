from loader import load_catalogs
from validator import analizar_entrada, analizar_mueble


def main():
    print("🛠️ Validador TEOWIN (versión automática sin input)")
    print("Ejemplo entrada: D1000 180/600/500 encaje columna")
    print("Orden de medidas: alto/ancho/profundo")
    print("Escribe 'salir' para terminar.\n")

    modulos, especiales_dict = load_catalogs()

    while True:
        entrada = input("🔍 Entrada: ").strip()
        if entrada.lower() in ["salir", "exit", "q"]:
            break
        ref, ancho, alto, profundo, especiales_input = analizar_entrada(entrada)
        if not all([ref, ancho, alto, profundo]):
            print("❌ Entrada no válida. Usa: referencia alto/ancho/profundo especiales")
            continue
        resultado = analizar_mueble(ref, ancho, alto, profundo, especiales_input, modulos, especiales_dict)
        print("\n--- Resultado ---")
        print(resultado)
        print("-----------------\n")


if __name__ == "__main__":
    main()
