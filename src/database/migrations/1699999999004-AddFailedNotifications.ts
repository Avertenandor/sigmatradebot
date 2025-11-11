/**
 * Migration: Add failed_notifications table
 * FIX #17: Track and retry failed notification deliveries
 */

import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddFailedNotifications1699999999004 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      CREATE TABLE "failed_notifications" (
        "id" SERIAL PRIMARY KEY,
        "user_telegram_id" BIGINT NOT NULL,
        "notification_type" VARCHAR(100) NOT NULL,
        "message" TEXT NOT NULL,
        "metadata" JSONB,
        "attempt_count" INTEGER NOT NULL DEFAULT 1,
        "last_error" TEXT,
        "resolved" BOOLEAN NOT NULL DEFAULT false,
        "critical" BOOLEAN NOT NULL DEFAULT false,
        "created_at" TIMESTAMP NOT NULL DEFAULT now(),
        "updated_at" TIMESTAMP NOT NULL DEFAULT now(),
        "last_attempt_at" TIMESTAMP,
        "resolved_at" TIMESTAMP
      );
    `);

    // Index for finding unresolved notifications to retry
    await queryRunner.query(`
      CREATE INDEX "IDX_failed_notifications_retry"
      ON "failed_notifications" ("resolved", "attempt_count", "created_at")
      WHERE "resolved" = false AND "attempt_count" < 5;
    `);

    // Index for finding critical unresolved notifications
    await queryRunner.query(`
      CREATE INDEX "IDX_failed_notifications_critical"
      ON "failed_notifications" ("critical", "resolved")
      WHERE "critical" = true AND "resolved" = false;
    `);

    // Index for user lookup
    await queryRunner.query(`
      CREATE INDEX "IDX_failed_notifications_user"
      ON "failed_notifications" ("user_telegram_id", "created_at" DESC);
    `);

    // Index for notification type analytics
    await queryRunner.query(`
      CREATE INDEX "IDX_failed_notifications_type"
      ON "failed_notifications" ("notification_type", "created_at" DESC);
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS "IDX_failed_notifications_type";`);
    await queryRunner.query(`DROP INDEX IF EXISTS "IDX_failed_notifications_user";`);
    await queryRunner.query(`DROP INDEX IF EXISTS "IDX_failed_notifications_critical";`);
    await queryRunner.query(`DROP INDEX IF EXISTS "IDX_failed_notifications_retry";`);
    await queryRunner.query(`DROP TABLE IF EXISTS "failed_notifications";`);
  }
}
