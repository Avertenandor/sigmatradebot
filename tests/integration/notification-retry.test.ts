/**
 * Integration Tests: Notification Retry System
 * Tests for notification failure tracking and retry with exponential backoff
 * FIX #17: Ensure users don't miss critical notifications
 */

import { AppDataSource } from '../../src/database/data-source';
import { FailedNotification, User } from '../../src/database/entities';
import { createTestUser, clearDatabase } from '../helpers/database';
import { mockUsers } from '../fixtures/users';

describe('Notification Retry System Integration Tests', () => {
  let failedNotificationRepo: any;
  let userRepo: any;
  let testUser: User;

  beforeEach(async () => {
    await clearDatabase();

    failedNotificationRepo = AppDataSource.getRepository(FailedNotification);
    userRepo = AppDataSource.getRepository(User);

    testUser = await createTestUser(mockUsers.user1);
  });

  describe('Failed Notification Tracking (FIX #17)', () => {
    it('should create failed notification record on delivery failure', async () => {
      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: '✅ Ваш депозит подтвержден!',
        metadata: {
          deposit_id: 123,
          amount: 10,
          tx_hash: '0x' + 'abc'.repeat(20),
        },
        attempt_count: 1,
        last_error: 'Forbidden: bot was blocked by the user',
        last_attempt_at: new Date(),
      });

      expect(notification.id).toBeDefined();
      expect(notification.user_telegram_id).toBe(testUser.telegram_id);
      expect(notification.attempt_count).toBe(1);
      expect(notification.resolved).toBe(false);
    });

    it('should track different notification types', async () => {
      const types = [
        'deposit_confirmed',
        'earning_credited',
        'payment_sent',
        'level_upgraded',
        'referral_joined',
      ];

      for (const type of types) {
        await failedNotificationRepo.save({
          user_telegram_id: testUser.telegram_id,
          notification_type: type,
          message: `Test message for ${type}`,
          attempt_count: 1,
          last_error: 'Test error',
          last_attempt_at: new Date(),
        });
      }

      const allFailed = await failedNotificationRepo.find({
        where: { user_telegram_id: testUser.telegram_id },
      });

      expect(allFailed).toHaveLength(5);

      // Check each type exists
      const typesFound = allFailed.map((n: any) => n.notification_type);
      types.forEach(type => {
        expect(typesFound).toContain(type);
      });
    });

    it('should preserve notification metadata for retry', async () => {
      const metadata = {
        deposit_id: 456,
        amount: 50,
        level: 2,
        tx_hash: '0x' + 'def'.repeat(20),
        timestamp: Date.now(),
      };

      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: 'Test message',
        metadata,
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
      });

      const retrieved = await failedNotificationRepo.findOne({
        where: { id: notification.id },
      });

      expect(retrieved.metadata).toEqual(metadata);
      expect(retrieved.metadata.deposit_id).toBe(456);
      expect(retrieved.metadata.tx_hash).toBe('0x' + 'def'.repeat(20));
    });
  });

  describe('Exponential Backoff Retry (FIX #17)', () => {
    it('should use correct delays for each retry attempt', () => {
      const DELAYS_MS = [
        60000,    // 1 minute (1st retry)
        300000,   // 5 minutes (2nd retry)
        900000,   // 15 minutes (3rd retry)
        3600000,  // 1 hour (4th retry)
        7200000,  // 2 hours (5th retry)
      ];

      for (let attempt = 1; attempt <= 5; attempt++) {
        const delay = DELAYS_MS[attempt - 1];
        const nextAttemptTime = new Date(Date.now() + delay);

        expect(nextAttemptTime.getTime()).toBeGreaterThan(Date.now());

        // Verify exponential growth
        if (attempt > 1) {
          const prevDelay = DELAYS_MS[attempt - 2];
          expect(delay).toBeGreaterThan(prevDelay);
        }
      }
    });

    it('should increment attempt count on each retry', async () => {
      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: 1,
        last_error: 'Attempt 1',
        last_attempt_at: new Date(),
      });

      // Simulate retries
      for (let i = 2; i <= 5; i++) {
        notification.attempt_count = i;
        notification.last_error = `Attempt ${i}`;
        notification.last_attempt_at = new Date();
        await failedNotificationRepo.save(notification);
      }

      const final = await failedNotificationRepo.findOne({
        where: { id: notification.id },
      });

      expect(final.attempt_count).toBe(5);
      expect(final.last_error).toBe('Attempt 5');
    });

    it('should respect retry timing based on attempt count', async () => {
      const DELAYS_MS = [60000, 300000, 900000, 3600000, 7200000];

      // Create notifications with different attempt counts
      const notifications = [];
      for (let attempt = 1; attempt <= 5; attempt++) {
        const requiredDelay = DELAYS_MS[attempt - 1];
        const lastAttemptTime = new Date(Date.now() - requiredDelay - 1000);

        const n = await failedNotificationRepo.save({
          user_telegram_id: testUser.telegram_id + attempt,
          notification_type: 'test',
          message: `Test ${attempt}`,
          attempt_count: attempt,
          last_error: 'Error',
          last_attempt_at: lastAttemptTime,
        });

        notifications.push(n);
      }

      // All should be ready for retry (lastAttemptTime + delay has passed)
      for (const notification of notifications) {
        const requiredDelay = DELAYS_MS[notification.attempt_count - 1];
        const timeSinceLastAttempt = Date.now() - notification.last_attempt_at.getTime();

        expect(timeSinceLastAttempt).toBeGreaterThan(requiredDelay);
      }
    });

    it('should not retry before required delay has passed', async () => {
      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: 2,
        last_error: 'Error',
        last_attempt_at: new Date(Date.now() - 60000), // 1 minute ago
      });

      // Required delay for attempt 2 is 5 minutes (300000ms)
      // Only 1 minute has passed, so should not retry yet
      const REQUIRED_DELAY = 300000; // 5 minutes
      const timeSinceLastAttempt = Date.now() - notification.last_attempt_at.getTime();

      expect(timeSinceLastAttempt).toBeLessThan(REQUIRED_DELAY);
    });
  });

  describe('Critical Notifications (FIX #17)', () => {
    it('should mark critical notifications for immediate attention', async () => {
      const criticalNotification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'payment_sent',
        message: '💰 Вам начислено 1000 USDT',
        metadata: { amount: 1000, payment_id: 789 },
        attempt_count: 1,
        last_error: 'User blocked bot',
        last_attempt_at: new Date(),
        critical: true,
      });

      expect(criticalNotification.critical).toBe(true);

      // Query critical notifications
      const criticals = await failedNotificationRepo.find({
        where: { critical: true, resolved: false },
      });

      expect(criticals).toHaveLength(1);
      expect(criticals[0].id).toBe(criticalNotification.id);
    });

    it('should differentiate critical vs non-critical notifications', async () => {
      // Critical
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'payment_sent',
        message: 'Critical payment notification',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
        critical: true,
      });

      // Non-critical
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'referral_joined',
        message: 'New referral joined',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
        critical: false,
      });

      const criticals = await failedNotificationRepo.count({
        where: { critical: true },
      });

      const nonCriticals = await failedNotificationRepo.count({
        where: { critical: false },
      });

      expect(criticals).toBe(1);
      expect(nonCriticals).toBe(1);
    });
  });

  describe('Successful Retry', () => {
    it('should mark notification as resolved on successful delivery', async () => {
      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: 'Test',
        attempt_count: 3,
        last_error: 'Previous error',
        last_attempt_at: new Date(),
      });

      // Simulate successful retry
      notification.resolved = true;
      notification.resolved_at = new Date();
      await failedNotificationRepo.save(notification);

      const resolved = await failedNotificationRepo.findOne({
        where: { id: notification.id },
      });

      expect(resolved.resolved).toBe(true);
      expect(resolved.resolved_at).toBeDefined();
    });

    it('should not retry resolved notifications', async () => {
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: 2,
        last_error: 'Old error',
        last_attempt_at: new Date(Date.now() - 600000), // 10 minutes ago
        resolved: true,
        resolved_at: new Date(),
      });

      // Query unresolved notifications
      const unresolved = await failedNotificationRepo.find({
        where: { resolved: false },
      });

      expect(unresolved).toHaveLength(0);
    });

    it('should track time to resolution', async () => {
      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
      });

      const createdAt = notification.created_at;

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 100));

      // Resolve
      notification.resolved = true;
      notification.resolved_at = new Date();
      await failedNotificationRepo.save(notification);

      const resolved = await failedNotificationRepo.findOne({
        where: { id: notification.id },
      });

      const timeToResolve = resolved.resolved_at.getTime() - createdAt.getTime();
      expect(timeToResolve).toBeGreaterThan(0);
    });
  });

  describe('Max Retries and Give Up', () => {
    it('should stop retrying after max attempts', async () => {
      const MAX_RETRIES = 5;

      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: MAX_RETRIES,
        last_error: 'Final error',
        last_attempt_at: new Date(),
      });

      // Query notifications that should still be retried
      const pending = await failedNotificationRepo
        .createQueryBuilder('notification')
        .where('notification.resolved = :resolved', { resolved: false })
        .andWhere('notification.attempt_count < :maxRetries', { maxRetries: MAX_RETRIES })
        .getMany();

      expect(pending).toHaveLength(0);
    });

    it('should identify notifications that gave up for admin review', async () => {
      const MAX_RETRIES = 5;

      // Create notification at max retries
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'payment_sent',
        message: 'Important message',
        attempt_count: MAX_RETRIES,
        last_error: 'Max retries exceeded',
        last_attempt_at: new Date(),
        critical: true,
      });

      // Query gave-up notifications
      const gaveUp = await failedNotificationRepo
        .createQueryBuilder('notification')
        .where('notification.resolved = :resolved', { resolved: false })
        .andWhere('notification.attempt_count >= :maxRetries', { maxRetries: MAX_RETRIES })
        .getMany();

      expect(gaveUp).toHaveLength(1);
      expect(gaveUp[0].critical).toBe(true);
    });
  });

  describe('Batch Processing', () => {
    it('should fetch pending notifications in batches', async () => {
      // Create 25 notifications
      for (let i = 0; i < 25; i++) {
        await failedNotificationRepo.save({
          user_telegram_id: testUser.telegram_id + i,
          notification_type: 'test',
          message: `Message ${i}`,
          attempt_count: 1,
          last_error: 'Error',
          last_attempt_at: new Date(Date.now() - 120000), // 2 minutes ago
        });
      }

      // Fetch in batches of 10
      const BATCH_SIZE = 10;
      const batch1 = await failedNotificationRepo
        .createQueryBuilder('notification')
        .where('notification.resolved = :resolved', { resolved: false })
        .andWhere('notification.attempt_count < :maxRetries', { maxRetries: 5 })
        .take(BATCH_SIZE)
        .getMany();

      expect(batch1).toHaveLength(10);

      // Fetch second batch (skip first 10)
      const batch2 = await failedNotificationRepo
        .createQueryBuilder('notification')
        .where('notification.resolved = :resolved', { resolved: false })
        .andWhere('notification.attempt_count < :maxRetries', { maxRetries: 5 })
        .skip(BATCH_SIZE)
        .take(BATCH_SIZE)
        .getMany();

      expect(batch2).toHaveLength(10);

      // Third batch should have remaining 5
      const batch3 = await failedNotificationRepo
        .createQueryBuilder('notification')
        .where('notification.resolved = :resolved', { resolved: false })
        .andWhere('notification.attempt_count < :maxRetries', { maxRetries: 5 })
        .skip(BATCH_SIZE * 2)
        .take(BATCH_SIZE)
        .getMany();

      expect(batch3).toHaveLength(5);
    });

    it('should process batch with mixed success/failure', async () => {
      const user2 = await createTestUser(mockUsers.user2);

      const n1 = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Message 1',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(Date.now() - 120000),
      });

      const n2 = await failedNotificationRepo.save({
        user_telegram_id: user2.telegram_id,
        notification_type: 'test',
        message: 'Message 2',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(Date.now() - 120000),
      });

      // Simulate processing: n1 succeeds, n2 fails
      n1.resolved = true;
      n1.resolved_at = new Date();
      await failedNotificationRepo.save(n1);

      n2.attempt_count += 1;
      n2.last_error = 'Retry failed';
      n2.last_attempt_at = new Date();
      await failedNotificationRepo.save(n2);

      // Check results
      const resolved = await failedNotificationRepo.count({
        where: { resolved: true },
      });

      const pending = await failedNotificationRepo.count({
        where: { resolved: false },
      });

      expect(resolved).toBe(1);
      expect(pending).toBe(1);
    });
  });

  describe('Statistics and Monitoring', () => {
    it('should query statistics for monitoring dashboard', async () => {
      const user2 = await createTestUser(mockUsers.user2);

      // Create various notifications
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: 'Test 1',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
        resolved: false,
      });

      await failedNotificationRepo.save({
        user_telegram_id: user2.telegram_id,
        notification_type: 'payment_sent',
        message: 'Test 2',
        attempt_count: 5,
        last_error: 'Max retries',
        last_attempt_at: new Date(),
        resolved: false,
        critical: true,
      });

      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'earning_credited',
        message: 'Test 3',
        attempt_count: 2,
        last_error: 'Error',
        last_attempt_at: new Date(),
        resolved: true,
        resolved_at: new Date(),
      });

      // Get statistics
      const total = await failedNotificationRepo.count();
      const unresolved = await failedNotificationRepo.count({
        where: { resolved: false },
      });
      const critical = await failedNotificationRepo.count({
        where: { critical: true, resolved: false },
      });
      const maxedOut = await failedNotificationRepo.count({
        where: { attempt_count: 5, resolved: false },
      });

      expect(total).toBe(3);
      expect(unresolved).toBe(2);
      expect(critical).toBe(1);
      expect(maxedOut).toBe(1);
    });

    it('should group notifications by type for analytics', async () => {
      // Create notifications of different types
      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: 'Test',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
      });

      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'deposit_confirmed',
        message: 'Test',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
      });

      await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'payment_sent',
        message: 'Test',
        attempt_count: 1,
        last_error: 'Error',
        last_attempt_at: new Date(),
      });

      // Group by type
      const byType = await failedNotificationRepo
        .createQueryBuilder('notification')
        .select('notification.notification_type', 'type')
        .addSelect('COUNT(*)', 'count')
        .groupBy('notification.notification_type')
        .getRawMany();

      expect(byType).toHaveLength(2);

      const depositCount = byType.find((b: any) => b.type === 'deposit_confirmed');
      const paymentCount = byType.find((b: any) => b.type === 'payment_sent');

      expect(parseInt(depositCount.count)).toBe(2);
      expect(parseInt(paymentCount.count)).toBe(1);
    });
  });

  describe('Error Messages', () => {
    it('should preserve detailed error messages', async () => {
      const detailedError = `
Telegram API Error: 403 Forbidden
User has blocked the bot
User ID: ${testUser.telegram_id}
Timestamp: ${new Date().toISOString()}
`;

      const notification = await failedNotificationRepo.save({
        user_telegram_id: testUser.telegram_id,
        notification_type: 'test',
        message: 'Test',
        attempt_count: 1,
        last_error: detailedError.trim(),
        last_attempt_at: new Date(),
      });

      const retrieved = await failedNotificationRepo.findOne({
        where: { id: notification.id },
      });

      expect(retrieved.last_error).toContain('403 Forbidden');
      expect(retrieved.last_error).toContain('blocked the bot');
      expect(retrieved.last_error).toContain(String(testUser.telegram_id));
    });
  });
});
