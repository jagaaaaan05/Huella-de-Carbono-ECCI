# Levantar la app en AWS desde Windows

Pasos para desplegar **staging** con PowerShell, desde la raíz del repositorio
(`C:\Users\User\Documents\Universidad\proyecto de grado tecnologo\Huella-de-Carbono-ECCI`).
Para producción se repiten los pasos 4 a 7 cambiando `staging` por `prod`.

Tiempo aproximado: 30 a 45 minutos la primera vez, casi todo esperando a que AWS cree CloudFront.

---

## 1. Instalar las herramientas (una sola vez)

```powershell
winget install Amazon.AWSCLI
winget install Hashicorp.Terraform
winget install Python.Python.3.12
```

Cierra y vuelve a abrir PowerShell, y comprueba las versiones:

```powershell
aws --version          # aws-cli/2.x
terraform version      # 1.10 o superior
py -3.12 --version
```

## 2. Crear la cuenta y las credenciales de AWS

1. Crea la cuenta en <https://aws.amazon.com/free> y activa MFA en el usuario raíz.
2. En la consola, abre **IAM → Usuarios → Crear usuario**, por ejemplo `terraform-admin`,
   y asígnale la política `AdministratorAccess`.
3. En ese usuario, abre **Credenciales de seguridad → Crear clave de acceso → Interfaz de línea de comandos**
   y copia la clave y el secreto. No uses claves del usuario raíz.
4. Configura la CLI:

```powershell
aws configure
# AWS Access Key ID:     <tu clave>
# AWS Secret Access Key: <tu secreto>
# Default region name:   us-east-2
# Default output format: json

aws sts get-caller-identity   # debe mostrar el número de tu cuenta
```

Guarda el número de cuenta, porque lo usarás en el nombre del bucket:

```powershell
$ACCOUNT = aws sts get-caller-identity --query Account --output text
```

## 3. Crear el estado remoto y el aviso de gasto (una sola vez)

```powershell
cd infra\terraform\bootstrap
terraform init
terraform apply -var "state_bucket_name=ecci-huella-tfstate-$ACCOUNT" -var "budget_email=tu-correo@ejemplo.com"
cd ..
```

Escribe `yes` cuando lo pida. Esto crea el bucket S3 del estado y un presupuesto de 1 USD que te
avisa por correo si algo empieza a cobrar. El archivo `bootstrap\terraform.tfstate` queda en tu
equipo: no lo borres.

## 4. Configurar el entorno

Abre `infra\terraform\environments\staging.backend.hcl` y cambia la línea del bucket por el
nombre que acabas de crear:

```hcl
bucket = "ecci-huella-tfstate-123456789012"   # con tu número de cuenta
```

Si quieres recibir las alarmas por correo, descomenta `alarm_email` en `staging.tfvars`.
AWS te enviará un correo de confirmación que debes aceptar.

## 5. Crear la infraestructura

Desde `infra\terraform`:

```powershell
terraform init -backend-config="environments/staging.backend.hcl"
terraform plan  -var-file="environments/staging.tfvars"
terraform apply -var-file="environments/staging.tfvars"
```

`apply` tarda entre 5 y 15 minutos, sobre todo por CloudFront. Al final muestra `app_url`. Si la
abres ahora verás *"Despliegue pendiente"*: la función todavía tiene un código provisional.

## 6. Empaquetar y subir la aplicación

Vuelve a la raíz del repositorio y ejecuta:

```powershell
cd ..\..
Remove-Item -Recurse -Force build, lambda.zip -ErrorAction SilentlyContinue

# Dependencias para Lambda (Linux ARM), aunque estés en Windows
py -3.12 -m pip install --target build --platform manylinux2014_aarch64 --implementation cp `
  --python-version 3.12 --only-binary=:all: -r requirements-lambda.txt

Copy-Item -Recurse manage.py, ecci_carbon_footprint_dj, carbon_footprint, templates build\

cd build
$env:DJANGO_DEBUG = "False"
py -3.12 manage.py collectstatic --noinput
Remove-Item Env:DJANGO_DEBUG
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
py -3.12 -c "import shutil; shutil.make_archive('../lambda', 'zip', '.')"
cd ..

$FUNCTION = terraform -chdir=infra/terraform output -raw lambda_function_name
aws lambda update-function-code --function-name $FUNCTION --zip-file fileb://lambda.zip
aws lambda wait function-updated --function-name $FUNCTION
```

El zip pesa unos 11 MB. Usa `shutil.make_archive` y no `Compress-Archive`: en Windows
PowerShell 5, `Compress-Archive` guarda las rutas con `\` y Lambda no encuentra los archivos.

Agrega `build/` y `lambda.zip` a tu `.gitignore` para no subirlos a git.

## 7. Crear la base, cargar los datos y crear el administrador

```powershell
'{"manage": ["migrate", "--noinput"]}' | Out-File -Encoding ascii migrate.json
'{"manage": ["loaddata", "carbon_footprint/fixtures/initial_data.json"]}' | Out-File -Encoding ascii loaddata.json

aws lambda invoke --function-name $FUNCTION --payload fileb://migrate.json out.json; Get-Content out.json
aws lambda invoke --function-name $FUNCTION --payload fileb://loaddata.json out.json; Get-Content out.json
```

Cada respuesta debe traer `"ok": true`. Para el superusuario del admin, cambia el usuario, el correo
y la clave:

```powershell
'{"manage": ["createsuperuser", "--noinput", "--username", "admin", "--email", "tu-correo@ejemplo.com"], "env": {"DJANGO_SUPERUSER_PASSWORD": "UnaClaveLarga-2026"}}' | Out-File -Encoding ascii superuser.json
aws lambda invoke --function-name $FUNCTION --payload fileb://superuser.json out.json; Get-Content out.json
Remove-Item migrate.json, loaddata.json, superuser.json, out.json
```

## 8. Abrir la aplicación

```powershell
terraform -chdir=infra/terraform output app_url
```

Abre esa dirección (`https://xxxx.cloudfront.net`). El admin está en `/admin/`. La primera visita
después de un rato sin uso tarda de 2 a 4 segundos mientras la función arranca.

---

## Cada vez que cambies el código

Repite el paso 6. Si el cambio incluye migraciones nuevas, repite también el `migrate` del paso 7.
Si prefieres que esto pase solo con cada push, mira la siguiente sección.

## Despliegue automático con GitHub Actions (opcional)

Necesitas permisos de administrador en el repositorio de GitHub.

1. Mueve `infra\terraform\deploy.yml` a `.github\workflows\deploy.yml` y haz commit.
2. En `staging.tfvars`, descomenta `github_repository` con tu repositorio y vuelve a ejecutar el
   `terraform apply` del paso 5.
3. En GitHub, abre **Settings → Environments → New environment**, créalo con el nombre `staging` y
   agrega tres variables con los valores de `terraform output`:
   `AWS_REGION` = `us-east-2`, `AWS_DEPLOY_ROLE_ARN` = `github_deploy_role_arn` y
   `LAMBDA_FUNCTION_NAME` = `lambda_function_name`.

Desde ahí, cada push a `main` ejecuta las pruebas, sube el código y aplica las migraciones.

## Si algo falla

| Síntoma | Causa probable |
| --- | --- |
| *Despliegue pendiente* (503) | Todavía no se subió el código: falta el paso 6 |
| `Forbidden` al abrir la URL `lambda-url...` | Es lo esperado: solo se entra por la URL de CloudFront |
| Error 502 o 504 | Mira los logs: `aws logs tail /aws/lambda/huella-staging --follow` |
| `"ok": false` en un comando | El campo `error` de `out.json` dice qué falló |
| `BucketAlreadyExists` en el paso 3 | El nombre del bucket ya existe en AWS: agrégale un sufijo |
| Un servicio aparece bloqueado por el plan gratuito | Pasa la cuenta al plan de pago; las cuotas Always Free siguen aplicando |

## Apagar todo

```powershell
terraform -chdir=infra/terraform destroy -var-file="environments/staging.tfvars"
```

Esto borra la base SQLite. Si quieres guardar los datos antes, crea un `dump.json` con
`{"manage": ["dumpdata", "--indent", "2"]}` e invócalo como en el paso 7.
