/**
 * Referral Service
 * Main orchestrator for referral program operations
 */

import { User, ReferralEarning } from '../../database/entities';
import referralCoreService from './core.service';
import referralRewardsService from './rewards.service';
import referralStatsService from './stats.service';

export class ReferralService {
  /**
   * Build referral chain for user up to N levels
   * Returns array of users from direct referrer to Nth level
   */
  async getReferralChain(
    userId: number,
    depth?: number
  ): Promise<User[]> {
    return referralCoreService.getReferralChain(userId, depth);
  }

  /**
   * Create or update referral relationships
   * Called when new user registers with referrer
   */
  async createReferralRelationships(
    newUserId: number,
    directReferrerId: number
  ): Promise<{ success: boolean; error?: string }> {
    return referralCoreService.createReferralRelationships(newUserId, directReferrerId);
  }

  /**
   * Calculate referral rewards for a transaction
   * Returns rewards for each level
   */
  calculateRewards(amount: number): Array<{
    level: number;
    rate: number;
    reward: number;
  }> {
    return referralRewardsService.calculateRewards(amount);
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
    return referralRewardsService.processReferralRewards(
      userId,
      depositAmount,
      sourceTransactionId
    );
  }

  /**
   * Get referral statistics for user
   */
  async getReferralStats(userId: number): Promise<{
    directReferrals: number;
    level2Referrals: number;
    level3Referrals: number;
    totalEarned: number;
    pendingEarnings: number;
    paidEarnings: number;
  }> {
    return referralStatsService.getReferralStats(userId);
  }

  /**
   * Get referral list by level
   */
  async getReferralsByLevel(
    userId: number,
    level: number,
    options?: { page?: number; limit?: number }
  ): Promise<{
    referrals: Array<{
      user: User;
      earned: number;
      joinedAt: Date;
    }>;
    total: number;
    page: number;
    pages: number;
  }> {
    return referralCoreService.getReferralsByLevel(userId, level, options);
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
    return referralRewardsService.getPendingEarnings(userId, options);
  }

  /**
   * Mark earning as paid (called by payment processor)
   */
  async markEarningAsPaid(
    earningId: number,
    txHash: string
  ): Promise<{ success: boolean; error?: string }> {
    return referralRewardsService.markEarningAsPaid(earningId, txHash);
  }

  /**
   * Get platform referral statistics
   */
  async getPlatformReferralStats(): Promise<{
    totalReferrals: number;
    totalEarnings: number;
    paidEarnings: number;
    pendingEarnings: number;
    byLevel: Record<number, { count: number; earnings: number }>;
  }> {
    return referralStatsService.getPlatformReferralStats();
  }

  /**
   * Get referral leaderboard
   * Returns top users by referral count and earnings
   */
  async getReferralLeaderboard(options: {
    limit?: number;
    sortBy?: 'referrals' | 'earnings';
  } = {}): Promise<{
    byReferrals: Array<{
      userId: number;
      username?: string;
      telegramId: number;
      referralCount: number;
      totalEarnings: number;
      rank: number;
    }>;
    byEarnings: Array<{
      userId: number;
      username?: string;
      telegramId: number;
      referralCount: number;
      totalEarnings: number;
      rank: number;
    }>;
  }> {
    return referralStatsService.getReferralLeaderboard(options);
  }

  /**
   * Get user's position in leaderboard
   */
  async getUserLeaderboardPosition(userId: number): Promise<{
    referralRank: number | null;
    earningsRank: number | null;
    totalUsers: number;
  }> {
    return referralStatsService.getUserLeaderboardPosition(userId);
  }
}

export default new ReferralService();
