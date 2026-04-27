# Checklist de Preproduccion

Fecha de referencia: 2026-04-27
Proyecto: ECCI Carbon Footprint DJ
Estado esperado: listo para despliegue productivo

## 1) Seguridad y configuracion

- [ ] DJANGO_DEBUG en false.
- [ ] DJANGO_SECRET_KEY definida por variable de entorno y no hardcodeada.
- [ ] DJANGO_ALLOWED_HOSTS configurado con dominios reales de produccion.
- [ ] DJANGO_CSRF_TRUSTED_ORIGINS configurado con URLs HTTPS reales.
- [ ] API con permisos productivos (no AllowAny en endpoints sensibles).
- [ ] Autenticacion y autorizacion revisadas en ViewSets y endpoints custom.
- [ ] CORS revisado (si aplica) con origenes permitidos minimos.
- [ ] Rotacion de secretos definida (claves, tokens, credenciales BD).
- [ ] No exponer archivos .env en repositorio ni artefactos de build.

## 2) Base de datos y migraciones

- [ ] DATABASE_URL apuntando a motor productivo (PostgreSQL recomendado).
- [ ] Conexion segura a BD (TLS/SSL segun entorno).
- [ ] Migraciones aplicadas en entorno staging y luego produccion.
- [ ] Validacion de integridad de tablas criticas post-migracion.
- [ ] Politica de backup y retencion aprobada.
- [ ] Procedimiento de restore probado al menos una vez.

## 3) Estaticos, archivos y frontend

- [ ] collectstatic ejecutado en pipeline o arranque controlado.
- [ ] WhiteNoise o CDN configurado correctamente para static files.
- [ ] Cache busting de assets validado (JS/CSS actualizados en cliente).
- [ ] Verificacion UI: tablas operativas solo exportan CSV en modo oficial.
- [ ] Verificacion UI: flujo de corrida oficial desde Huella funcional.

## 4) API y contrato funcional

- [ ] Endpoint de corrida oficial /api/calculation-runs/ validado end-to-end.
- [ ] Endpoint de historico /api/calculation-runs-history/ validado con filtros.
- [ ] Filtros de factores de emision validados en entorno productivo.
- [ ] Trazabilidad por fuente y evidencia de corrida persistida confirmadas.
- [ ] Validacion de respuestas de error (400/401/403/500) y mensajes.

## 5) Calidad y pruebas

- [ ] python manage.py check sin issues.
- [ ] python manage.py test en verde.
- [ ] Regresion UI ejecutada segun docs/audits/REGRESION_UI_E2E.md.
- [ ] Prueba de exportacion CSV con archivo no vacio y cabeceras correctas.
- [ ] Validacion de datos minimos reales por periodo y sede.

## 6) Observabilidad y operacion

- [ ] Logging estructurado habilitado (app, acceso, errores).
- [ ] Nivel de logs en produccion definido (no debug excesivo).
- [ ] Healthcheck de aplicacion disponible para orquestador/infra.
- [ ] Monitoreo de CPU, RAM, disco, latencia y errores HTTP.
- [ ] Alertas configuradas para caidas, errores 5xx y fallos de BD.
- [ ] Correlacion de eventos de corrida (run_id) en logs.

## 7) Despliegue y rollback

- [ ] Pipeline CI/CD con build reproducible y validaciones previas.
- [ ] Imagen Docker versionada y publicada con tag de release.
- [ ] Estrategia de despliegue definida (blue/green o rolling).
- [ ] Plan de rollback documentado y probado.
- [ ] Ventana de cambio y responsables definidos.

## 8) Cumplimiento y auditoria

- [ ] Metodologia de calculo alineada con documento fuente y versionada.
- [ ] Version de factores de emision documentada por corrida.
- [ ] Evidencia de trazabilidad disponible para auditoria interna/externa.
- [ ] Politica de retencion de historicos de corrida definida.

## 9) Go/No-Go final

- [ ] Aprobacion tecnica (arquitectura/backend/frontend).
- [ ] Aprobacion funcional (usuario lider del proceso).
- [ ] Aprobacion de seguridad.
- [ ] Aprobacion de operacion/infra.
- [ ] Go-Live autorizado.

---

## Evidencia recomendada para cierre

- Resultado de check y tests.
- Capturas de UI clave (Huella + historico + exportacion).
- Registro de despliegue (version, fecha, responsable).
- Registro de backup previo y posterior al despliegue.
