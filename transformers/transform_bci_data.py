if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

from pathlib import Path
import pandas as pd
import glob

@transformer
def transform(directorio, *args, **kwargs):

    ruta_directorio = Path(directorio)
    archivos_encontrados = list(ruta_directorio.glob("ultimosMovimientosNacionales_*.xls"))

    ruta_archivo_excel = archivos_encontrados[0]
    print(f"Procesando archivo: {ruta_archivo_excel}")

    try:
        # Leemos la primera hoja (sheet_name=0) y omitimos las primeras 12 filas.
        # La fila 13 (índice 12) se usará como cabecera.
        df = pd.read_excel(ruta_archivo_excel, sheet_name=0, skiprows=12)

    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo_excel}' no fue encontrado.")
        return None
    except Exception as e:
        print(f"Error al leer el archivo Excel '{ruta_archivo_excel}': {e}")
        return None

    mapeo_columnas = {
        'Fecha': 'fecha',
        'Código referencia': 'codigo',
        'Ciudad': 'ciudad',
        'Descripción': 'descripcion',
        'Tipo de tarjeta': 'tipo_tarjeta',
        'Monto ($)': 'monto'
    }

    columnas_originales_esperadas = list(mapeo_columnas.keys())
    columnas_faltantes = [col for col in columnas_originales_esperadas if col not in df.columns]

    if columnas_faltantes:
        print(f"Advertencia: Faltan las siguientes columnas en el archivo Excel: {columnas_faltantes}")
        print("Se intentará renombrar las columnas disponibles y continuar.")
        # Renombrar solo las columnas que existen
        columnas_a_renombrar = {k: v for k, v in mapeo_columnas.items() if k in df.columns}
        df.rename(columns=columnas_a_renombrar, inplace=True)
    else:
        df.rename(columns=mapeo_columnas, inplace=True)

    # Fecha: convertir a datetime y luego a date (solo la parte de la fecha)
    if 'fecha' in df.columns:
        try:
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d-%m-%Y', errors='coerce').dt.date
        except Exception as e:
            print(f"Advertencia: Error al convertir la columna 'fecha': {e}. Se dejará como está o con NaT.")

    # Código: quitar espacios y convertir a int64 para números grandes
    if 'codigo' in df.columns:
        try:
            df['codigo'] = df['codigo'].astype(str).str.replace(r'\s+', '', regex=True)
            # Intentar convertir a Int64 que soporta NaN, si falla, intentar con float y luego int
            df['codigo'] = pd.to_numeric(df['codigo'], errors='coerce').astype('Int64')
        except Exception as e:
            print(f"Advertencia: Error al convertir la columna 'codigo': {e}. Se dejará como está o con NaN.")


    # Ciudad: asegurar que sea string, rellenar NaN con string vacío
    if 'ciudad' in df.columns:
        df['ciudad'] = df['ciudad'].astype(str)

    # Descripción: asegurar que sea string, rellenar NaN con string vacío
    if 'descripcion' in df.columns:
        df['descripcion'] = df['descripcion'].astype(str)

    # Tipo de tarjeta: extraer los últimos 4 caracteres numéricos y convertir a int
    if 'tipo_tarjeta' in df.columns:
        try:
            # Extraer los últimos 4 caracteres del string
            # Asegurarse de que x sea un string y manejar casos donde podría ser None o no un string
            df['tipo_tarjeta'] = df['tipo_tarjeta'].apply(
                lambda x: str(x)[-4:] if pd.notna(x) and isinstance(x, str) and len(str(x)) >= 4 else (str(x) if pd.notna(x) and isinstance(x, str) else None)
            )
            # Intentar convertir esos 4 caracteres a numérico. Si no son numéricos, resultará en NaN (o NA para Int64).
            df['tipo_tarjeta'] = pd.to_numeric(df['tipo_tarjeta'], errors='coerce').astype('Int64')
        except Exception as e:
            print(f"Advertencia: Error al procesar la columna 'tipo_tarjeta': {e}. Se dejará como está o con NaN.")

    # Monto: quitar comas (separador de miles) y convertir a int
    if 'monto' in df.columns:
        try:
            # Primero convertir a string para poder usar .str.replace
            df['monto'] = df['monto'].astype(str).str.replace(',', '', regex=False)
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').astype('Int64')
        except Exception as e:
            print(f"Advertencia: Error al convertir la columna 'monto': {e}. Se dejará como está o con NaN.")

    borrados_exitosamente = 0
    errores_al_borrar = 0
    for archivo_a_borrar in archivos_encontrados:
        try:
            archivo_a_borrar.unlink() # Borra el archivo
            print(f"Archivo borrado: {archivo_a_borrar}")
            borrados_exitosamente += 1
        except OSError as e:
            print(f"Error al borrar el archivo {archivo_a_borrar}: {e}")
            errores_al_borrar += 1
        except Exception as e_gen:
            print(f"Error inesperado al borrar el archivo {archivo_a_borrar}: {e_gen}")
            errores_al_borrar += 1
    
    print(f"\nResumen del borrado:")
    print(f"  Archivos borrados exitosamente: {borrados_exitosamente}")
    print(f"  Errores al borrar: {errores_al_borrar}")

    return df