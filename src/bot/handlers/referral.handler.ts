/**
 * Referral Handler
 * Handles referral program actions
 */

import { Context } from 'telegraf';
import { AuthContext } from '../middlewares/auth.middleware';
import {
  getReferralMenuKeyboard,
  getReferralStatsKeyboard,
  getReferralEarningsKeyboard,
  getBackButton,
} from '../keyboards';
import referralService from '../../services/referral.service';
import userService from '../../services/user.service';
import { REFERRAL_RATES } from '../../utils/constants';
import { createLogger } from '../../utils/logger.util';

const logger = createLogger('ReferralHandler');

/**
 * Handle referrals menu
 */
export const handleReferrals = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get referral stats
  const stats = await referralService.getReferralStats(authCtx.user.id);

  const message = `
🤝 **Реферальная программа**

**Ваша статистика:**
👥 Прямые партнеры (Уровень 1): ${stats.directReferrals}
👥 Уровень 2: ${stats.level2Referrals}
👥 Уровень 3: ${stats.level3Referrals}

💰 **Доходы:**
💵 Всего заработано: ${stats.totalEarned.toFixed(2)} USDT
⏳ Ожидает выплаты: ${stats.pendingEarnings.toFixed(2)} USDT
✅ Выплачено: ${stats.paidEarnings.toFixed(2)} USDT

**Комиссии:**
• Уровень 1: ${REFERRAL_RATES[1] * 100}% от депозитов прямых партнеров
• Уровень 2: ${REFERRAL_RATES[2] * 100}% от партнеров второго уровня
• Уровень 3: ${REFERRAL_RATES[3] * 100}% от партнеров третьего уровня

📈 Чем больше ваша сеть, тем больше доход!
  `.trim();

  if (ctx.callbackQuery && 'message' in ctx.callbackQuery) {
    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...getReferralMenuKeyboard(),
    });
  } else {
    await ctx.reply(message, {
      parse_mode: 'Markdown',
      ...getReferralMenuKeyboard(),
    });
  }

  if (ctx.callbackQuery) {
    await ctx.answerCbQuery();
  }

  logger.debug('Referrals menu shown', {
    userId: authCtx.user.id,
    stats,
  });
};

/**
 * Handle referral link
 */
export const handleReferralLink = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get bot username
  const botInfo = await ctx.telegram.getMe();
  const referralLink = userService.generateReferralLink(
    authCtx.user.id,
    botInfo.username
  );

  const message = `
🔗 **Ваша реферальная ссылка**

\`${referralLink}\`

**Как использовать:**
1. Скопируйте ссылку
2. Поделитесь с друзьями
3. Получайте вознаграждения от их депозитов!

**Ваши комиссии:**
• ${REFERRAL_RATES[1] * 100}% от депозитов прямых партнеров
• ${REFERRAL_RATES[2] * 100}% от партнеров 2-го уровня
• ${REFERRAL_RATES[3] * 100}% от партнеров 3-го уровня

💡 Отправьте эту ссылку в соцсети, мессенджеры или на форумы!
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getBackButton('referrals'),
  });

  await ctx.answerCbQuery('Ссылка готова к отправке!');

  logger.debug('Referral link shown', {
    userId: authCtx.user.id,
  });
};

/**
 * Handle referral stats by level
 */
export const handleReferralStats = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get level from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const level = parseInt(callbackData.split('_').pop() || '1', 10);

  if (level < 1 || level > 3) {
    await ctx.answerCbQuery('Неверный уровень');
    return;
  }

  // Get referrals for this level
  const { referrals, total } = await referralService.getReferralsByLevel(
    authCtx.user.id,
    level,
    { page: 1, limit: 5 }
  );

  let message = `
📊 **Рефералы: Уровень ${level}**

**Комиссия:** ${REFERRAL_RATES[level as keyof typeof REFERRAL_RATES] * 100}%

`;

  if (referrals.length === 0) {
    message += `У вас пока нет партнеров на уровне ${level}.`;
  } else {
    referrals.forEach((ref, index) => {
      const joinDate = new Date(ref.joinedAt).toLocaleDateString('ru-RU');
      message += `${index + 1}. ${ref.user.displayName}\n`;
      message += `   💰 Заработано: ${ref.earned.toFixed(2)} USDT\n`;
      message += `   📅 Присоединился: ${joinDate}\n\n`;
    });

    message += `\n👥 Всего партнеров: ${total}`;

    if (total > 5) {
      message += `\n📄 Показаны первые 5`;
    }
  }

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getReferralStatsKeyboard(level),
  });

  await ctx.answerCbQuery();

  logger.debug('Referral stats shown', {
    userId: authCtx.user.id,
    level,
    totalReferrals: total,
  });
};

/**
 * Handle referral earnings
 */
export const handleReferralEarnings = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get page from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const page = parseInt(callbackData.split('_').pop() || '1', 10);

  // Get pending earnings
  const { earnings, total, totalAmount, pages } = await referralService.getPendingEarnings(
    authCtx.user.id,
    { page, limit: 5 }
  );

  let message = `💸 **Ожидающие выплаты**\n\n`;

  if (earnings.length === 0) {
    message += 'У вас пока нет ожидающих выплат.';
  } else {
    earnings.forEach((earning, index) => {
      const date = new Date(earning.created_at).toLocaleDateString('ru-RU');
      const emoji = earning.paid ? '✅' : '⏳';

      message += `${emoji} ${earning.amountAsNumber.toFixed(2)} USDT\n`;
      message += `Дата: ${date}\n`;
      message += `Статус: ${earning.paid ? 'Выплачено' : 'Ожидает'}\n\n`;
    });

    message += `\n💰 Всего ожидает: ${totalAmount.toFixed(2)} USDT`;
    message += `\n📊 Всего записей: ${total}`;
  }

  const keyboard = getReferralEarningsKeyboard(page, pages);

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...keyboard,
  });

  await ctx.answerCbQuery();

  logger.debug('Referral earnings shown', {
    userId: authCtx.user.id,
    page,
    totalEarnings: total,
    totalAmount,
  });
};

export default {
  handleReferrals,
  handleReferralLink,
  handleReferralStats,
  handleReferralEarnings,
};
