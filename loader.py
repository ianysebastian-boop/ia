import pandas as pd


def load_catalogs(modulos_path="catalogo_modulos_teowin.xlsx", especiales_path="especiales_teowin.xlsx"):
    """Load catalog data and build special items dictionary."""
    modulos = pd.read_excel(modulos_path)
    especiales = pd.read_excel(especiales_path).fillna("")

    especiales_dict = {}
    for _, row in especiales.iterrows():
        nombre = row["Nombre del especial"].strip().lower().replace("_", " ")
        especiales_dict[nombre] = {
            "descripcion": row["Descripción técnica"],
            "requiere_medidas": [m.strip().lower() for m in str(row["Requiere medidas"]).split(",") if m.strip()],
            "acciones": row["Acciones Técnicas"],
            "comentario": row["Comentarios predefinidos"],
            "incremento": float(row["Incremento %"]) if row["Incremento %"] else 0,
            "incompatible_con": [i.strip().lower() for i in str(row["No compatible con"]).split(",") if i.strip()],
        }

    return modulos, especiales_dict
