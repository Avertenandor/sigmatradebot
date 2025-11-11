/**
 * Notification Retry Service
 * Handles retrying failed notification deliveries with exponential backoff
 * FIX #17: Ensure users don't miss critical notifications
 */

import { AppDataSource } from '../database/data-source';
import { FailedNotification } from '../database/entities';
import { createLogger } from '../utils/logger.util';
import { LessThan, IsNull } from 'typeorm';
import { Telegraf } from 'telegraf';
import { notificationService } from './notification.service';

const logger = createLogger('NotificationRetryService');

export class NotificationRetryService {
  private readonly MAX_RETRIES = 5;
  private readonly RETRY_DELAYS_MS = [
    60000, // 1 minute
    300000, // 5 minutes
    900000, // 15 minutes
    3600000, // 1 hour
    7200000, // 2 hours
  ];

  constructor(private bot: Telegraf) {}

  /**
   * Process pending failed notifications (called by background job)
   */
  async processPendingRetries(): Promise<{
    processed: number;
    successful: number;
    failed: number;
    gaveUp: number;
  }> {
    const failedRepo = AppDataSource.getRepository(FailedNotification);

    try {
      // Get failed notifications ready for retry
      const now = new Date();
      const pending = await failedRepo.find({
        where: {
          resolved: false,
          attempt_count: LessThan(this.MAX_RETRIES),
        },
        order: { created_at: 'ASC' },
        take: 100, // Process in batches
      });

      if (pending.length === 0) {
        logger.debug('No failed notifications to retry');
        return { processed: 0, successful: 0, failed: 0, gaveUp: 0 };
      }

      logger.info(`Processing ${pending.length} failed notifications...`);

      let successful = 0;
      let failed = 0;
      let gaveUp = 0;

      for (const notification of pending) {
        try {
          // Check if enough time has passed since last attempt
          if (notification.last_attempt_at) {
            const timeSinceLastAttempt =
              now.getTime() - notification.last_attempt_at.getTime();
            const requiredDelay = this.RETRY_DELAYS_MS[notification.attempt_count - 1] || this.RETRY_DELAYS_MS[this.RETRY_DELAYS_MS.length - 1];

            if (timeSinceLastAttempt < requiredDelay) {
              logger.debug('Notification not ready for retry yet', {
                id: notification.id,
                attemptCount: notification.attempt_count,
                timeSinceLastMs: timeSinceLastAttempt,
                requiredDelayMs: requiredDelay,
              });
              continue;
            }
          }

          // Attempt to send notification
          await this.bot.telegram.sendMessage(
            notification.user_telegram_id,
            notification.message,
            { parse_mode: 'Markdown' }
          );

          // Success - mark as resolved
          notification.resolved = true;
          notification.resolved_at = new Date();
          await failedRepo.save(notification);

          successful++;

          logger.info('Notification retry successful', {
            id: notification.id,
            telegramId: notification.user_telegram_id,
            type: notification.notification_type,
            attemptCount: notification.attempt_count,
          });
        } catch (error) {
          // Failed again - increment counter
          notification.attempt_count += 1;
          notification.last_error =
            error instanceof Error ? error.message : String(error);
          notification.last_attempt_at = new Date();
          await failedRepo.save(notification);

          failed++;

          logger.warn('Notification retry failed', {
            id: notification.id,
            telegramId: notification.user_telegram_id,
            type: notification.notification_type,
            attemptCount: notification.attempt_count,
            error: notification.last_error,
          });

          // If max retries reached, alert admin and give up
          if (notification.attempt_count >= this.MAX_RETRIES) {
            gaveUp++;

            // Alert admin about giving up
            await notificationService
              .alertNotificationGaveUp(
                notification.user_telegram_id,
                notification.notification_type,
                notification.message,
                notification.last_error || 'Unknown error'
              )
              .catch((err) => {
                logger.error('Failed to alert admin about notification failure', {
                  error: err,
                });
              });

            logger.error('Notification gave up after max retries', {
              id: notification.id,
              telegramId: notification.user_telegram_id,
              type: notification.notification_type,
              attemptCount: notification.attempt_count,
            });
          }
        }
      }

      logger.info('Notification retry batch complete', {
        processed: pending.length,
        successful,
        failed,
        gaveUp,
      });

      return {
        processed: pending.length,
        successful,
        failed,
        gaveUp,
      };
    } catch (error) {
      logger.error('Error processing notification retries', {
        error: error instanceof Error ? error.message : String(error),
      });

      return { processed: 0, successful: 0, failed: 0, gaveUp: 0 };
    }
  }

  /**
   * Get statistics about failed notifications
   */
  async getStatistics(): Promise<{
    total: number;
    unresolved: number;
    critical: number;
    byType: Record<string, number>;
  }> {
    const failedRepo = AppDataSource.getRepository(FailedNotification);

    try {
      const total = await failedRepo.count();
      const unresolved = await failedRepo.count({ where: { resolved: false } });
      const critical = await failedRepo.count({
        where: { resolved: false, critical: true },
      });

      // Get counts by type
      const byTypeResults = await failedRepo
        .createQueryBuilder('fn')
        .select('fn.notification_type', 'type')
        .addSelect('COUNT(*)', 'count')
        .where('fn.resolved = false')
        .groupBy('fn.notification_type')
        .getRawMany();

      const byType: Record<string, number> = {};
      for (const result of byTypeResults) {
        byType[result.type] = parseInt(result.count, 10);
      }

      return { total, unresolved, critical, byType };
    } catch (error) {
      logger.error('Error getting failed notification statistics', {
        error: error instanceof Error ? error.message : String(error),
      });

      return { total: 0, unresolved: 0, critical: 0, byType: {} };
    }
  }

  /**
   * Manually resolve a failed notification
   */
  async resolveNotification(notificationId: number): Promise<boolean> {
    const failedRepo = AppDataSource.getRepository(FailedNotification);

    try {
      const notification = await failedRepo.findOne({
        where: { id: notificationId },
      });

      if (!notification) {
        logger.warn('Notification not found for manual resolution', {
          notificationId,
        });
        return false;
      }

      notification.resolved = true;
      notification.resolved_at = new Date();
      await failedRepo.save(notification);

      logger.info('Notification manually resolved', {
        id: notificationId,
        telegramId: notification.user_telegram_id,
        type: notification.notification_type,
      });

      return true;
    } catch (error) {
      logger.error('Error resolving notification', {
        notificationId,
        error: error instanceof Error ? error.message : String(error),
      });

      return false;
    }
  }
}
