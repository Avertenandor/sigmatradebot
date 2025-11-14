"""Database backup task."""

import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from app.config import get_settings


async def backup_database() -> None:
    """
    Backup PostgreSQL database.

    Creates pg_dump backup with retention policy.
    """
    settings = get_settings()

    if not settings.backup_enabled:
        logger.info("Backup disabled in settings")
        return

    try:
        # Create backup directory
        backup_dir = Path(settings.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.sql"

        logger.info(f"Starting database backup to {backup_file}")

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h", settings.db_host,
            "-p", str(settings.db_port),
            "-U", settings.db_user,
            "-d", settings.db_name,
            "-F", "c",  # Custom format (compressed)
            "-f", str(backup_file),
        ]

        # Set password via environment
        env = {"PGPASSWORD": settings.db_password}

        # Run pg_dump
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Backup failed: {stderr.decode()}")
            return

        logger.success(f"Database backup completed: {backup_file}")

        # Cleanup old backups
        await _cleanup_old_backups(backup_dir, settings.backup_retention_days)

    except Exception as e:
        logger.error(f"Backup error: {e}")


async def _cleanup_old_backups(backup_dir: Path, retention_days: int) -> None:
    """Clean up old backup files."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        for backup_file in backup_dir.glob("backup_*.sql"):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

            if file_time < cutoff_date:
                backup_file.unlink()
                logger.info(f"Deleted old backup: {backup_file.name}")

    except Exception as e:
        logger.error(f"Backup cleanup error: {e}")
