# Sistema de archivos EFS donde vive la base SQLite (db.sqlite3).
# Se paga solo por lo almacenado (~0,30 USD por GB al mes); una base de unos MB cuesta centavos.
# Pasados 7 días sin acceso, los bloques fríos pasan a la clase Infrequent Access, aún más barata.

resource "aws_efs_file_system" "this" {
  creation_token   = "${var.name}-data"
  encrypted        = true
  performance_mode = "generalPurpose"
  throughput_mode  = "elastic"

  lifecycle_policy {
    transition_to_ia = "AFTER_7_DAYS"
  }

  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = { Name = "${var.name}-data" }
}

resource "aws_efs_backup_policy" "this" {
  file_system_id = aws_efs_file_system.this.id

  backup_policy {
    status = var.backups ? "ENABLED" : "DISABLED"
  }
}

resource "aws_security_group" "efs" {
  name        = "${var.name}-efs"
  description = "NFS solo desde la funcion Lambda"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "nfs" {
  count                        = length(var.allowed_security_group_ids)
  security_group_id            = aws_security_group.efs.id
  referenced_security_group_id = var.allowed_security_group_ids[count.index]
  ip_protocol                  = "tcp"
  from_port                    = 2049
  to_port                      = 2049
}

# Los puntos de montaje no tienen costo.
resource "aws_efs_mount_target" "this" {
  count           = length(var.subnet_ids)
  file_system_id  = aws_efs_file_system.this.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

# Lambda entra siempre como el usuario 1000 a la carpeta /django.
resource "aws_efs_access_point" "this" {
  file_system_id = aws_efs_file_system.this.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/django"
    creation_info {
      owner_uid   = 1000
      owner_gid   = 1000
      permissions = "750"
    }
  }
}
