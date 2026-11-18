environment              = "staging"
vpc_cidr                 = "10.20.0.0/16"
min_tasks                = 1
max_tasks                = 2
db_instance_class        = "db.t4g.micro"
db_multi_az              = false
db_backup_retention_days = 1
db_deletion_protection   = false
use_fargate_spot         = true
enable_waf               = false

# github_repository = "jagaaaaan05/Huella-de-Carbono-ECCI"
# alarm_email       = "correo@ejemplo.com"
