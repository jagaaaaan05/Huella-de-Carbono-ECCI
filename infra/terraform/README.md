# Infraestructura en AWS sin costo (Terraform)

Despliega la aplicación Django usando solo servicios que caben en la capa **Always Free** de AWS:
**CloudFront** delante de una función **AWS Lambda**, con la base **SQLite** guardada en **EFS**.
No hay servidores, balanceador, NAT, IP públicas ni base de datos administrada, que son los
recursos que cobran por hora. Hay dos entornos: `staging` y `prod`.

```
Navegador ──HTTPS──► CloudFront (caché de /static/, certificado gratuito)
                        │  agrega un encabezado secreto y el Host original
                        ▼
                     URL de la función Lambda (rechaza lo que no venga de CloudFront)
                        │
                        ▼
                     Lambda Python 3.12 arm64 (Django + apig-wsgi), en subredes privadas
                        │  NFS 2049, solo desde la función
                        ▼
                     EFS: /mnt/data/db.sqlite3 (cifrado)

CloudWatch (logs y alarmas) · SNS (correo de alarmas) · AWS Budgets (aviso de gasto)
GitHub Actions ──OIDC──► rol IAM de despliegue (sube el código y ejecuta migrate)
```

## Qué cuesta

| Servicio | Capa gratuita permanente | Uso esperado | USD/mes |
| --- | --- | --- | --- |
| Lambda | 1 M peticiones y 400 000 GB-s al mes | Unas 300 000 peticiones de 1 s con 1 GB | 0 |
| URL de función | Sin costo propio | | 0 |
| CloudFront | 1 TB de salida, 10 M peticiones, 2 M funciones | | 0 |
| CloudWatch | 5 GB de logs, 10 alarmas, 10 métricas | 2 alarmas, logs 14 días | 0 |
| SNS | 1000 correos | | 0 |
| AWS Budgets | 2 presupuestos | 1 | 0 |
| VPC, subredes, grupos de seguridad | Sin costo | | 0 |
| EFS | No tiene capa permanente: 0,30 por GB | Base de unos 50 MB | ~0,02 |
| S3 (estado de Terraform) | No tiene capa permanente: 0,023 por GB | Unos KB | < 0,01 |
| Copias de EFS (solo prod, opcional) | 0,05 por GB | | < 0,01 |
| **Total** | | | **~0,03** |

EFS y S3 son los únicos que cobran, y lo hacen por gigabyte guardado, así que con esta base el
cargo queda en centavos. `bootstrap/` crea un presupuesto de 1 USD que avisa por correo si algo
empieza a cobrar de verdad.

> Las cuentas de AWS creadas desde el 15 de julio de 2025 empiezan en el *plan gratuito*, que dura
> 6 meses y da créditos. Para seguir usando la cuenta después hay que pasarla al plan de pago; las
> cuotas Always Free de la tabla siguen aplicando en ese plan. Conviene confirmarlo en la consola de
> facturación al crear la cuenta.

## Decisiones de diseño

- **Lambda en lugar de contenedores o EC2**: Fargate, ECS, App Runner y el balanceador cobran por
  hora aunque nadie use la aplicación. Lambda cobra por petición y la cuota gratuita alcanza para
  el uso de una universidad. `apig-wsgi` traduce los eventos de Lambda a WSGI, así que Django
  no cambia.
- **SQLite en EFS en lugar de RDS**: RDS y Aurora no tienen capa permanente. DynamoDB sí la tiene,
  pero no funciona con el ORM de Django. SQLite ya es la base por defecto del proyecto y en EFS
  sobrevive entre ejecuciones de la función.
- **CloudFront delante de Lambda**: da HTTPS con dominio propio sin pagar el certificado, guarda
  en caché los archivos estáticos y oculta la URL de la función. Una función de CloudFront copia el
  Host original a `X-Forwarded-Host` y CloudFront agrega un encabezado secreto; el manejador
  (`ecci_carbon_footprint_dj/lambda_handler.py`) rechaza con 403 lo que no lo traiga.
- **Sin Internet en la VPC**: la función solo necesita llegar a EFS. Sin NAT ni Internet Gateway no
  hay cargo por hora y la función no puede sacar datos a ningún lado.
- **Secretos como variables de entorno**: Secrets Manager cobra 0,40 USD por secreto. Las variables
  de Lambda quedan cifradas con la llave administrada de AWS, que es gratuita.
- **Comandos de Django por invocación directa**: la misma función ejecuta `migrate`, `loaddata` o
  `createsuperuser` cuando se invoca con `{"manage": [...]}`. Esa invocación exige credenciales
  de IAM; la URL pública no puede usarla.
- **Estado remoto sin DynamoDB**: Terraform 1.10 bloquea el estado con un archivo en S3.

## Límites que hay que conocer

- **Un escritor a la vez**: SQLite bloquea la base mientras escribe. Para el número de personas que
  registran inventarios en la ECCI alcanza; si crece mucho, la alternativa con RDS está en
  `../terraform-ecs-fargate/` (unos 48 USD/mes).
- **Arranque en frío**: la primera petición tras unos minutos sin uso tarda de 2 a 4 segundos.
- **30 segundos por petición**: es el máximo que CloudFront espera. Los cálculos actuales tardan
  mucho menos.
- **Sin WAF**: AWS WAF cobra unos 10 USD/mes y por eso no está. La API sigue abierta sin
  autenticación (ver el diagnóstico), así que hay que agregarla antes de publicar producción.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `bootstrap/` | Bucket S3 del estado remoto y presupuesto de 1 USD. Se aplica una vez |
| `modules/network` | VPC con dos subredes privadas, sin Internet Gateway ni NAT |
| `modules/storage` | EFS cifrado, punto de montaje por zona y punto de acceso para Django |
| `modules/app` | Lambda, URL de función, CloudFront, IAM, logs y alarmas |
| `modules/github_oidc` | Rol que usa GitHub Actions para desplegar sin llaves guardadas |
| `environments/` | Variables y configuración del backend por entorno |
| `tests/` | Pruebas con proveedores simulados (`terraform test`), no necesitan cuenta de AWS |

Archivos de la aplicación que acompañan esta infraestructura:
`ecci_carbon_footprint_dj/lambda_handler.py`, `requirements-lambda.txt` y
`.github/workflows/deploy.yml`.

## Primer despliegue

Requisitos: Terraform >= 1.10, AWS CLI con credenciales de administrador y Python 3.12.

```bash
# 1. Estado remoto y presupuesto (una sola vez por cuenta)
cd infra/terraform/bootstrap
terraform init
terraform apply -var state_bucket_name=ecci-huella-tfstate-<id-de-cuenta> \
  -var budget_email=correo@ejemplo.com

# 2. Editar environments/staging.backend.hcl con el nombre del bucket

# 3. Infraestructura
cd ..
terraform init -backend-config=environments/staging.backend.hcl
terraform apply -var-file=environments/staging.tfvars
```

La función queda con un código provisional que responde 503. El código real lo sube GitHub
Actions (siguiente sección) o, a mano, los mismos pasos del workflow:

```bash
cd ../..   # raíz del repositorio
pip install --target build --platform manylinux2014_aarch64 --implementation cp \
  --python-version 3.12 --only-binary=:all: -r requirements-lambda.txt
cp -r manage.py ecci_carbon_footprint_dj carbon_footprint templates build/
(cd build && DJANGO_DEBUG=False python manage.py collectstatic --noinput && zip -qr ../lambda.zip .)

FUNCTION=$(terraform -chdir=infra/terraform output -raw lambda_function_name)
aws lambda update-function-code --function-name "$FUNCTION" --zip-file fileb://lambda.zip
aws lambda wait function-updated --function-name "$FUNCTION"
```

### Migraciones, datos iniciales y superusuario

```bash
invoke() {
  aws lambda invoke --function-name "$FUNCTION" --cli-binary-format raw-in-base64-out \
    --payload "$1" /dev/stdout
}

invoke '{"manage": ["migrate", "--noinput"]}'
invoke '{"manage": ["loaddata", "carbon_footprint/fixtures/initial_data.json"]}'
invoke '{"manage": ["createsuperuser", "--noinput", "--username", "admin", "--email", "correo@ejemplo.com"],
         "env": {"DJANGO_SUPERUSER_PASSWORD": "<clave-segura>"}}'

terraform -chdir=infra/terraform output app_url
```

## Despliegue continuo

1. En `environments/<entorno>.tfvars`, descomentar `github_repository` y aplicar.
2. En GitHub, crear los entornos `staging` y `prod` (Settings → Environments) con estas variables,
   tomadas de `terraform output`: `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN` (= `github_deploy_role_arn`)
   y `LAMBDA_FUNCTION_NAME` (= `lambda_function_name`).
3. Cada push a `main` ejecuta las pruebas, publica el código en staging y aplica las migraciones.
   Producción se despliega a mano desde *Actions → Deploy to AWS → Run workflow*.
   Se recomienda exigir aprobación en el entorno `prod`.

GitHub Actions es gratuito para repositorios públicos y tiene 2000 minutos al mes en privados.

## Dominio propio

1. Pedir en ACM, región `us-east-1`, un certificado para el dominio (es gratuito) y validarlo por DNS.
2. Poner `domain_name` y `certificate_arn` en `environments/prod.tfvars` y aplicar.
3. En el DNS de la universidad, crear un CNAME del dominio hacia el output `cloudfront_domain`.

Route 53 no se usa porque cada zona cuesta 0,50 USD al mes.

## Pruebas de la infraestructura

```bash
cd infra/terraform
terraform init -backend=false
terraform validate
terraform test
```

`terraform test` simula AWS y comprueba que staging sirve por HTTPS en el dominio de CloudFront,
que producción con dominio propio usa ese dominio y crea el rol de despliegue, y que un tiempo
máximo de la función mayor a 30 segundos se rechaza.

## Para no pagar nada mientras no se usa

`terraform destroy -var-file=environments/staging.tfvars` borra todo el entorno, incluida la base
SQLite. Antes se puede descargar con `invoke '{"manage": ["dumpdata", "--indent", "2"]}'`.
