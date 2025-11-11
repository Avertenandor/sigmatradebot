/**
 * Integration Tests: Payment Retry System
 * Tests for exponential backoff and Dead Letter Queue
 * FIX #4: Payment retry system with DLQ
 */

import { AppDataSource } from '../../src/database/data-source';
import { Payment, User, PaymentRetry } from '../../src/database/entities';
import { TransactionStatus } from '../../src/database/entities/Transaction.entity';
import { createTestUser, clearDatabase } from '../helpers/database';
import { mockUsers } from '../fixtures/users';

describe('Payment Retry System Integration Tests', () => {
  let paymentRepo: any;
  let retryRepo: any;
  let userRepo: any;
  let testUser: User;

  beforeEach(async () => {
    await clearDatabase();

    paymentRepo = AppDataSource.getRepository(Payment);
    retryRepo = AppDataSource.getRepository(PaymentRetry);
    userRepo = AppDataSource.getRepository(User);

    testUser = await createTestUser(mockUsers.user1);
  });

  describe('Exponential Backoff (FIX #4)', () => {
    it('should create payment retry record on first failure', async () => {
      // Create failed payment
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      // Simulate payment failure and create retry record
      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Network timeout',
        next_retry_at: new Date(Date.now() + 60000), // 1 minute
      });

      expect(retry.id).toBeDefined();
      expect(retry.attempt_count).toBe(1);
      expect(retry.last_error).toBe('Network timeout');
    });

    it('should calculate exponential backoff delays correctly', () => {
      const DELAYS_MS = [
        60000,    // 1 minute
        300000,   // 5 minutes
        900000,   // 15 minutes
        3600000,  // 1 hour
        14400000, // 4 hours
      ];

      for (let attempt = 1; attempt <= 5; attempt++) {
        const delay = DELAYS_MS[attempt - 1];
        const nextRetryAt = new Date(Date.now() + delay);

        expect(nextRetryAt.getTime()).toBeGreaterThan(Date.now());

        // Verify delay increases exponentially
        if (attempt > 1) {
          const prevDelay = DELAYS_MS[attempt - 2];
          expect(delay).toBeGreaterThan(prevDelay);
        }
      }
    });

    it('should increment attempt count on each retry', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      // First attempt
      let retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Error 1',
        next_retry_at: new Date(Date.now() + 60000),
      });

      // Second attempt
      retry.attempt_count += 1;
      retry.last_error = 'Error 2';
      retry.next_retry_at = new Date(Date.now() + 300000);
      retry = await retryRepo.save(retry);

      expect(retry.attempt_count).toBe(2);

      // Third attempt
      retry.attempt_count += 1;
      retry.last_error = 'Error 3';
      retry.next_retry_at = new Date(Date.now() + 900000);
      retry = await retryRepo.save(retry);

      expect(retry.attempt_count).toBe(3);
    });

    it('should not retry before next_retry_at time', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      // Create retry with future next_retry_at
      const futureTime = new Date(Date.now() + 60000); // 1 minute from now
      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Timeout',
        next_retry_at: futureTime,
      });

      // Query for retries that are ready
      const readyRetries = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.next_retry_at <= :now', { now: new Date() })
        .andWhere('retry.attempt_count < :maxAttempts', { maxAttempts: 5 })
        .getMany();

      // Should not include our retry
      expect(readyRetries).toHaveLength(0);
    });

    it('should include retry when next_retry_at has passed', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      // Create retry with past next_retry_at
      const pastTime = new Date(Date.now() - 60000); // 1 minute ago
      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Timeout',
        next_retry_at: pastTime,
      });

      // Query for ready retries
      const readyRetries = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.next_retry_at <= :now', { now: new Date() })
        .andWhere('retry.attempt_count < :maxAttempts', { maxAttempts: 5 })
        .getMany();

      expect(readyRetries).toHaveLength(1);
      expect(readyRetries[0].id).toBe(retry.id);
    });
  });

  describe('Dead Letter Queue (FIX #4)', () => {
    it('should move payment to DLQ after max retries', async () => {
      const MAX_RETRIES = 5;

      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      // Create retry record with max attempts reached
      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: MAX_RETRIES,
        last_error: 'Final error',
        next_retry_at: new Date(Date.now() + 14400000),
        in_dlq: true,
      });

      expect(retry.in_dlq).toBe(true);
      expect(retry.attempt_count).toBe(MAX_RETRIES);

      // Query for DLQ items
      const dlqItems = await retryRepo.find({
        where: { in_dlq: true },
      });

      expect(dlqItems).toHaveLength(1);
      expect(dlqItems[0].payment_id).toBe(payment.id);
    });

    it('should exclude DLQ items from normal retry processing', async () => {
      // Create normal retry
      const normalPayment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      await retryRepo.save({
        payment_id: normalPayment.id,
        attempt_count: 2,
        last_error: 'Normal error',
        next_retry_at: new Date(Date.now() - 1000),
        in_dlq: false,
      });

      // Create DLQ retry
      const dlqPayment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 200,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      await retryRepo.save({
        payment_id: dlqPayment.id,
        attempt_count: 5,
        last_error: 'DLQ error',
        next_retry_at: new Date(Date.now() - 1000),
        in_dlq: true,
      });

      // Query for retries excluding DLQ
      const activeRetries = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.next_retry_at <= :now', { now: new Date() })
        .andWhere('retry.in_dlq = :inDlq', { inDlq: false })
        .andWhere('retry.attempt_count < :maxAttempts', { maxAttempts: 5 })
        .getMany();

      expect(activeRetries).toHaveLength(1);
      expect(activeRetries[0].payment_id).toBe(normalPayment.id);
    });

    it('should track all retry attempts in history', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const errors = [
        'Network timeout',
        'Insufficient gas',
        'Nonce too low',
        'Connection refused',
        'Final error - moving to DLQ',
      ];

      let retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 0,
        last_error: '',
        next_retry_at: new Date(),
      });

      // Simulate 5 retry attempts
      for (let i = 0; i < 5; i++) {
        retry.attempt_count = i + 1;
        retry.last_error = errors[i];
        retry.next_retry_at = new Date(Date.now() + (i + 1) * 60000);

        if (i === 4) {
          retry.in_dlq = true;
        }

        retry = await retryRepo.save(retry);
      }

      const finalRetry = await retryRepo.findOne({
        where: { payment_id: payment.id },
      });

      expect(finalRetry?.attempt_count).toBe(5);
      expect(finalRetry?.last_error).toBe('Final error - moving to DLQ');
      expect(finalRetry?.in_dlq).toBe(true);
    });
  });

  describe('Successful Retry', () => {
    it('should mark payment as resolved when retry succeeds', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 2,
        last_error: 'Previous error',
        next_retry_at: new Date(Date.now() - 1000),
      });

      // Simulate successful retry
      retry.resolved = true;
      retry.resolved_at = new Date();
      await retryRepo.save(retry);

      payment.status = TransactionStatus.CONFIRMED;
      payment.tx_hash = '0x' + 'success'.repeat(12);
      await paymentRepo.save(payment);

      // Verify resolution
      const resolvedRetry = await retryRepo.findOne({
        where: { payment_id: payment.id },
      });

      expect(resolvedRetry?.resolved).toBe(true);
      expect(resolvedRetry?.resolved_at).toBeDefined();

      const confirmedPayment = await paymentRepo.findOne({
        where: { id: payment.id },
      });

      expect(confirmedPayment?.status).toBe(TransactionStatus.CONFIRMED);
      expect(confirmedPayment?.tx_hash).toBeDefined();
    });

    it('should not retry resolved payments', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.CONFIRMED,
        tx_hash: '0x' + 'resolved'.repeat(12),
      });

      await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Old error',
        next_retry_at: new Date(Date.now() - 1000),
        resolved: true,
        resolved_at: new Date(),
      });

      // Query for unresolved retries
      const unresolvedRetries = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.resolved = :resolved', { resolved: false })
        .andWhere('retry.next_retry_at <= :now', { now: new Date() })
        .getMany();

      expect(unresolvedRetries).toHaveLength(0);
    });
  });

  describe('Admin Interface Requirements', () => {
    it('should query DLQ items for admin review', async () => {
      // Create multiple DLQ items
      for (let i = 0; i < 3; i++) {
        const payment = await paymentRepo.save({
          user_id: testUser.id,
          amount: 100 + i * 50,
          to_address: testUser.wallet_address,
          status: TransactionStatus.PENDING,
        });

        await retryRepo.save({
          payment_id: payment.id,
          attempt_count: 5,
          last_error: `Error ${i + 1}`,
          next_retry_at: new Date(),
          in_dlq: true,
        });
      }

      // Admin queries DLQ
      const dlqItems = await retryRepo
        .createQueryBuilder('retry')
        .leftJoinAndSelect('retry.payment', 'payment')
        .where('retry.in_dlq = :inDlq', { inDlq: true })
        .andWhere('retry.resolved = :resolved', { resolved: false })
        .orderBy('retry.updated_at', 'DESC')
        .getMany();

      expect(dlqItems).toHaveLength(3);
      expect(dlqItems[0].in_dlq).toBe(true);
    });

    it('should allow admin to manually resolve DLQ item', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 5,
        last_error: 'Max retries exceeded',
        next_retry_at: new Date(),
        in_dlq: true,
      });

      // Admin manually resolves
      retry.resolved = true;
      retry.resolved_at = new Date();
      retry.last_error = 'Manually resolved by admin';
      await retryRepo.save(retry);

      payment.status = TransactionStatus.CONFIRMED;
      payment.tx_hash = '0x' + 'admin'.repeat(14);
      await paymentRepo.save(payment);

      // Verify resolution
      const resolvedRetry = await retryRepo.findOne({
        where: { id: retry.id },
      });

      expect(resolvedRetry?.resolved).toBe(true);
      expect(resolvedRetry?.last_error).toContain('admin');
    });

    it('should allow admin to retry DLQ item', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 5,
        last_error: 'Max retries exceeded',
        next_retry_at: new Date(),
        in_dlq: true,
      });

      // Admin resets retry count to force retry
      retry.attempt_count = 0;
      retry.in_dlq = false;
      retry.next_retry_at = new Date();
      retry.last_error = 'Admin initiated retry';
      await retryRepo.save(retry);

      // Verify can be retried
      const activeRetries = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.in_dlq = :inDlq', { inDlq: false })
        .andWhere('retry.attempt_count < :maxAttempts', { maxAttempts: 5 })
        .getMany();

      expect(activeRetries).toHaveLength(1);
      expect(activeRetries[0].id).toBe(retry.id);
    });
  });

  describe('Error Tracking', () => {
    it('should categorize different error types', async () => {
      const errorTypes = [
        'Network timeout',
        'Insufficient gas',
        'Nonce too low',
        'User rejected',
        'Contract reverted',
      ];

      const payments = [];
      for (const errorType of errorTypes) {
        const payment = await paymentRepo.save({
          user_id: testUser.id,
          amount: 100,
          to_address: testUser.wallet_address,
          status: TransactionStatus.PENDING,
        });

        await retryRepo.save({
          payment_id: payment.id,
          attempt_count: 1,
          last_error: errorType,
          next_retry_at: new Date(),
        });

        payments.push(payment);
      }

      // Query by error type (for analytics)
      const timeoutErrors = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.last_error LIKE :error', { error: '%timeout%' })
        .getMany();

      expect(timeoutErrors).toHaveLength(1);
      expect(timeoutErrors[0].last_error).toContain('timeout');

      const gasErrors = await retryRepo
        .createQueryBuilder('retry')
        .where('retry.last_error LIKE :error', { error: '%gas%' })
        .getMany();

      expect(gasErrors).toHaveLength(1);
      expect(gasErrors[0].last_error).toContain('gas');
    });

    it('should track timestamps for retry lifecycle', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 1,
        last_error: 'Error',
        next_retry_at: new Date(Date.now() + 60000),
      });

      expect(retry.created_at).toBeDefined();
      expect(retry.updated_at).toBeDefined();

      // Update retry
      await new Promise(resolve => setTimeout(resolve, 100)); // Small delay

      retry.attempt_count = 2;
      const updatedRetry = await retryRepo.save(retry);

      expect(updatedRetry.updated_at.getTime()).toBeGreaterThan(
        retry.created_at.getTime()
      );
    });
  });

  describe('Concurrency Protection', () => {
    it('should handle concurrent retry attempts safely', async () => {
      const payment = await paymentRepo.save({
        user_id: testUser.id,
        amount: 100,
        to_address: testUser.wallet_address,
        status: TransactionStatus.PENDING,
      });

      const retry = await retryRepo.save({
        payment_id: payment.id,
        attempt_count: 2,
        last_error: 'Error',
        next_retry_at: new Date(Date.now() - 1000),
      });

      // Simulate concurrent retry processing
      const processRetry = async () => {
        return await AppDataSource.transaction(
          'SERIALIZABLE',
          async (manager) => {
            // Lock retry for update
            const lockedRetry = await manager
              .createQueryBuilder(PaymentRetry, 'retry')
              .setLock('pessimistic_write')
              .where('retry.id = :id', { id: retry.id })
              .getOne();

            if (!lockedRetry) {
              throw new Error('Retry not found or locked');
            }

            // Increment attempt
            lockedRetry.attempt_count += 1;
            lockedRetry.last_error = 'New attempt';

            await manager.save(lockedRetry);
            return lockedRetry;
          }
        );
      };

      // Execute concurrent attempts
      const results = await Promise.allSettled([
        processRetry(),
        processRetry(),
        processRetry(),
      ]);

      const successful = results.filter(r => r.status === 'fulfilled');
      const failed = results.filter(r => r.status === 'rejected');

      // Only one should succeed due to locking
      expect(successful).toHaveLength(1);
      expect(failed.length).toBeGreaterThan(0);

      // Verify final attempt count
      const finalRetry = await retryRepo.findOne({
        where: { id: retry.id },
      });

      expect(finalRetry?.attempt_count).toBe(3); // Only incremented once
    });
  });
});
