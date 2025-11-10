/**
 * Reward Calculator Job
 * Automatically calculates rewards for active reward sessions
 * Runs every hour to process all active sessions
 */

import { Job } from 'bull';
import { getQueue, QueueName } from './queue.config';
import rewardService from '../services/reward.service';
import { config } from '../config';
import { logger } from '../utils/logger.util';

export interface RewardCalculatorJobData {
  timestamp: number;
  sessionId?: number; // Optional - calculate specific session
}

/**
 * Calculate rewards for active sessions
 */
export const calculateRewards = async (
  job: Job<RewardCalculatorJobData>
): Promise<void> => {
  try {
    logger.debug('💰 Running reward calculator job...');

    const { sessionId } = job.data;

    // If specific session ID provided, calculate only that session
    if (sessionId) {
      logger.info(`Calculating rewards for session #${sessionId}`);

      const result = await rewardService.calculateRewardsForSession(sessionId);

      if (!result.success) {
        logger.error(`Failed to calculate rewards for session #${sessionId}: ${result.error}`);
        throw new Error(result.error);
      }

      logger.info(
        `✅ Rewards calculated for session #${sessionId}: ${result.rewardsCalculated} rewards, ${result.totalRewardAmount?.toFixed(2)} USDT`
      );

      return;
    }

    // Otherwise, calculate for all active sessions
    const activeSessions = await rewardService.getActiveSessions();

    if (activeSessions.length === 0) {
      logger.debug('ℹ️ No active reward sessions to process');
      return;
    }

    logger.info(`Found ${activeSessions.length} active reward sessions to process`);

    let totalRewardsCalculated = 0;
    let totalRewardAmount = 0;
    let sessionsProcessed = 0;
    let sessionsFailed = 0;

    for (const session of activeSessions) {
      try {
        logger.debug(`Processing session #${session.id}: ${session.name}`);

        const result = await rewardService.calculateRewardsForSession(session.id);

        if (result.success) {
          totalRewardsCalculated += result.rewardsCalculated || 0;
          totalRewardAmount += result.totalRewardAmount || 0;
          sessionsProcessed++;

          if ((result.rewardsCalculated || 0) > 0) {
            logger.info(
              `✅ Session #${session.id} (${session.name}): ${result.rewardsCalculated} rewards, ${result.totalRewardAmount?.toFixed(2)} USDT`
            );
          } else {
            logger.debug(`ℹ️ Session #${session.id} (${session.name}): No new rewards to calculate`);
          }
        } else {
          sessionsFailed++;
          logger.error(
            `❌ Failed to calculate rewards for session #${session.id} (${session.name}): ${result.error}`
          );
        }
      } catch (error) {
        sessionsFailed++;
        logger.error(
          `❌ Error processing session #${session.id} (${session.name}):`,
          error
        );
      }
    }

    if (totalRewardsCalculated > 0) {
      logger.info(
        `✅ Reward calculator completed: ${totalRewardsCalculated} rewards calculated, ` +
        `${totalRewardAmount.toFixed(2)} USDT total. ` +
        `Processed: ${sessionsProcessed}, Failed: ${sessionsFailed}`
      );
    } else {
      logger.debug('ℹ️ No new rewards calculated in this run');
    }
  } catch (error) {
    logger.error('❌ Reward calculator job failed:', error);
    throw error; // Let Bull handle retries
  }
};

/**
 * Start reward calculator
 */
export const startRewardCalculator = async (): Promise<void> => {
  if (!config.jobs.rewardCalculator?.enabled) {
    logger.warn('⚠️ Reward calculator is disabled');
    return;
  }

  try {
    const queue = getQueue(QueueName.REWARD_CALCULATOR);

    // Add repeating job (every hour by default)
    const interval = config.jobs.rewardCalculator.intervalMinutes * 60 * 1000;

    await queue.add(
      'calculate-rewards',
      { timestamp: Date.now() },
      {
        repeat: {
          every: interval,
        },
        removeOnComplete: 5,
        removeOnFail: false,
      }
    );

    // Process jobs
    queue.process('calculate-rewards', calculateRewards);

    logger.info(
      `✅ Reward calculator started (running every ${config.jobs.rewardCalculator.intervalMinutes} minutes)`
    );
  } catch (error) {
    logger.error('❌ Failed to start reward calculator:', error);
    throw error;
  }
};

/**
 * Stop reward calculator
 */
export const stopRewardCalculator = async (): Promise<void> => {
  try {
    const queue = getQueue(QueueName.REWARD_CALCULATOR);
    const interval = config.jobs.rewardCalculator?.intervalMinutes * 60 * 1000 || 3600000;

    await queue.removeRepeatable('calculate-rewards', {
      every: interval,
    });

    logger.info('✅ Reward calculator stopped');
  } catch (error) {
    logger.error('❌ Error stopping reward calculator:', error);
  }
};

/**
 * Manually trigger reward calculation (for admin panel)
 */
export const triggerRewardCalculation = async (sessionId?: number): Promise<{
  rewardsCalculated: number;
  totalRewardAmount: number;
  error?: string;
}> => {
  try {
    logger.info('🔄 Manual reward calculation triggered', { sessionId });

    const queue = getQueue(QueueName.REWARD_CALCULATOR);

    // Add one-time job
    const job = await queue.add('manual-calculate-rewards', {
      timestamp: Date.now(),
      sessionId,
    });

    // Wait for job to complete (with timeout)
    await job.finished();

    if (sessionId) {
      // Get results for specific session
      const result = await rewardService.calculateRewardsForSession(sessionId);
      return {
        rewardsCalculated: result.rewardsCalculated || 0,
        totalRewardAmount: result.totalRewardAmount || 0,
        error: result.error,
      };
    } else {
      // For all sessions, we can't easily get aggregated results
      // Return a success indicator
      return {
        rewardsCalculated: 0,
        totalRewardAmount: 0,
      };
    }
  } catch (error) {
    logger.error('❌ Manual reward calculation failed:', error);
    return {
      rewardsCalculated: 0,
      totalRewardAmount: 0,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};
