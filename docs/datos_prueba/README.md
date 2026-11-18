# Datos de prueba — Huella de Carbono ECCI

Este paquete permite probar **todas las funciones** de la app con datos realistas y resultados esperados conocidos.

| Archivo | Para qué sirve |
|---|---|
| `carbon_footprint/management/commands/cargar_datos_prueba.py` | Comando que carga 2022, 2023 y 2024 (ene–mar) y deja 8 corridas en el histórico. |
| `docs/datos_prueba/subir_datos_2025.csv` | Archivo para **Huella → Subir datos → Carga masiva** (31 filas, los 12 tipos que acepta la carga). |
| `docs/datos_prueba/subir_datos_con_errores.csv` | Archivo con errores a propósito para probar las validaciones (1 fila válida + 6 que deben fallar). |

## Qué contiene cada periodo

| Periodo | Contenido | Neto esperado (t CO₂e) |
|---|---|---|
| 2022 anual | Datos reales de la herramienta Excel ECCI, Sede Principal, vuelos y remociones | **304,342** (bruto 309,987; remociones −5,645; biogénico 4,595) |
| 2023 anual | Escenario completo en 3 sedes: gas natural, ACPM en galones y **litros**, GLP en kg, flota, procesos industriales, 4 tipos de extintor/refrigerante, lubricantes, electricidad, 10 vuelos (incluye uno de regreso a Bogotá), salidas de campo, bus/Transmilenio/taxi, hotel y alojamiento con desayuno, papel A4/Carta/Oficio y reciclado, residuos en kg y **toneladas**, 4 tratamientos, agua, remociones forestales, por aprovechamiento y entrada directa | **404,508** (todas las sedes) · Principal 281,958 · Norte 71,510 · Sur 40,965 |
| 2024-01/02/03 | Periodos **mensuales**: electricidad de 3 sedes, agua y papel | 20,793 · 22,169 · 22,912 |
| 2024-03 | Incluye una remoción sin cantidad para ver una **advertencia** | 1 advertencia |
| 2025 anual | Se crea al subir `subir_datos_2025.csv` desde la interfaz | **≈ 369,34** (369,45 si también subes el archivo con errores, que guarda 1 fila válida de 1000 kWh) |

> La suma de las tres sedes 2023 (394,43) es menor que el total (404,508) porque los vuelos son institucionales y solo cuentan en "Todas las sedes". El agua se registra pero no suma al total (decisión del proyecto).

## Pasos para probar en tu computador (Windows, PowerShell)

```powershell
cd "C:\Users\User\Documents\Universidad\proyecto de grado tecnologo\Huella-de-Carbono-ECCI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Base de datos limpia
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue
python manage.py migrate

# Carga catálogos + datos de prueba + 8 corridas
python manage.py cargar_datos_prueba

# Pruebas automáticas (deben pasar 39)
python manage.py test

# Levantar la app
python manage.py runserver
```

Abre http://127.0.0.1:8000/ y sigue este recorrido:

1. **Huella → Resumen general**: elige *Anual 2022*, sede *Todas las sedes* y pulsa **Calcular inventario oficial**. Debe mostrar Huella neta **304.342**.
2. Repite con *Anual 2023* (404.508) y luego con *Anual 2023 + Sede Norte* (71.510).
3. Elige *Marzo 2024*: verás una advertencia por la remoción sin cantidad.
4. **Gráficos**: barras de directas, indirectas y remociones del último cálculo.
5. **Histórico de corridas** → *Actualizar historial*: aparecen las corridas del periodo elegido (las 8 creadas por el comando y las que hagas).
6. **Subir datos → Carga masiva**: deja "Usar valor de la columna record_type", selecciona `docs\datos_prueba\subir_datos_2025.csv` y pulsa **Procesar archivo**. Debe decir *Registros guardados: 31*. Recarga la página y calcula *Anual 2025* (≈ 369,34).
7. Sube `subir_datos_con_errores.csv`: debe decir *Guardados: 1. Errores: 6* (kWh negativo, cantidad negativa, combustible inexistente, sede inexistente, tipo desconocido, año fuera de rango).
8. **Subir datos → formulario individual**: registra a mano un dato (por ejemplo electricidad 2025) y vuelve a calcular para ver el cambio.
9. **Emisiones directas / indirectas / Remociones**: las tablas muestran los registros del periodo más reciente.
10. **Descargar reporte en Excel** (botón superior) después de un cálculo.
11. **API** (navegable en el navegador): http://127.0.0.1:8000/api/ — por ejemplo `/api/electricity/`, `/api/calculation-runs-history/?period_id=1`.
12. **Admin**: `python manage.py createsuperuser` y entra a http://127.0.0.1:8000/admin/.

Para volver a empezar: `python manage.py cargar_datos_prueba --reset` (borra y recarga solo 2022, 2023 y 2024 ene–mar; 2025 no se toca).
Opción `--sin-corridas` carga los datos sin ejecutar cálculos.

## Hallazgos que salieron al probar

- **Lubricantes (ED5) da 0,000 t**: el factor del catálogo es 0,00178 kg CO₂/gal (aceite) y 0,00059 kg/kg (grasa); parece estar en t CO₂ por unidad en vez de kg. Revisar contra la hoja FE.
- **Vidrio especial en procesos industriales (ED3)** usa 0,03 por tonelada mientras las calcinaciones usan 439,71 kg/t; posible mezcla de unidades (t vs kg) en el catálogo.
- **Las tablas de Alcance 1/2 calculan un "estimado" distinto del motor oficial**: 105 gal de ACPM muestran 0,031 t en la tabla, y el motor da 1,034 t. El resultado válido es el de Huella.
- Los tipos *procesos industriales, lubricantes y agua* no se pueden subir por la carga masiva (no están en la lista); entran por el comando, la API o el admin.
