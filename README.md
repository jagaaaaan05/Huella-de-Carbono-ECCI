# ECCI Carbon Footprint — Sistema de Inventario GHG

Backend en **Django + Django REST Framework** para la gestión y cálculo del **Inventario de Gases de Efecto Invernadero (GEI)** de la Universidad ECCI, siguiendo la metodología **ISO 14064-1:2020 / NTC Colombia** y el protocolo **GHG Protocol**.

El sistema registra datos de actividad por fuente de emisión, aplica factores de emisión verificados, calcula tCO2e con trazabilidad completa y genera un inventario auditable por periodo y sede.

---

## Inicio rápido

### Opción A — Local (un solo comando)

```bash
pip install -r requirements.txt
py -3 run.py
```

La app queda disponible en:
- `http://127.0.0.1:8000/` — Interfaz web
- `http://127.0.0.1:8000/api/` — API REST

### Opción B — Docker

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/macOS
docker compose up --build
```

### Carga de datos iniciales (factores de emisión y catálogos)

```bash
python manage.py loaddata carbon_footprint/fixtures/initial_data.json
```

---

## Metodología de cálculo

### Normativa aplicada

| Norma | Uso |
|---|---|
| ISO 14064-1:2020 / NTC | Marco general del inventario GHG |
| GHG Protocol | Clasificación Alcance 1, 2, 3 |
| IPCC AR6 2021 | Valores GWP a 100 años |
| UPME FECOC 2016 | Factores de emisión combustibles colombianos |
| GTC-ISO-TR 14069:2017 | Incertidumbre y método de cálculo Alcance 3 |

### Fórmula general

Para cada fuente de emisión con múltiples gases:

```
tCO2e = (A × FE_CO2 + A × FE_CH4 × GWP_CH4 + A × FE_N2O × GWP_N2O) / 1000
```

Donde `A` = dato de actividad en la unidad correspondiente.

### Valores GWP utilizados (IPCC AR6 2021)

| Gas | GWP 100 años | Notas |
|---|---|---|
| CO2 | 1.0 | — |
| CH4 (no fósil) | 27.0 | Residuos, biogénico |
| CH4 (fósil) | 29.8 | Combustión ED1/ED2/ED3 y salidas de campo (EI2) |
| N2O | 273.0 | — |
| HCFC-123 | 90.4 | Extintores — Informe ECCI 2022 |
| HFC-134a / R-404A / R-410A / R-407C / HCFC-22 | 1530 / 3942.8 / 2255.5 / 1624.21 / 1960 | Refrigerantes |

### Factores de emisión base (fixture inicial)

Los factores salen de la hoja FE de la herramienta de cálculo ECCI (`VF_25_07_2024_Herramienta_de_cálculo_huella_de_carbono_corporativa_ECCI.xlsm`). El fixture trae 207 filas: una por gas y agente. Los principales:

| Fuente | Agente | Factor | Unidad | Referencia |
|---|---|---|---|---|
| ED1/ED2 | Diésel / ACPM (B10) | CO2 9.162 + CH4 + N2O; CO2 biogénico 0.688 aparte | kg/gal | FECOC 2016, mezcla 90/10 |
| ED1/ED2 | Gasolina corriente (E10) | CO2 6.856 + CH4 + N2O; CO2 biogénico 0.762 aparte | kg/gal | FECOC 2016, mezcla 90/10 |
| ED1 | Gas natural | CO2 1.98, CH4 3.6e-5, N2O 3.57e-6 | kg/m³ | FECOC 2016 / IPCC 2006 |
| ED1/ED2 | GLP, kerosene, etanol, carbón | CO2, CH4, N2O | kg/unidad | FECOC 2016 / IPCC 2006 |
| ED3 | Cal, cemento, carbonatos, amoniaco, etc. | CO2 o CH4 | kg/t | IPCC 2006 |
| ED4 | Extintores y refrigerantes | PCG AR6 (HCFC-123 90.4, HFC-134a 1530, HFC-227ea 3600) | kg × PCG | IPCC AR6 |
| ED5 | Aceites / grasa lubricante | 0.00178 / 0.00059 | kg CO2/gal, kg CO2/kg | Herramienta ECCI |
| EI1 | Electricidad SIN 2022 | 0.112 | kg CO2/kWh | UPME 2023 |
| EI2 | Vuelos desde Bogotá (50 rutas, ida y regreso o un trayecto) | 34.2 a 1216 | kg CO2e/pasajero | ICAO 2023 |
| EI2 | Salidas de campo, vehículo diésel 12 km/gal | km / 12 × factores diésel B10 | kg/km | MDL Transmilenio 2011 |
| EI2 | Moto, carro/taxi, bus, Transmilenio | 0.195, 0.19, 0.045, 0.012 | kg CO2e/pasajero-km | SDM 2023 |
| EI2 | Hospedaje hotel / alojamiento y desayuno | 7.895 / 4.142 | kg CO2/noche | Ivanova 2012 |
| EI3 | Papel bond / reciclado | 1.05 / 0.81 | kg CO2e/kg | Herramienta ECCI |
| EI4 | Relleno sanitario | 0.048 kg CH4/kg × 27 | kg CH4/kg | CAEM |
| EI4 | Residuos peligrosos, incineración | 0.5; 0.23 a 1.38 | kg CO2/kg | CAEM |
| EI5 | Agua potable Bogotá | 0.345 | kg CO2/m³ | Documento de ecuaciones. Se registra, pero no suma al inventario porque la herramienta ECCI no la incluye |
| RE1 | Aprovechamiento de residuos | −0.048 kg CH4/kg × 27 | kg | CAEM |
| RE1 | Forestal (17 especies) | captura t/ha/año ÷ árboles/ha | kg CO2/árbol | Herramienta ECCI |

El CO2 biogénico (gas `CO2_BIO`) no suma al total: cada cálculo lo devuelve aparte en `biogenic_tco2e`, como en la hoja R_Biogenicas. La prueba `Inventory2022ValidationTestCase` carga los datos 2022 de la herramienta y comprueba que el resultado es 304.342 t CO2e netas, igual que el informe.

### Incertidumbre

Calculada por el método raíz-cuadra-suma (GTC-ISO-TR 14069:2017):

```
U_fuente = sqrt(U_actividad² + U_factor²)
U_inventario = sqrt(Σ(Ei × Ui)²) / Σ(Ei) × 100%
```

---

## Arquitectura del sistema

### Estructura de carpetas

```
HuellaCarbonoECCI/
├── carbon_footprint/
│   ├── engine/                        # Motor de cálculo GHG
│   │   ├── calculation_service.py     # Orquesta el inventario completo
│   │   ├── formulas_engine.py         # Fórmulas matemáticas puras
│   │   ├── emission_factors.py        # Selección de factores desde BD
│   │   ├── emission_sources.py        # Constantes de fuentes (ED1, EI1...)
│   │   ├── gases_catalog.py           # Catálogo GWP por perfil metodológico
│   │   ├── uncertainty_module.py      # Cálculo de incertidumbre
│   │   ├── units_catalog.py           # Conversión de unidades
│   │   ├── validation_engine.py       # Validaciones de datos de actividad
│   │   └── activity_data.py
│   ├── fixtures/
│   │   └── initial_data.json          # Catálogos y factores de emisión iniciales
│   ├── migrations/                    # Migraciones de BD Django
│   ├── models.py                      # Modelos ORM (19 modelos)
│   ├── serializers.py                 # Serializers DRF
│   ├── views.py                       # ViewSets y endpoints API
│   ├── urls.py                        # Enrutamiento API
│   └── tests.py                       # Tests unitarios y de regresión
├── ecci_carbon_footprint_dj/
│   └── settings.py                    # Configuración Django
├── templates/
│   └── carbon_footprint/
│       ├── dashboard.html             # SPA principal (HTMX)
│       └── partials/screens/          # Pantallas por alcance
├── docs/
│   ├── reference/                     # PDFs normativos (fuente de verdad)
│   └── audits/                        # Checklists de QA y modelos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── run.py
```

### Flujo de cálculo

```
[Datos de actividad BD]
        ↓
calculation_service.py
  ├── _calculate_stationary()      ED1 — Combustión estacionaria
  ├── _calculate_mobile()          ED2 — Combustión móvil (flota)
  ├── _calculate_industrial()      ED3 — Procesos industriales
  ├── _calculate_fugitive()        ED4 — Emisiones fugitivas (extintores)
  ├── _calculate_lubricants()      ED5 — Lubricantes
  ├── _calculate_electricity()     EI1 — Electricidad
  ├── _calculate_transport()       EI2 — Transporte y hospedaje + vuelos
  ├── _calculate_paper()           EI3 — Consumo de papel
  ├── _calculate_waste()           EI4 — Residuos sólidos
  └── _calculate_removals()        RE1 — Remociones (forestal + reciclaje)
        ↓
[CalculationRun persistido con trazas auditables]
```

### Modelos principales

| Modelo | Fuente GHG | Alcance |
|---|---|---|
| `NaturalGasConsumption` | ED1 — Combustión estacionaria | Alcance 1 |
| `FuelConsumption` | ED1 — Combustión estacionaria | Alcance 1 |
| `VehicleFleetConsumption` | ED2 — Combustión móvil | Alcance 1 |
| `IndustrialProcessEmission` | ED3 — Procesos industriales | Alcance 1 |
| `ExtinguisherRefill` | ED4 — Emisiones fugitivas | Alcance 1 |
| `ElectricityConsumption` | EI1 — Electricidad | Alcance 2 |
| `FieldPracticeTrip` | EI2 — Transporte terrestre | Alcance 3 |
| `GroundTransportRecord` | EI2 — Transporte terrestre | Alcance 3 |
| `Flight` | EI2 — Transporte aéreo | Alcance 3 |
| `LodgingRecord` | EI2 — Hospedaje | Alcance 3 |
| `PaperConsumption` | EI3 — Consumo papel | Alcance 3 |
| `WasteRecord` | EI4 — Residuos | Alcance 3 |
| `WaterConsumption` | EI5 — Agua potable | Alcance 3 |
| `RemovalRecord` | RE1 — Remociones | Remoción |
| `CalculationRun` | Resultado auditable persistido | — |

---

## Endpoints REST

### Catálogos

| Endpoint | Descripción |
|---|---|
| `GET /api/campus/` | Sedes |
| `GET /api/periods/` | Periodos (año/mes) |
| `GET /api/emission-factors/` | Factores de emisión (`?source_code=EI1&year_applic=2022`) |
| `GET /api/fuel-types/` | Tipos de combustible |
| `GET /api/waste-types/` | Tipos de residuo |
| `GET /api/extinguisher-types/` | Tipos de extintor |
| `GET /api/paper-weight/` | Catálogo de pesos de papel |

### Datos de actividad (CRUD)

| Endpoint | Fuente GHG |
|---|---|
| `/api/natural-gas/` | Gas natural (m³) |
| `/api/fuel/` | Combustibles estacionarios |
| `/api/vehicle-fleet/` | Flota vehicular |
| `/api/extinguisher-refill/` | Recargas de extintores |
| `/api/electricity/` | Consumo eléctrico (kWh) |
| `/api/flights/` | Vuelos (origen, destino, pasajeros, ida y regreso) |
| `/api/field-practice/` | Prácticas de campo (km) |
| `/api/ground-transport/` | Transporte terrestre |
| `/api/lodging/` | Hospedaje (noches) |
| `/api/paper/` | Consumo de papel (resmas) |
| `/api/waste/` | Residuos sólidos (kg) |
| `/api/water/` | Consumo de agua (m³) |
| `/api/removals/` | Remociones: árboles por especie, kg aprovechados o tCO2e directo |
| `/api/industrial-processes/` | Procesos industriales (t) |
| `/api/lubricants/` | Aceites y grasas lubricantes |

Todos los endpoints de datos soportan filtros `?period_id=1&campus_id=1`.

### Cálculo e histórico

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/calculation-runs/` | `POST` | Ejecuta inventario auditable |
| `/api/calculation-runs-history/` | `GET` | Consulta corridas persistidas |

**POST `/api/calculation-runs/`**

```json
{
  "period_id": 1,
  "campus_id": 1,
  "method_profile": "ISO14064_ECCI_2022",
  "include_traces": true
}
```

Respuesta incluye `gross_tco2e`, `removals_tco2e`, `net_tco2e`, `uncertainty_pct`, desglose por fuente y trazas auditables completas.

Filtros para histórico: `period_id`, `campus_id`, `created_from`, `created_to`, `ordering` (`-created_at`, `net_tco2e`...).

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/jagaaaaan05/Huella-de-Carbono-ECCI.git
cd Huella-de-Carbono-ECCI
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Editar `.env` con los valores requeridos:

```
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### 4. Aplicar migraciones y cargar datos iniciales

```bash
python manage.py migrate
python manage.py loaddata carbon_footprint/fixtures/initial_data.json
```

### 5. (Opcional) Crear superusuario para el panel admin

```bash
python manage.py createsuperuser
```

### 6. Ejecutar el servidor

```bash
python manage.py runserver
# o el wrapper simplificado:
py -3 run.py
```

Acceder a:
- **Interfaz web:** http://127.0.0.1:8000/
- **API REST:** http://127.0.0.1:8000/api/
- **Panel Admin:** http://127.0.0.1:8000/admin/

---

## Despliegue con Docker

```bash
docker compose up --build
```

La imagen usa Gunicorn + WhiteNoise. Variables de entorno configurables vía `.env`.

---

## Comandos de desarrollo

| Acción | Comando |
|---|---|
| Aplicar migraciones | `python manage.py migrate` |
| Crear migraciones nuevas | `python manage.py makemigrations` |
| Cargar datos iniciales | `python manage.py loaddata carbon_footprint/fixtures/initial_data.json` |
| Ejecutar tests | `python manage.py test carbon_footprint` |
| Tests de regresión QA | `python manage.py test carbon_footprint.tests.BugRegressionTestCase` |
| Shell interactivo | `python manage.py shell` |
| Generar diagrama ERD | `python manage.py graph_models carbon_footprint -o erd.svg` |

---

## Documentación de referencia

Los documentos fuente del modelo de cálculo se encuentran en `docs/reference/`:

- **Evaluaciones de Ecuaciones de Huella de Carbono.pdf** — Evaluación técnica de todas las fórmulas del modelo de cálculo. Identifica brechas entre factores usados y valores de referencia nacionales.
- **Informe ECCI.pdf** — Informe completo del inventario GHG de la Universidad ECCI año 2022 (304.342 tCO2e). Fuente de los factores de emisión y GWP aplicados.

Estos documentos son la **fuente de verdad** para cualquier modificación de fórmulas o factores de emisión.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.10+ / Django 5+ |
| API REST | Django REST Framework |
| Frontend | HTMX + JavaScript ES6 modules |
| Base de datos | SQLite (dev) / PostgreSQL (prod via DATABASE_URL) |
| Servidor producción | Gunicorn + WhiteNoise |
| Contenedores | Docker / docker-compose |
| CI/CD | GitHub Actions |
| Tests | Django TestCase |

---

## Licencia

Proyecto bajo licencia **MIT** — puedes usarlo, modificarlo y distribuirlo libremente citando su origen.

---

## Autores

**Equipo de Ingeniería Ambiental — Universidad ECCI**

- Juan David Laverde — Desarrollador — juand.laverdemo@ecci.edu.co
- Andres Felipe Orozco — Desarrollador — andresf.orozcom@ecci.edu.co
