# Alternativa escalable: ECS Fargate y RDS (Terraform)

> Esta no es la arquitectura principal. La principal, sin costo, está en `../terraform/`.
> Esta sirve si la aplicación crece y necesita PostgreSQL y varios escritores a la vez; cuesta
> unos 48 USD/mes en staging. Sus comandos asumen que esta carpeta se llama `infra/terraform`,
> y su workflow de GitHub Actions es `deploy-ecs.yml`.

Despliega la aplicación Django en **ECS Fargate** detrás de un **Application Load Balancer**,
con **RDS PostgreSQL** en subredes privadas, secretos en **Secrets Manager**, imágenes en **ECR**
y logs y alarmas en **CloudWatch**. Hay dos entornos: `staging` y `prod`.

```
Internet ──► WAF (solo prod: límite por IP y reglas de AWS)
               ▼
           ALB (80/443, subredes públicas)
               │  solo el ALB puede llegar al puerto 8000
               ▼
           ECS Fargate (Gunicorn + Django, subredes públicas, IP pública solo de salida)
               │  solo las tareas pueden llegar al puerto 5432
               ▼
           RDS PostgreSQL 16 (subredes privadas, sin salida a Internet)

ECR (imagen) · Secrets Manager (DJANGO_SECRET_KEY, DATABASE_URL) · CloudWatch (logs, alarmas)
GitHub Actions ──OIDC──► rol IAM de despliegue (push a ECR + reinicio del servicio)
```

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `bootstrap/` | Bucket S3 y tabla DynamoDB para el estado remoto, y aviso de presupuesto. Se aplica una vez |
| `modules/network` | VPC, 2 subredes públicas y 2 privadas en dos zonas, sin NAT Gateway |
| `modules/database` | RDS PostgreSQL cifrado, copias automáticas y secreto `DATABASE_URL` |
| `modules/app` | ECR, ALB, WAF, ECS (tarea, servicio, autoescalado por CPU), IAM, logs y alarmas |
| `modules/github_oidc` | Rol que usa GitHub Actions para desplegar sin llaves guardadas |
| `environments/` | Variables y configuración del backend por entorno |
| `tests/` | Pruebas con proveedores simulados (`terraform test`), no necesitan cuenta de AWS |

## Decisiones de diseño

- **Fargate en lugar de EC2**: no hay servidores que parchear y se paga por tarea.
- **Sin NAT Gateway**: ahorra unos 32 USD/mes por entorno. Las tareas tienen IP pública,
  pero su grupo de seguridad solo acepta tráfico del ALB. La base de datos no tiene salida a Internet.
- **Migraciones al arrancar**: la tarea ejecuta `migrate` antes de Gunicorn, así un despliegue
  nunca deja el esquema atrasado.
- **HTTPS opcional**: sin `certificate_arn` el sitio funciona por HTTP en el DNS del ALB
  (útil para staging); con certificado de ACM, HTTP redirige a HTTPS y se activa HSTS.
- **Fargate Spot en staging**: las tareas de staging cuestan hasta 70 % menos. AWS puede
  interrumpirlas con aviso de dos minutos; ECS lanza otra sola. Producción usa Fargate normal.
- **WAF en producción**: bloquea a una IP que haga más de 100 escrituras (POST, PATCH, DELETE)
  o 1000 peticiones en 5 minutos, y aplica las reglas administradas de AWS contra ataques comunes.
  Mientras la API no tenga autenticación es la principal barrera contra el abuso; no la reemplaza.
- **ECS Exec**: permite abrir una consola dentro del contenedor (`aws ecs execute-command`) para
  cargar datos o crear el superusuario, sin abrir puertos ni usar llaves SSH. Requiere permiso IAM.
- **Alarmas**: 5xx en el balanceador, ninguna tarea sana, base de datos con menos de 2 GB libres
  y CPU de la base sobre 80 %. Llegan por correo si se define `alarm_email`.
- **Presupuesto**: `bootstrap/` puede crear un aviso por correo cuando el gasto mensual de la cuenta
  llega al 80 % del límite, para que una cuenta de estudiante no tenga sorpresas.
- **`/health/`**: el ALB revisa esta ruta, que comprueba la conexión a la base de datos.
  Está implementada en `ecci_carbon_footprint_dj/health.py`.

## Costo aproximado

Estimación de staging en `us-east-2` con precios de lista, sin capa gratuita:

| Recurso | USD/mes |
| --- | --- |
| Application Load Balancer | ~18 |
| Fargate Spot 0,25 vCPU / 512 MB, 1 tarea | ~3 |
| RDS db.t4g.micro + 20 GB gp3 | ~14 |
| IPv4 públicas (ALB y tarea) | ~11 |
| Secrets Manager, CloudWatch, ECR | ~2 |
| **Total** | **~48** |

Producción suma el WAF (~10 USD/mes: 5 por la ACL, 1 por regla y 0,60 por millón de peticiones),
Fargate normal y una base `db.t4g.small`, en total unos 76 USD/mes con una tarea.

Para no pagar mientras no se usa: `terraform destroy -var-file=environments/staging.tfvars`
(staging no tiene protección de borrado).

## Primer despliegue

Requisitos: Terraform >= 1.7, AWS CLI con credenciales de administrador y Docker.

```bash
# 1. Estado remoto (una sola vez por cuenta)
cd infra/terraform/bootstrap
terraform init
terraform apply -var state_bucket_name=ecci-huella-tfstate-<id-de-cuenta> \
  -var budget_email=correo@ejemplo.com -var monthly_budget_usd=100

# 2. Editar environments/staging.backend.hcl con el bucket y la tabla creados

# 3. Infraestructura
cd ..
terraform init -backend-config=environments/staging.backend.hcl
terraform apply -var-file=environments/staging.tfvars

# 4. Primera imagen (después lo hace GitHub Actions)
REPO=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password | docker login --username AWS --password-stdin "${REPO%%/*}"
docker build -t "$REPO:staging" ../..
docker push "$REPO:staging"
aws ecs update-service --cluster "$(terraform output -raw ecs_cluster)" \
  --service "$(terraform output -raw ecs_service)" --force-new-deployment

# 5. Abrir la aplicación
terraform output app_url
```

### Cargar los datos iniciales

El fixture de catálogos y factores se carga una vez desde una consola en el contenedor
(requiere el [plugin de Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
en el equipo local):

```bash
CLUSTER=$(terraform output -raw ecs_cluster)
TASK=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$(terraform output -raw ecs_service)" \
  --query 'taskArns[0]' --output text)

aws ecs execute-command --cluster "$CLUSTER" --task "$TASK" --container web --interactive \
  --command "python manage.py loaddata carbon_footprint/fixtures/initial_data.json"

aws ecs execute-command --cluster "$CLUSTER" --task "$TASK" --container web --interactive \
  --command "python manage.py createsuperuser"
```

## Despliegue continuo

1. En `environments/<entorno>.tfvars`, descomentar `github_repository` y aplicar.
2. En GitHub, crear los entornos `staging` y `prod` (Settings → Environments) con estas variables,
   tomadas de `terraform output`:
   `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN` (= `github_deploy_role_arn`), `ECR_REPOSITORY_URL`,
   `ECS_CLUSTER`, `ECS_SERVICE`.
3. Cada push a `main` ejecuta las pruebas y despliega a staging (`.github/workflows/deploy.yml`).
   Producción se despliega a mano desde *Actions → Deploy to AWS → Run workflow*.
   Se recomienda exigir aprobación en el entorno `prod`.

## Pruebas de la infraestructura

```bash
cd infra/terraform
terraform init -backend=false
terraform validate
terraform test
```

`terraform test` simula AWS y comprueba que staging sirve por HTTP en el DNS del ALB, corre en
Fargate Spot y no lleva WAF, y que producción con dominio y certificado sirve por HTTPS, corre en
Fargate normal, tiene WAF y crea el rol de despliegue.

## Pendiente antes de producción

La infraestructura no corrige los hallazgos del diagnóstico. Antes de abrir producción hay que
añadir autenticación a la API, porque hoy cualquier visitante puede modificar o borrar datos.
