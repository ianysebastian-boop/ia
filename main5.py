
import pandas as pd
from typing import Dict, List, Optional, Tuple

# Cargar los catálogos
modulos = pd.read_excel("catalogo_modulos_teowin.xlsx")
especiales = pd.read_excel("especiales_teowin.xlsx").fillna("")

# Convertir especiales en diccionario
especiales_dict = {}
for _, row in especiales.iterrows():
    nombre = row["Nombre del especial"].strip().lower().replace("_", " ")
    especiales_dict[nombre] = {
        "descripcion": row["Descripción técnica"],
        "requiere_medidas": [m.strip().lower() for m in str(row["Requiere medidas"]).split(",") if m.strip()],
        "acciones": row["Acciones Técnicas"],
        "comentario": row["Comentarios predefinidos"],
        "incremento": float(row["Incremento %"]) if row["Incremento %"] else 0,
        "incompatible_con": [i.strip().lower() for i in str(row["No compatible con"]).split(",") if i.strip()]
    }

def analizar_entrada(texto: str) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[int], List[str]]:
    """Extrae la referencia, medidas y especiales de una entrada de texto.

    Args:
        texto: Cadena con el formato "referencia alto/ancho/profundo [especiales]".

    Returns:
        Una tupla con la referencia, ancho, alto, profundo y una lista de
        especiales detectados. Los valores numéricos o la referencia pueden ser
        ``None`` si la entrada es inválida.
    """
    partes = texto.strip().split()
    if len(partes) < 2:
        return None, None, None, None, []

    referencia = partes[0].strip()
    medidas = partes[1].strip()
    dimensiones = medidas.split("/")
    if len(dimensiones) != 3:
        return referencia, None, None, None, []

    try:
        alto = int(dimensiones[0])
        ancho = int(dimensiones[1])
        profundo = int(dimensiones[2])
    except ValueError:
        return referencia, None, None, None, []

    especiales_input: List[str] = []
    i = 2
    while i < len(partes):
        palabra = partes[i].strip().lower()
        if i + 1 < len(partes) and "/" in partes[i + 1]:
            medidas_extra = partes[i + 1].strip()
            especiales_input.append(f"{palabra} {medidas_extra}")
            i += 2
        else:
            especiales_input.append(palabra)
            i += 1

    return referencia, ancho, alto, profundo, especiales_input


def obtener_mueble(ref: str) -> Optional[pd.Series]:
    """Busca un mueble en el catálogo por su referencia.

    Args:
        ref: Referencia del módulo a buscar.

    Returns:
        La fila del catálogo correspondiente al módulo o ``None`` si no se
        encuentra.
    """
    coincidencias = modulos[modulos["Referencia"].str.lower() == ref.lower()]
    if coincidencias.empty:
        return None
    return coincidencias.iloc[0]

def procesar_especial(
    nombre: str,
    medidas: Dict[str, int],
    colocacion_usada: Optional[str],
    tipo_mueble: Optional[str],
) -> Tuple[List[str], float]:
    """Evalúa un especial y calcula su incremento.

    Args:
        nombre: Nombre del especial a procesar.
        medidas: Diccionario con las medidas disponibles del mueble.
        colocacion_usada: Clave de la colocación detectada en el mueble.
        tipo_mueble: Tipo de mueble al que pertenece la referencia.

    Returns:
        Una lista de mensajes generados y el incremento porcentual acumulado.
    """
    salida: List[str] = []
    incremento_total = 0.0

    regla = especiales_dict.get(nombre)
    if not regla:
        salida.append(f"❌ Especial '{nombre}' no encontrado.")
        return salida, 0.0

    if colocacion_usada and colocacion_usada.lower() in regla["incompatible_con"]:
        salida.append(f"❌ Especial '{nombre}' incompatible con colocación '{colocacion_usada}'.")
        return salida, 0.0
    if tipo_mueble and tipo_mueble.lower() in regla["incompatible_con"]:
        salida.append(f"❌ Especial '{nombre}' incompatible con tipo de mueble '{tipo_mueble}'.")
        return salida, 0.0

    acciones = regla["acciones"]
    for key in regla["requiere_medidas"]:
        valor = medidas.get(key)
        if valor is None:
            salida.append(
                f"❗ Especial '{nombre}' requiere medida '{key}' que no se proporcionó."
            )
            return salida, 0.0
        acciones = acciones.replace(f"{{{key}}}", str(valor))

    salida.append(f"✅ Especial '{nombre}': {acciones}")
    if regla["comentario"]:
        salida.append(f"📝 Comentario: {regla['comentario']}")
    incremento_total += regla["incremento"]

    return salida, incremento_total

def analizar_mueble(
    ref: str, ancho: int, alto: int, profundo: int, especiales_input: List[str]
) -> str:
    """Analiza un mueble con sus medidas y especiales asociados.

    Args:
        ref: Referencia del mueble a validar.
        ancho: Ancho introducido en milímetros.
        alto: Alto introducido en milímetros.
        profundo: Profundidad introducida en milímetros.
        especiales_input: Lista de especiales indicados por el usuario.

    Returns:
        Un texto descriptivo con el resultado del análisis y los puntos
        calculados.
    """
    mueble = obtener_mueble(ref)
    if mueble is None:
        return f"❌ Referencia '{ref}' no encontrada."

    salida: List[str] = []
    incremento_total = 0.0
    colocaciones = str(mueble.get("Colocaciones Permitidas", "")).split(",")
    puntos_base = mueble.get("PUNTOS BASE", 0)
    base = float(puntos_base) if pd.notna(puntos_base) else 0
    tipo_mueble = str(mueble.get("Tipo", "")).lower()

    colocacion_usada: Optional[str] = None
    altura_valida = False
    for coloc in ["S", "A", "C", "X"]:
        if coloc in colocaciones:
            min_col = mueble.get(f"Min {coloc} (mm)")
            max_col = mueble.get(f"Max {coloc} (mm)")
            if pd.notna(min_col) and pd.notna(max_col):
                if int(min_col) <= alto <= int(max_col):
                    colocacion_usada = coloc
                    altura_valida = True
                    break
            elif pd.isna(min_col) and pd.isna(max_col):
                colocacion_usada = coloc
                altura_valida = True
                break

    if not altura_valida:
        salida.append(f"❌ Altura {alto} mm no válida para ninguna colocación de {ref}")
        return "\n".join(salida)

    # Mapear la colocación a su nombre completo
    colocacion_nombres = {"S": "A suelo", "A": "Apilable", "C": "Colgado", "X": ""}
    colocacion_legible = colocacion_nombres.get(colocacion_usada, colocacion_usada)

    descripcion = mueble.get("Descripción", "").strip()
    salida.append(f"✅ {descripcion} ({ref}) {colocacion_legible} con altura {alto} mm")
    salida.append(f"🔢 Puntos base: {base:.2f}")

    # Detectar fondo o ancho especial
    ancho_ref = mueble.get("Ancho (mm)")
    profundo_ref = mueble.get("Profundo (mm)")

    if pd.notna(ancho_ref) and ancho > int(ancho_ref):
        especiales_input.append("ancho especial")
    if pd.notna(profundo_ref) and profundo > int(profundo_ref):
        especiales_input.append("fondo especial")

    # Preparar medidas disponibles
    medidas_disponibles = {
        "alto": alto,
        "ancho": ancho,
        "profundo": profundo,
        "fondo": profundo,
    }

    # Procesar especiales
    ya_procesados = set()
    for esp in especiales_input:
        nombre = esp.strip().lower()
        if not nombre or nombre in ya_procesados:
            continue
        ya_procesados.add(nombre)

        resultados, inc = procesar_especial(
            nombre, medidas_disponibles, colocacion_usada, tipo_mueble
        )
        salida.extend(resultados)
        incremento_total += inc

    if incremento_total > 0:
        puntos_final = base * (1 + incremento_total / 100)
        salida.append(f"💰 Incremento total aplicado: {incremento_total:.0f}%")
        salida.append(f"🎯 Puntos finales: {puntos_final:.2f}")
    else:
        salida.append(f"🎯 Puntos finales: {base:.2f}")

    return "\n".join(salida)

def main() -> None:
    """Ejecuta el validador en modo interactivo por consola."""
    print("🛠️ Validador TEOWIN (versión automática sin input)")
    print("Ejemplo entrada: D1000 180/600/500 encaje columna")
    print("Orden de medidas: alto/ancho/profundo")
    print("Escribe 'salir' para terminar.\n")

    while True:
        entrada = input("🔍 Entrada: ").strip()
        if entrada.lower() in ["salir", "exit", "q"]:
            break
        ref, ancho, alto, profundo, especiales_input = analizar_entrada(entrada)
        if not all([ref, ancho, alto, profundo]):
            print("❌ Entrada no válida. Usa: referencia alto/ancho/profundo especiales")
            continue
        resultado = analizar_mueble(ref, ancho, alto, profundo, especiales_input)
        print("\n--- Resultado ---")
        print(resultado)
        print("-----------------\n")

if __name__ == "__main__":
    main()
