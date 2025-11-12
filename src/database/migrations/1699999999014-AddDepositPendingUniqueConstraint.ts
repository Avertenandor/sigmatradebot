/**
 * Migration: Add partial unique index for pending deposits
 *
 * PURPOSE:
 * - Prevent multiple pending deposits of the same level for the same user
 * - Use partial index (WHERE status='pending') for efficiency
 * - Works in conjunction with transaction locks to prevent race conditions
 *
 * BUSINESS LOGIC:
 * - User can only have ONE pending deposit per level at a time
 * - Once deposit is confirmed/failed, another can be created
 * - Partial index only applies to pending status (no overhead for other statuses)
 *
 * TECHNICAL DETAILS:
 * - PostgreSQL partial index: lightweight and efficient
 * - Only rows with status='pending' are indexed
 * - Combined with SELECT FOR UPDATE in createPendingDeposit() for full protection
 */

import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddDepositPendingUniqueConstraint1699999999014 implements MigrationInterface {
  name = 'AddDepositPendingUniqueConstraint1699999999014';

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Create partial unique index to prevent duplicate pending deposits
    // Only applies to deposits with status='pending'
    await queryRunner.query(`
      CREATE UNIQUE INDEX IF NOT EXISTS idx_deposits_user_level_pending_unique
      ON deposits(user_id, level)
      WHERE status = 'pending'
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Drop the partial unique index
    await queryRunner.query(`
      DROP INDEX IF EXISTS idx_deposits_user_level_pending_unique
    `);
  }
}
