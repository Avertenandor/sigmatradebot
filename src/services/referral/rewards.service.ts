/**
 * Referral Rewards Service
 * Handles reward calculation and processing
 */

import { AppDataSource } from '../../database/data-source';
import { Referral, ReferralEarning } from '../../database/entities';
import { createLogger } from '../../utils/logger.util';
import { REFERRAL_RATES, REFERRAL_DEPTH } from '../../utils/constants';

const logger = createLogger('ReferralRewardsService');

export class ReferralRewardsService {
  private referralRepository = AppDataSource.getRepository(Referral);
  private referralEarningRepository = AppDataSource.getRepository(ReferralEarning);

  /**
   * Calculate referral rewards for a transaction
   * Returns rewards for each level
   */
  calculateRewards(amount: number): Array<{
    level: number;
    rate: number;
    reward: number;
  }> {
    const rewards = [];

    for (let level = 1; level <= REFERRAL_DEPTH; level++) {
      const rate = REFERRAL_RATES[level as keyof typeof REFERRAL_RATES];
      const reward = amount * rate;

      rewards.push({ level, rate, reward });
    }

    return rewards;
  }

  /**
   * Process referral rewards for a deposit
   * Creates earning records for all referrers in chain
   */
  async processReferralRewards(
    userId: number,
    depositAmount: number,
    sourceTransactionId?: number
  ): Promise<{ success: boolean; rewards: number; error?: string }> {
    try {
      // Get all referral relationships where this user is the referral
      const relationships = await this.referralRepository.find({
        where: { referral_id: userId },
        relations: ['referrer'],
        order: { level: 'ASC' },
      });

      if (relationships.length === 0) {
        logger.debug('No referrers found for user', { userId });
        return { success: true, rewards: 0 };
      }

      let totalRewards = 0;

      // Create earning records for each referrer
      for (const relationship of relationships) {
        const level = relationship.level;
        const rate = REFERRAL_RATES[level as keyof typeof REFERRAL_RATES];
        const rewardAmount = depositAmount * rate;

        // Create earning record
        const earning = this.referralEarningRepository.create({
          referral_id: relationship.id,
          amount: rewardAmount.toFixed(8),
          source_transaction_id: sourceTransactionId,
          paid: false, // Will be paid by payment processor
        });

        await this.referralEarningRepository.save(earning);

        // Update total earned in relationship
        const currentTotal = parseFloat(relationship.total_earned);
        relationship.total_earned = (currentTotal + rewardAmount).toFixed(8);
        await this.referralRepository.save(relationship);

        totalRewards += rewardAmount;

        logger.info('Referral reward created', {
          referrerId: relationship.referrer_id,
          referralUserId: userId,
          level,
          rate,
          amount: rewardAmount,
          sourceTransactionId,
        });
      }

      return { success: true, rewards: totalRewards };
    } catch (error) {
      logger.error('Error processing referral rewards', {
        userId,
        depositAmount,
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        success: false,
        rewards: 0,
        error: 'Ошибка при начислении реферальных вознаграждений',
      };
    }
  }

  /**
   * Get pending earnings to be paid
   */
  async getPendingEarnings(
    userId: number,
    options?: { page?: number; limit?: number }
  ): Promise<{
    earnings: ReferralEarning[];
    total: number;
    totalAmount: number;
    page: number;
    pages: number;
  }> {
    const page = options?.page || 1;
    const limit = options?.limit || 10;
    const skip = (page - 1) * limit;

    try {
      // Get user's referral relationships
      const relationships = await this.referralRepository.find({
        where: { referrer_id: userId },
      });

      const relationshipIds = relationships.map((r) => r.id);

      if (relationshipIds.length === 0) {
        return {
          earnings: [],
          total: 0,
          totalAmount: 0,
          page: 1,
          pages: 0,
        };
      }

      const [earnings, total] = await this.referralEarningRepository.findAndCount({
        where: relationshipIds.map((id) => ({
          referral_id: id,
          paid: false,
        })),
        order: { created_at: 'DESC' },
        take: limit,
        skip,
      });

      const totalAmount = earnings.reduce(
        (sum, e) => sum + parseFloat(e.amount),
        0
      );

      const pages = Math.ceil(total / limit);

      return { earnings, total, totalAmount, page, pages };
    } catch (error) {
      logger.error('Error getting pending earnings', {
        userId,
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        earnings: [],
        total: 0,
        totalAmount: 0,
        page: 1,
        pages: 0,
      };
    }
  }

  /**
   * Mark earning as paid (called by payment processor)
   */
  async markEarningAsPaid(
    earningId: number,
    txHash: string
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const earning = await this.referralEarningRepository.findOne({
        where: { id: earningId },
      });

      if (!earning) {
        return { success: false, error: 'Earning not found' };
      }

      if (earning.paid) {
        return { success: false, error: 'Already paid' };
      }

      earning.paid = true;
      earning.tx_hash = txHash;

      await this.referralEarningRepository.save(earning);

      logger.info('Earning marked as paid', {
        earningId,
        amount: earning.amount,
        txHash,
      });

      return { success: true };
    } catch (error) {
      logger.error('Error marking earning as paid', {
        earningId,
        error: error instanceof Error ? error.message : String(error),
      });
      return { success: false, error: 'Error marking as paid' };
    }
  }
}

export default new ReferralRewardsService();
