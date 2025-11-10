/**
 * Admin Panel Handler
 * Handles admin panel main menu and statistics
 */

import { Context } from 'telegraf';
import { AdminContext } from '../../middlewares/admin.middleware';
import { getAdminPanelKeyboard, getAdminStatsKeyboard } from '../../keyboards';
import { ERROR_MESSAGES } from '../../../utils/constants';
import userService from '../../../services/user.service';
import depositService from '../../../services/deposit.service';
import referralService from '../../../services/referral.service';
import { logAdminAction } from '../../../utils/logger.util';
import { requireAuthenticatedAdmin } from './utils';

/**
 * Handle admin panel main menu
 */
export const handleAdminPanel = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  const message = `
👑 **Панель администратора**

Добро пожаловать в панель управления SigmaTrade Bot.

Выберите действие:
  `.trim();

  if (ctx.callbackQuery && 'message' in ctx.callbackQuery) {
    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...getAdminPanelKeyboard(),
    });
  } else {
    await ctx.reply(message, {
      parse_mode: 'Markdown',
      ...getAdminPanelKeyboard(),
    });
  }

  if (ctx.callbackQuery) {
    await ctx.answerCbQuery();
  }

  logAdminAction(ctx.from!.id, 'opened_admin_panel');
};

/**
 * Handle platform statistics
 */
export const handleAdminStats = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  // Get range from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const range = callbackData.split('_').pop() || 'all';

  // Get statistics
  const totalUsers = await userService.getTotalUsers();
  const verifiedUsers = await userService.getVerifiedUsers();
  const depositStats = await depositService.getPlatformStats();
  const referralStats = await referralService.getPlatformReferralStats();

  const message = `
📊 **Статистика платформы**

**Пользователи:**
👥 Всего: ${totalUsers}
✅ Верифицированы: ${verifiedUsers}
❌ Не верифицированы: ${totalUsers - verifiedUsers}

**Депозиты:**
💰 Всего депозитов: ${depositStats.totalDeposits}
💵 Общая сумма: ${depositStats.totalAmount.toFixed(2)} USDT
👤 Пользователей с депозитами: ${depositStats.totalUsers}

**По уровням:**
• Уровень 1: ${depositStats.depositsByLevel[1]} депозитов
• Уровень 2: ${depositStats.depositsByLevel[2]} депозитов
• Уровень 3: ${depositStats.depositsByLevel[3]} депозитов
• Уровень 4: ${depositStats.depositsByLevel[4]} депозитов
• Уровень 5: ${depositStats.depositsByLevel[5]} депозитов

**Рефералы:**
🤝 Всего связей: ${referralStats.totalReferrals}
💰 Всего начислено: ${referralStats.totalEarnings.toFixed(2)} USDT
✅ Выплачено: ${referralStats.paidEarnings.toFixed(2)} USDT
⏳ Ожидает выплаты: ${referralStats.pendingEarnings.toFixed(2)} USDT

**По уровням:**
• Уровень 1: ${referralStats.byLevel[1].count} (${referralStats.byLevel[1].earnings.toFixed(2)} USDT)
• Уровень 2: ${referralStats.byLevel[2].count} (${referralStats.byLevel[2].earnings.toFixed(2)} USDT)
• Уровень 3: ${referralStats.byLevel[3].count} (${referralStats.byLevel[3].earnings.toFixed(2)} USDT)
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getAdminStatsKeyboard(range),
  });

  await ctx.answerCbQuery();

  logAdminAction(ctx.from!.id, 'viewed_stats', { range });
};
