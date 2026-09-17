import pandas as pd
import warnings
warnings.filterwarnings('ignore')

xl = pd.ExcelFile(r'c:\Users\Asus\Documentos\Distribuciones_CYS\FEB 2026 (2).xlsx')
print('=== HOJAS ===')
print(xl.sheet_names)
print()

for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet, header=None)
    print(f'=== HOJA: {sheet} ===')
    print(f'Dimensiones brutas (filas x cols): {df.shape}')

    # Intentar leer con encabezado en fila 0
    df_h = pd.read_excel(xl, sheet_name=sheet, header=0)
    print(f'Columnas detectadas: {list(df_h.columns)}')
    print(f'Tipos de datos:')
    print(df_h.dtypes.to_string())
    print(f'Filas vacías completamente: {df_h.isnull().all(axis=1).sum()}')
    print(f'Duplicados: {df_h.duplicated().sum()}')
    print(f'Nulos por columna:')
    print(df_h.isnull().sum().to_string())
    print()
