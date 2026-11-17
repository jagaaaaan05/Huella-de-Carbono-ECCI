output "access_point_arn" {
  value = aws_efs_access_point.this.arn
}

output "mount_target_ids" {
  value = aws_efs_mount_target.this[*].id
}
