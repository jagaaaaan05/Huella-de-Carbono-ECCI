# Regresion UI E2E - Flujo Oficial

Fecha base: 2026-04-27

## Objetivo
Verificar que la interfaz operativa mantenga el flujo oficial de calculo backend y no reintroduzca calculos locales inconsistentes.

## Alcance minimo
- Pantallas: Emisiones directas, Emisiones indirectas, Remociones.
- Reglas:
  - No debe existir boton `Calcular` en tablas operativas.
  - En tablas `backend-official`, no deben existir botones `add-row` ni `remove-row`.
  - Selects de variable/unidad deben tener opciones cargadas cuando aplique.
  - `Exportar CSV` debe seguir disponible y funcional.

## Checklist manual
1. Abrir aplicacion en `http://127.0.0.1:8000/`.
2. Ir a Emisiones directas -> Combustibles estacionarias.
3. Validar acciones visibles: solo `Exportar CSV`.
4. Ir a Emisiones indirectas -> Electricidad / Viajes.
5. Validar acciones visibles: solo `Exportar CSV`.
6. Verificar que los selects de tipo/unidad muestren opciones (no solo placeholder).
7. Ir a Remociones -> Inventario forestal / Residuos aprovechables.
8. Validar acciones visibles: solo `Exportar CSV`.
9. Ejecutar `Exportar CSV` y confirmar descarga con contenido no vacio.

## Evidencia recomendada
- Captura de cada pantalla con acciones visibles.
- Nombre del archivo CSV descargado y primeras 3 lineas del contenido.

## Criterio de aceptacion
Se acepta la regresion cuando los 9 pasos pasan sin errores y no aparece ningun flujo de calculo local en UI operativa.
