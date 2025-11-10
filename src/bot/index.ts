/**
 * Telegram Bot Main Module
 * Initializes and configures the Telegraf bot instance
 */

import { Telegraf } from 'telegraf';
import { config } from '../config';
import { createLogger } from '../utils/logger.util';

// Middlewares
import {
  loggerMiddleware,
  sessionMiddleware,
  authMiddleware,
  banMiddleware,
  adminMiddleware,
  rateLimitMiddleware,
  registrationRateLimitMiddleware,
} from './middlewares';

// Handlers
import {
  handleStart,
  handleMainMenu,
  handleHelp,
  handleStartRegistration,
  handleWalletInput,
  handleStartVerification,
  handleAddContactInfo,
  handleContactInfoInput,
  handleSkipContactInfo,
  handleCancelRegistration,
  handleProfile,
} from './handlers';

// Context types
import { AuthContext } from './middlewares/auth.middleware';
import { SessionContext } from './middlewares/session.middleware';
import { AdminContext } from './middlewares/admin.middleware';
import { BotState } from '../utils/constants';

const logger = createLogger('TelegramBot');

// Extended context type
export type BotContext = AuthContext & SessionContext & AdminContext;

/**
 * Initialize Telegram bot
 */
export const initializeBot = (): Telegraf => {
  const bot = new Telegraf(config.telegram.botToken);

  // Apply global middlewares
  bot.use(loggerMiddleware);
  bot.use(rateLimitMiddleware);
  bot.use(sessionMiddleware);
  bot.use(authMiddleware);
  bot.use(banMiddleware);
  bot.use(adminMiddleware);

  // ==================== COMMANDS ====================

  /**
   * /start command
   * Entry point for all users
   */
  bot.command('start', handleStart);

  /**
   * /help command
   */
  bot.command('help', handleHelp);

  // ==================== CALLBACK QUERIES ====================

  /**
   * Main menu
   */
  bot.action('main_menu', handleMainMenu);

  /**
   * Help
   */
  bot.action('help', handleHelp);

  /**
   * Registration flow
   */
  bot.action('start_registration', registrationRateLimitMiddleware, handleStartRegistration);
  bot.action('start_verification', handleStartVerification);
  bot.action('add_contact_info', handleAddContactInfo);
  bot.action('skip_contact_info', handleSkipContactInfo);
  bot.action('cancel', handleCancelRegistration);

  /**
   * Profile
   */
  bot.action('profile', handleProfile);

  /**
   * Deposits
   * TODO: Implement deposit handlers
   */
  bot.action('deposits', async (ctx) => {
    await ctx.answerCbQuery('Функция депозитов в разработке');
    await ctx.reply('💰 Депозиты\n\nЭта функция будет доступна в ближайшее время.');
  });

  /**
   * Referrals
   * TODO: Implement referral handlers
   */
  bot.action('referrals', async (ctx) => {
    await ctx.answerCbQuery('Функция рефералов в разработке');
    await ctx.reply('🤝 Рефералы\n\nЭта функция будет доступна в ближайшее время.');
  });

  /**
   * Admin panel
   * TODO: Implement admin handlers
   */
  bot.action('admin_panel', async (ctx) => {
    const adminCtx = ctx as AdminContext;

    if (!adminCtx.isAdmin) {
      await ctx.answerCbQuery('Доступ запрещен');
      return;
    }

    await ctx.answerCbQuery('Админ-панель в разработке');
    await ctx.reply('👑 Админ-панель\n\nЭта функция будет доступна в ближайшее время.');
  });

  /**
   * No-op action (for non-clickable buttons)
   */
  bot.action('noop', async (ctx) => {
    await ctx.answerCbQuery();
  });

  // ==================== TEXT MESSAGES ====================

  /**
   * Handle text messages based on session state
   */
  bot.on('text', async (ctx) => {
    const sessionCtx = ctx as SessionContext;

    switch (sessionCtx.session.state) {
      case BotState.AWAITING_WALLET_ADDRESS:
        await handleWalletInput(ctx);
        break;

      case BotState.AWAITING_CONTACT_INFO:
        await handleContactInfoInput(ctx);
        break;

      default:
        // Unknown text message
        await ctx.reply(
          'Используйте кнопки меню для навигации или команду /help для помощи.'
        );
    }
  });

  // ==================== ERROR HANDLING ====================

  /**
   * Global error handler
   */
  bot.catch((err, ctx) => {
    logger.error('Bot error', {
      error: err instanceof Error ? err.message : String(err),
      stack: err instanceof Error ? err.stack : undefined,
      updateType: ctx.updateType,
      userId: ctx.from?.id,
    });

    // Try to notify user
    ctx.reply('❌ Произошла ошибка. Пожалуйста, попробуйте позже.').catch(() => {
      // Ignore if can't send message
    });
  });

  logger.info('Telegram bot initialized');

  return bot;
};

/**
 * Start bot with webhook or polling
 */
export const startBot = async (bot: Telegraf): Promise<void> => {
  if (config.telegram.webhookUrl) {
    // Webhook mode (for production)
    await bot.telegram.setWebhook(config.telegram.webhookUrl, {
      secret_token: config.telegram.webhookSecret,
    });

    logger.info('Bot started in webhook mode', {
      webhookUrl: config.telegram.webhookUrl,
    });
  } else {
    // Polling mode (for development)
    await bot.launch();

    logger.info('Bot started in polling mode');

    // Enable graceful stop
    process.once('SIGINT', () => bot.stop('SIGINT'));
    process.once('SIGTERM', () => bot.stop('SIGTERM'));
  }
};

/**
 * Stop bot gracefully
 */
export const stopBot = async (bot: Telegraf): Promise<void> => {
  logger.info('Stopping bot...');
  await bot.stop();
  logger.info('Bot stopped');
};

export default {
  initializeBot,
  startBot,
  stopBot,
};
