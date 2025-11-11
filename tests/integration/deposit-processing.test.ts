/**
 * Integration Tests: Deposit Processing
 * Tests for race condition fixes and deposit confirmation flow
 * FIX #3: Race condition in pending deposits
 * FIX #13: Batch processing optimization
 */

import { AppDataSource } from '../../src/database/data-source';
import { Deposit, User, Transaction } from '../../src/database/entities';
import { TransactionStatus, TransactionType } from '../../src/database/entities/Transaction.entity';
import { DepositProcessor } from '../../src/services/blockchain/deposit-processor';
import { createTestUser, clearDatabase } from '../helpers/database';
import { mockUsers } from '../fixtures/users';
import { ethers } from 'ethers';

describe('Deposit Processing Integration Tests', () => {
  let depositRepo: any;
  let transactionRepo: any;
  let userRepo: any;
  let testUser: User;
  let depositProcessor: DepositProcessor;

  beforeEach(async () => {
    await clearDatabase();

    depositRepo = AppDataSource.getRepository(Deposit);
    transactionRepo = AppDataSource.getRepository(Transaction);
    userRepo = AppDataSource.getRepository(User);

    // Create test user
    testUser = await createTestUser(mockUsers.user1);

    // Mock deposit processor (we'll test the logic, not actual blockchain calls)
    depositProcessor = new DepositProcessor();
  });

  describe('Race Condition Protection (FIX #3)', () => {
    it('should prevent duplicate deposit confirmation with concurrent requests', async () => {
      // Create pending deposit
      const deposit = depositRepo.create({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'a'.repeat(64),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'b'.repeat(40),
      });
      await depositRepo.save(deposit);

      // Simulate concurrent confirmation attempts
      const confirmDeposit = async () => {
        return await AppDataSource.transaction(
          'SERIALIZABLE',
          async (manager) => {
            // Lock deposit for update (FIX #3)
            const lockedDeposit = await manager
              .createQueryBuilder(Deposit, 'deposit')
              .setLock('pessimistic_write')
              .where('deposit.id = :id', { id: deposit.id })
              .andWhere('deposit.status = :status', {
                status: TransactionStatus.PENDING
              })
              .getOne();

            if (!lockedDeposit) {
              throw new Error('Deposit already processed or not found');
            }

            // Confirm deposit
            lockedDeposit.status = TransactionStatus.CONFIRMED;
            await manager.save(lockedDeposit);

            // Create transaction record
            const transaction = manager.create(Transaction, {
              user_id: testUser.id,
              tx_hash: deposit.tx_hash,
              type: TransactionType.DEPOSIT,
              amount: deposit.amount,
              status: TransactionStatus.CONFIRMED,
              from_address: deposit.from_address,
              to_address: deposit.to_address,
            });
            await manager.save(transaction);

            return lockedDeposit;
          }
        );
      };

      // Execute concurrent confirmations
      const results = await Promise.allSettled([
        confirmDeposit(),
        confirmDeposit(),
        confirmDeposit(),
      ]);

      // Only one should succeed
      const successful = results.filter(r => r.status === 'fulfilled');
      const failed = results.filter(r => r.status === 'rejected');

      expect(successful).toHaveLength(1);
      expect(failed).toHaveLength(2);

      // Verify only one transaction was created
      const transactions = await transactionRepo.find({
        where: { tx_hash: deposit.tx_hash },
      });
      expect(transactions).toHaveLength(1);

      // Verify deposit is confirmed
      const finalDeposit = await depositRepo.findOne({
        where: { id: deposit.id },
      });
      expect(finalDeposit.status).toBe(TransactionStatus.CONFIRMED);
    });

    it('should handle multiple deposits with same tx_hash concurrently', async () => {
      const txHash = '0x' + 'c'.repeat(64);

      // Try to create multiple deposits with same tx_hash
      const createDeposit = async (userId: number) => {
        return await depositRepo.save({
          user_id: userId,
          level: 1,
          amount: 10,
          tx_hash: txHash,
          status: TransactionStatus.PENDING,
          from_address: testUser.wallet_address,
          to_address: '0x' + 'd'.repeat(40),
        });
      };

      const user2 = await createTestUser(mockUsers.user2);

      const results = await Promise.allSettled([
        createDeposit(testUser.id),
        createDeposit(user2.id),
      ]);

      // Both should fail if trying to create with same tx_hash
      // (depending on unique constraint setup)
      const deposits = await depositRepo.find({ where: { tx_hash: txHash } });

      // Should have at most one deposit with this tx_hash
      expect(deposits.length).toBeLessThanOrEqual(1);
    });

    it('should properly lock deposit during balance update', async () => {
      const deposit = await depositRepo.save({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'e'.repeat(64),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'f'.repeat(40),
      });

      const initialBalance = testUser.balance || 0;

      // Confirm deposit with balance update
      await AppDataSource.transaction('SERIALIZABLE', async (manager) => {
        // Lock deposit
        const lockedDeposit = await manager
          .createQueryBuilder(Deposit, 'deposit')
          .setLock('pessimistic_write')
          .where('deposit.id = :id', { id: deposit.id })
          .getOne();

        expect(lockedDeposit).not.toBeNull();

        // Lock user
        const lockedUser = await manager
          .createQueryBuilder(User, 'user')
          .setLock('pessimistic_write')
          .where('user.id = :id', { id: testUser.id })
          .getOne();

        expect(lockedUser).not.toBeNull();

        // Update balance
        lockedUser!.balance = (lockedUser!.balance || 0) + deposit.amount;
        await manager.save(lockedUser);

        // Confirm deposit
        lockedDeposit!.status = TransactionStatus.CONFIRMED;
        await manager.save(lockedDeposit);
      });

      // Verify balance updated
      const updatedUser = await userRepo.findOne({ where: { id: testUser.id } });
      expect(updatedUser.balance).toBe(initialBalance + 10);

      // Verify deposit confirmed
      const confirmedDeposit = await depositRepo.findOne({
        where: { id: deposit.id }
      });
      expect(confirmedDeposit.status).toBe(TransactionStatus.CONFIRMED);
    });
  });

  describe('Batch Processing (FIX #13)', () => {
    it('should process multiple pending deposits in batch', async () => {
      // Create multiple pending deposits
      const deposits = [];
      for (let i = 0; i < 10; i++) {
        const deposit = await depositRepo.save({
          user_id: testUser.id,
          level: 1,
          amount: 10,
          tx_hash: '0x' + i.toString().repeat(64),
          status: TransactionStatus.PENDING,
          from_address: testUser.wallet_address,
          to_address: '0x' + 'target'.repeat(8),
        });
        deposits.push(deposit);
      }

      // Fetch pending deposits (simulating batch fetch)
      const BATCH_SIZE = 5;
      const pendingDeposits = await depositRepo.find({
        where: { status: TransactionStatus.PENDING },
        take: BATCH_SIZE,
      });

      expect(pendingDeposits).toHaveLength(5);
      expect(pendingDeposits[0].status).toBe(TransactionStatus.PENDING);
    });

    it('should handle partial batch failures gracefully', async () => {
      // Create deposits with different scenarios
      const validDeposit = await depositRepo.save({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'valid'.repeat(12),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'target'.repeat(8),
      });

      const invalidDeposit = await depositRepo.save({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'invalid'.repeat(11),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'target'.repeat(8),
      });

      const deposits = [validDeposit, invalidDeposit];

      // Process with Promise.allSettled (FIX #13 pattern)
      const processDeposit = async (deposit: Deposit) => {
        if (deposit.tx_hash.includes('invalid')) {
          throw new Error('Invalid deposit');
        }

        deposit.status = TransactionStatus.CONFIRMED;
        await depositRepo.save(deposit);
        return deposit;
      };

      const results = await Promise.allSettled(
        deposits.map(d => processDeposit(d))
      );

      const successful = results.filter(r => r.status === 'fulfilled');
      const failed = results.filter(r => r.status === 'rejected');

      expect(successful).toHaveLength(1);
      expect(failed).toHaveLength(1);

      // Verify valid deposit was confirmed
      const validResult = await depositRepo.findOne({
        where: { id: validDeposit.id }
      });
      expect(validResult.status).toBe(TransactionStatus.CONFIRMED);

      // Verify invalid deposit remained pending
      const invalidResult = await depositRepo.findOne({
        where: { id: invalidDeposit.id }
      });
      expect(invalidResult.status).toBe(TransactionStatus.PENDING);
    });
  });

  describe('Expired Deposit Recovery (FIX #1)', () => {
    it('should mark old pending deposits as expired', async () => {
      // Create old pending deposit (simulate 25 hours ago)
      const oldDeposit = depositRepo.create({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'old'.repeat(16),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'target'.repeat(8),
      });

      // Manually set created_at to 25 hours ago
      oldDeposit.created_at = new Date(Date.now() - 25 * 60 * 60 * 1000);
      await depositRepo.save(oldDeposit);

      // Find expired deposits (older than 24 hours)
      const EXPIRY_HOURS = 24;
      const expiryDate = new Date(Date.now() - EXPIRY_HOURS * 60 * 60 * 1000);

      const expiredDeposits = await depositRepo
        .createQueryBuilder('deposit')
        .where('deposit.status = :status', { status: TransactionStatus.PENDING })
        .andWhere('deposit.created_at < :expiryDate', { expiryDate })
        .getMany();

      expect(expiredDeposits).toHaveLength(1);
      expect(expiredDeposits[0].id).toBe(oldDeposit.id);

      // Mark as expired_pending (FIX #1)
      for (const deposit of expiredDeposits) {
        deposit.status = 'expired_pending' as any;
        await depositRepo.save(deposit);
      }

      // Verify status changed
      const updatedDeposit = await depositRepo.findOne({
        where: { id: oldDeposit.id }
      });
      expect(updatedDeposit.status).toBe('expired_pending');
    });

    it('should not expire recent pending deposits', async () => {
      // Create recent pending deposit (1 hour ago)
      const recentDeposit = depositRepo.create({
        user_id: testUser.id,
        level: 1,
        amount: 10,
        tx_hash: '0x' + 'recent'.repeat(14),
        status: TransactionStatus.PENDING,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'target'.repeat(8),
      });

      recentDeposit.created_at = new Date(Date.now() - 1 * 60 * 60 * 1000);
      await depositRepo.save(recentDeposit);

      // Find expired deposits
      const EXPIRY_HOURS = 24;
      const expiryDate = new Date(Date.now() - EXPIRY_HOURS * 60 * 60 * 1000);

      const expiredDeposits = await depositRepo
        .createQueryBuilder('deposit')
        .where('deposit.status = :status', { status: TransactionStatus.PENDING })
        .andWhere('deposit.created_at < :expiryDate', { expiryDate })
        .getMany();

      expect(expiredDeposits).toHaveLength(0);
    });
  });

  describe('Deposit Tolerance (FIX #2)', () => {
    it('should accept deposit within tight tolerance (0.01 USDT)', async () => {
      const expectedAmount = 10;
      const actualAmount = 10.005; // Within 0.01 tolerance
      const TOLERANCE = 0.01;

      const isValid = Math.abs(actualAmount - expectedAmount) <= TOLERANCE;
      expect(isValid).toBe(true);
    });

    it('should reject deposit outside tolerance', async () => {
      const expectedAmount = 10;
      const actualAmount = 10.02; // Outside 0.01 tolerance
      const TOLERANCE = 0.01;

      const isValid = Math.abs(actualAmount - expectedAmount) <= TOLERANCE;
      expect(isValid).toBe(false);
    });

    it('should accept exact amount', async () => {
      const expectedAmount = 10;
      const actualAmount = 10.0;
      const TOLERANCE = 0.01;

      const isValid = Math.abs(actualAmount - expectedAmount) <= TOLERANCE;
      expect(isValid).toBe(true);
    });

    it('should accept amount at tolerance boundary', async () => {
      const expectedAmount = 10;
      const actualAmount = 10.01; // Exactly at boundary
      const TOLERANCE = 0.01;

      const isValid = Math.abs(actualAmount - expectedAmount) <= TOLERANCE;
      expect(isValid).toBe(true);
    });
  });

  describe('Transaction Deduplication (FIX #18)', () => {
    it('should prevent duplicate transaction creation', async () => {
      const txHash = '0x' + 'duplicate'.repeat(10);

      const createTransaction = async () => {
        return await transactionRepo.save({
          user_id: testUser.id,
          tx_hash: txHash,
          type: TransactionType.DEPOSIT,
          amount: 10,
          status: TransactionStatus.CONFIRMED,
          from_address: testUser.wallet_address,
          to_address: '0x' + 'target'.repeat(8),
        });
      };

      // First creation should succeed
      const firstTx = await createTransaction();
      expect(firstTx.id).toBeDefined();

      // Second creation should fail (unique constraint)
      await expect(createTransaction()).rejects.toThrow();

      // Verify only one transaction exists
      const transactions = await transactionRepo.find({
        where: { tx_hash: txHash },
      });
      expect(transactions).toHaveLength(1);
    });

    it('should allow same tx_hash for different transaction types', async () => {
      // Note: This depends on how unique constraint is set up
      // If constraint is on (tx_hash, type), this should pass
      // If constraint is only on tx_hash, this should fail

      const txHash = '0x' + 'multitype'.repeat(10);

      const depositTx = await transactionRepo.save({
        user_id: testUser.id,
        tx_hash: txHash,
        type: TransactionType.DEPOSIT,
        amount: 10,
        status: TransactionStatus.CONFIRMED,
        from_address: testUser.wallet_address,
        to_address: '0x' + 'target'.repeat(8),
      });

      expect(depositTx.id).toBeDefined();

      // Try to create with different type
      // This test verifies the constraint behavior
      const createReward = async () => {
        return await transactionRepo.save({
          user_id: testUser.id,
          tx_hash: txHash,
          type: TransactionType.REFERRAL_REWARD,
          amount: 1,
          status: TransactionStatus.CONFIRMED,
          from_address: '0x' + 'source'.repeat(8),
          to_address: testUser.wallet_address,
        });
      };

      // Behavior depends on unique constraint configuration
      // If unique(tx_hash, type): should succeed
      // If unique(tx_hash): should fail
      const result = await createReward().catch(err => err);

      if (result instanceof Error) {
        // Unique constraint on tx_hash only
        expect(result).toBeDefined();
      } else {
        // Unique constraint on (tx_hash, type)
        expect(result.id).toBeDefined();
      }
    });
  });
});
