/**
 * Failed Notification Entity
 * Tracks notifications that failed to send (user blocked bot, deleted account, etc.)
 * FIX #17: Enable retry mechanism and admin monitoring
 */

import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('failed_notifications')
export class FailedNotification {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'bigint' })
  user_telegram_id: number;

  @Column({ length: 100 })
  notification_type: string; // 'deposit_confirmed', 'earning', 'withdrawal', etc.

  @Column({ type: 'text' })
  message: string;

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any> | null;

  @Column({ type: 'int', default: 1 })
  attempt_count: number;

  @Column({ type: 'text', nullable: true })
  last_error: string | null;

  @Column({ type: 'boolean', default: false })
  resolved: boolean;

  @Column({ type: 'boolean', default: false })
  critical: boolean; // Mark as critical for immediate admin attention

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;

  @Column({ type: 'timestamp', nullable: true })
  last_attempt_at: Date | null;

  @Column({ type: 'timestamp', nullable: true })
  resolved_at: Date | null;
}
