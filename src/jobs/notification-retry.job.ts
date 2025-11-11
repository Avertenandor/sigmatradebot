/**
 * Notification Retry Job
 * Periodically retries failed notification deliveries
 * FIX #17: Ensure users don't miss critical notifications
 */

import { Job } from 'bull';
import { createLogger } from '../utils/logger.util';
import { getQueue, QueueName } from './queue.config';
import { NotificationRetryService } from '../services/notification-retry.service';
import { bot } from '../bot';
import { config } from '../config';

const logger = createLogger('NotificationRetryJob');

export interface NotificationRetryJobData {
  timestamp: number;
}

let notificationRetryService: NotificationRetryService;

/**
 * Initialize the notification retry service
 */
function initService() {
  if (!notificationRetryService) {
    notificationRetryService = new NotificationRetryService(bot);
  }
  return notificationRetryService;
}

/**
 * Process notification retries
 */
export const processNotificationRetries = async (
  job: Job<NotificationRetryJobData>
): Promise<void> => {
  try {
    logger.debug('🔄 Running notification retry processor job...');

    const service = initService();
    const result = await service.processPendingRetries();

    if (result.processed > 0) {
      logger.info(
        `✅ Notification retry processor: ${result.successful} successful, ${result.failed} failed, ${result.gaveUp} gave up out of ${result.processed} total`
      );
    } else {
      logger.debug('ℹ️ No failed notifications to retry');
    }
  } catch (error) {
    logger.error('❌ Notification retry processor job failed:', error);
    throw error; // Let Bull handle retries
  }
};

/**
 * Start notification retry processor job
 * Runs every 30 minutes
 */
export const startNotificationRetryProcessor = async (): Promise<void> => {
  if (!config.jobs.notificationRetryProcessor?.enabled) {
    logger.warn('⚠️ Notification retry processor is disabled');
    return;
  }

  try {
    const queue = getQueue(QueueName.NOTIFICATION_RETRY);

    // Add repeating job (every 30 minutes)
    await queue.add(
      'process-notification-retries',
      { timestamp: Date.now() },
      {
        repeat: {
          every: 1800000, // 30 minutes in milliseconds
        },
        removeOnComplete: true,
        removeOnFail: false,
      }
    );

    // Register processor
    queue.process('process-notification-retries', processNotificationRetries);

    logger.info('✅ Notification retry processor started (running every 30 minutes)');
  } catch (error) {
    logger.error('❌ Failed to start notification retry processor:', error);
    throw error;
  }
};
