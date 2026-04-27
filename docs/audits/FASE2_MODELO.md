# Auditoria FASE 2 - Modelo de Huella de Carbono

Fecha: 2026-04-27
Fuente de verdad: docs/reference/Evaluaciones de Ecuaciones de Huella de Carbono(1).pdf

## Matriz de consistencia (documento vs codigo)

1. Combustion estacionaria
- Documento: E = A * FE_CO2 + A * FE_CH4 * PCG_CH4 + A * FE_N2O * PCG_N2O (conversion a toneladas)
- Codigo: carbon_formulas.combustion_estacionaria
- Estado: Parcialmente consistente
- Observacion: El codigo aplica doble division por 1000 (conversion g->kg y kg->t), valida si FE entra en g/unidad.

2. Combustion movil
- Documento: misma estructura de ecuacion que estacionaria
- Codigo: carbon_formulas.combustion_movil
- Estado: Parcialmente consistente
- Observacion: Misma nota de conversion y unidades.

3. Procesos industriales
- Documento: E = Q * FE
- Codigo: carbon_formulas.procesos_industriales
- Estado: Consistente

4. Fugitivas (extintores)
- Documento: E = m * FE (FE incluye GWP), ejemplo FE_R123 = 77
- Codigo: carbon_formulas.fugitivas(m_kg, GWP) / 1000
- Estado: Consistente por conversion a toneladas

5. Electricidad
- Documento: E = C * f / 1000, con referencia UPME 2023: 0.112 kg CO2e/kWh
- Codigo: carbon_formulas.electricidad (consumo_kwh * FE_kg_kwh) / 1000
- Estado: Consistente
- Ajuste aplicado: default FE UI cambiado a 0.112 en templates/carbon_footprint/partials/screens/_screen_alcance2.html

6. Transporte / hospedaje
- Documento: ecuacion general E = D * FE / 1000 y alerta de desfases en hoja Excel
- Codigo: carbon_formulas.transporte_generico
- Estado: Estructuralmente consistente
- Observacion: Los FE por defecto UI deben revisarse contra fuente oficial anual.

7. Papel
- Documento: E = C * FE, conversion de resmas: C_kg = Resmas * 2.5
- Codigo: carbon_formulas.papel_resmas
- Estado: Consistente
- Ajuste aplicado: default FE UI cambiado a 1.35 en templates/carbon_footprint/partials/screens/_screen_alcance2.html

8. Residuos
- Documento: E = M * FE
- Codigo: carbon_formulas.residuos
- Estado: Consistente

9. Remocion forestal
- Documento: remocion con signo negativo (se resta del inventario)
- Codigo: carbon_formulas.remocion_forestal retorna valor positivo
- Estado: Ambiguo
- Riesgo: Medio
- Nota: Confirmar convencion de signo (almacenar remociones positivas y restar en consolidado, o almacenar negativo).

10. Remocion por reciclaje
- Documento: remocion = -(FE_CH4_res * GWP_CH4 * M), FE_CH4_res=0.048, GWP_CH4=27
- Codigo: carbon_formulas.reciclaje devuelve positivo
- Estado: Ambiguo
- Riesgo: Medio
- Ajuste aplicado: default FE_CH4_res UI cambiado a 0.048 en templates/carbon_footprint/partials/screens/_screen_remociones.html

## Factores y desviaciones detectadas

1. Factor electricidad
- Fixture: 0.144 (carbon_footprint/fixtures/initial_data.json)
- Documento: 0.112 para SIN 2022 (UPME 2023)
- Interpretacion: Puede ser diferencia temporal/metodologica. Requiere regla por anio y fuente.

2. Factores de combustible
- Documento muestra FE en orden de g/unidad para ejemplos de validacion.
- Fixture usa varios FE en kg/unidad.
- Riesgo: Alto de inconsistencia si no se valida unidad por factor al calcular.

3. Defaults UI historicamente subestimados
- Electricidad estaba 0.001 (corregido a 0.112)
- Papel estaba 1.0 (corregido a 1.35)
- Reciclaje estaba 1.0 (corregido a 0.048)

## Riesgos cientificos prioritarios

1. Alto: Unidad de FE no normalizada de extremo a extremo (g, kg, t).
2. Alto: Seleccion de factor por fuente/anio sin trazabilidad completa en motor de calculo.
3. Medio: Convencion de signo para remociones no definida explicitamente en backend.
4. Medio: Transporte/hospedaje depende de FE hardcodeados en frontend.

## Acciones recomendadas (FASE 2.1)

1. Implementar validador de unidades por formula (entrada y factor).
2. Construir catalogo de factores versionado por anio/fuente.
3. Definir y documentar convencion de signo para remociones.
4. Mover FE por defecto desde frontend a API/catalogo para evitar divergencias.
5. Agregar pruebas de regresion de formulas con casos del PDF y tolerancias.
