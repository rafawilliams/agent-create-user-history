"""
Genera historias de usuario (Titulo, Descripcion, Criterios de Aceptacion)
a partir de un Excel de entrada que contiene una columna "Titulo", usando
la API de Claude (Anthropic) para redactar descripcion y criterios.

Uso:
    python generador_historias.py entrada.xlsx salida.xlsx

Requiere variable de entorno ANTHROPIC_API_KEY (puede definirse en un
archivo .env en el mismo directorio).
"""

import sys
import re
import json

import pandas as pd
from dotenv import load_dotenv
from anthropic import Anthropic

COLUMNA_TITULO = "Titulo"
MODELO = "claude-sonnet-4-6"

PROMPT_SISTEMA = (
    "Eres un analista de negocio experto en redactar historias de usuario "
    "para equipos de desarrollo de software. A partir de un titulo de "
    "funcionalidad, debes generar una descripcion en formato "
    "'Como [rol], quiero [accion], para [beneficio]' y una lista de 3 a 5 "
    "criterios de aceptacion claros y verificables, en formato Gherkin "
    "(Dado/Cuando/Entonces) cuando sea posible. Responde unicamente en "
    "formato JSON valido con las claves 'descripcion' (string) y "
    "'criterios' (lista de strings), sin texto adicional."
)


def limpiar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto)).strip()


def generar_historia(client: Anthropic, titulo: str) -> dict:
    mensaje = client.messages.create(
        model=MODELO,
        max_tokens=1024,
        system=PROMPT_SISTEMA,
        messages=[
            {
                "role": "user",
                "content": f"Titulo de la funcionalidad: {titulo}",
            }
        ],
    )

    texto_respuesta = mensaje.content[0].text.strip()

    # Por si el modelo envuelve el JSON en bloque de codigo
    texto_respuesta = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto_respuesta.strip())

    datos = json.loads(texto_respuesta)
    return {
        "descripcion": datos["descripcion"],
        "criterios": datos["criterios"],
    }


def procesar(ruta_entrada: str, ruta_salida: str) -> None:
    load_dotenv()
    client = Anthropic()

    df = pd.read_excel(ruta_entrada)

    if COLUMNA_TITULO not in df.columns:
        raise ValueError(
            f"El archivo de entrada debe contener una columna llamada '{COLUMNA_TITULO}'. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    titulos = df[COLUMNA_TITULO].dropna().map(limpiar_texto)
    titulos = titulos[titulos != ""]

    filas = []
    for i, titulo in enumerate(titulos, start=1):
        print(f"[{i}/{len(titulos)}] Generando historia para: {titulo}")
        try:
            historia = generar_historia(client, titulo)
            criterios_texto = "\n".join(f"- {c}" for c in historia["criterios"])
            filas.append(
                {
                    "Titulo": titulo,
                    "Descripcion": historia["descripcion"],
                    "Criterios de Aceptacion": criterios_texto,
                }
            )
        except Exception as exc:
            print(f"  Error generando historia para '{titulo}': {exc}")
            filas.append(
                {
                    "Titulo": titulo,
                    "Descripcion": f"ERROR: {exc}",
                    "Criterios de Aceptacion": "",
                }
            )

    resultado = pd.DataFrame(filas, columns=["Titulo", "Descripcion", "Criterios de Aceptacion"])
    resultado.to_excel(ruta_salida, index=False)
    print(f"Se generaron {len(resultado)} historias de usuario en '{ruta_salida}'.")


def main():
    if len(sys.argv) != 3:
        print("Uso: python generador_historias.py <entrada.xlsx> <salida.xlsx>")
        sys.exit(1)

    procesar(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
