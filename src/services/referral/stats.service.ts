/**
 * Referral Stats Service
 * Handles statistics and leaderboards
 */

import { AppDataSource } from '../../database/data-source';
import { Referral, ReferralEarning, User } from '../../database/entities';
import { createLogger } from '../../utils/logger.util';

const logger = createLogger('ReferralStatsService');

export class ReferralStatsService {
  private referralRepository = AppDataSource.getRepository(Referral);
  private referralEarningRepository = AppDataSource.getRepository(ReferralEarning);
  private userRepository = AppDataSource.getRepository(User);

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
    try {
      // Get all relationships where user is referrer
      const relationships = await this.referralRepository.find({
        where: { referrer_id: userId },
      });

      // Count by level
      const level1 = relationships.filter((r) => r.level === 1).length;
      const level2 = relationships.filter((r) => r.level === 2).length;
      const level3 = relationships.filter((r) => r.level === 3).length;

      // Calculate total earned
      const totalEarned = relationships.reduce(
        (sum, r) => sum + parseFloat(r.total_earned),
        0
      );

      // Get earnings
      const relationshipIds = relationships.map((r) => r.id);

      const earnings = await this.referralEarningRepository.find({
        where: relationshipIds.map((id) => ({ referral_id: id })),
      });

      const pendingEarnings = earnings
        .filter((e) => !e.paid)
        .reduce((sum, e) => sum + parseFloat(e.amount), 0);

      const paidEarnings = earnings
        .filter((e) => e.paid)
        .reduce((sum, e) => sum + parseFloat(e.amount), 0);

      return {
        directReferrals: level1,
        level2Referrals: level2,
        level3Referrals: level3,
        totalEarned,
        pendingEarnings,
        paidEarnings,
      };
    } catch (error) {
      logger.error('Error getting referral stats', {
        userId,
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        directReferrals: 0,
        level2Referrals: 0,
        level3Referrals: 0,
        totalEarned: 0,
        pendingEarnings: 0,
        paidEarnings: 0,
      };
    }
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
    try {
      const relationships = await this.referralRepository.find();

      const byLevel: Record<number, { count: number; earnings: number }> = {
        1: { count: 0, earnings: 0 },
        2: { count: 0, earnings: 0 },
        3: { count: 0, earnings: 0 },
      };

      let totalEarnings = 0;

      relationships.forEach((r) => {
        byLevel[r.level].count++;
        const earned = parseFloat(r.total_earned);
        byLevel[r.level].earnings += earned;
        totalEarnings += earned;
      });

      // Get all earnings
      const earnings = await this.referralEarningRepository.find();

      const paidEarnings = earnings
        .filter((e) => e.paid)
        .reduce((sum, e) => sum + parseFloat(e.amount), 0);

      const pendingEarnings = earnings
        .filter((e) => !e.paid)
        .reduce((sum, e) => sum + parseFloat(e.amount), 0);

      return {
        totalReferrals: relationships.length,
        totalEarnings,
        paidEarnings,
        pendingEarnings,
        byLevel,
      };
    } catch (error) {
      logger.error('Error getting platform referral stats', {
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        totalReferrals: 0,
        totalEarnings: 0,
        paidEarnings: 0,
        pendingEarnings: 0,
        byLevel: {
          1: { count: 0, earnings: 0 },
          2: { count: 0, earnings: 0 },
          3: { count: 0, earnings: 0 },
        },
      };
    }
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
    const limit = options.limit || 10;

    try {
      // Get all users with their referral counts
      const usersWithReferrals = await this.referralRepository
        .createQueryBuilder('referral')
        .select('referral.referrer_id', 'userId')
        .addSelect('COUNT(DISTINCT referral.referral_id)', 'referralCount')
        .addSelect('SUM(CAST(referral.total_earned AS DECIMAL))', 'totalEarnings')
        .groupBy('referral.referrer_id')
        .having('COUNT(DISTINCT referral.referral_id) > 0')
        .getRawMany();

      // Fetch all users in a single query (fix N+1 query issue)
      const userIds = usersWithReferrals.map((item) => parseInt(item.userId));
      const users = await this.userRepository.findByIds(userIds);

      // Create user lookup map for O(1) access
      const userMap = new Map(users.map((user) => [user.id, user]));

      // Map user data using in-memory lookup
      const leaderboardData = usersWithReferrals.map((item) => {
        const userId = parseInt(item.userId);
        const user = userMap.get(userId);

        return {
          userId,
          username: user?.username,
          telegramId: user?.telegram_id || 0,
          referralCount: parseInt(item.referralCount || '0'),
          totalEarnings: parseFloat(item.totalEarnings || '0'),
        };
      });

      // Sort by referral count
      const byReferrals = [...leaderboardData]
        .sort((a, b) => b.referralCount - a.referralCount)
        .slice(0, limit)
        .map((item, index) => ({
          ...item,
          rank: index + 1,
        }));

      // Sort by earnings
      const byEarnings = [...leaderboardData]
        .sort((a, b) => b.totalEarnings - a.totalEarnings)
        .slice(0, limit)
        .map((item, index) => ({
          ...item,
          rank: index + 1,
        }));

      logger.debug('Referral leaderboard retrieved', {
        byReferralsCount: byReferrals.length,
        byEarningsCount: byEarnings.length,
      });

      return {
        byReferrals,
        byEarnings,
      };
    } catch (error) {
      logger.error('Error getting referral leaderboard', {
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        byReferrals: [],
        byEarnings: [],
      };
    }
  }

  /**
   * Get user's position in leaderboard
   */
  async getUserLeaderboardPosition(userId: number): Promise<{
    referralRank: number | null;
    earningsRank: number | null;
    totalUsers: number;
  }> {
    try {
      const leaderboard = await this.getReferralLeaderboard({ limit: 1000 });

      const referralRank = leaderboard.byReferrals.findIndex(
        (item) => item.userId === userId
      );
      const earningsRank = leaderboard.byEarnings.findIndex(
        (item) => item.userId === userId
      );

      return {
        referralRank: referralRank >= 0 ? referralRank + 1 : null,
        earningsRank: earningsRank >= 0 ? earningsRank + 1 : null,
        totalUsers: leaderboard.byReferrals.length,
      };
    } catch (error) {
      logger.error('Error getting user leaderboard position', {
        userId,
        error: error instanceof Error ? error.message : String(error),
      });
      return {
        referralRank: null,
        earningsRank: null,
        totalUsers: 0,
      };
    }
  }
}

export default new ReferralStatsService();
