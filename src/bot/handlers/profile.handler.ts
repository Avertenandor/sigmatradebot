/**
 * Profile Handler
 * Handles user profile display
 */

import { Context } from 'telegraf';
import { AuthContext } from '../middlewares/auth.middleware';
import { getBackButton } from '../keyboards';
import userService from '../../services/user.service';
import { createLogger } from '../../utils/logger.util';
import { config } from '../../config';

const logger = createLogger('ProfileHandler');

/**
 * Handle profile view
 */
export const handleProfile = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  const user = authCtx.user;

  // Get user stats
  const stats = await userService.getUserStats(user.id);

  // Get referral link
  const botUsername = (await ctx.telegram.getMe()).username;
  const referralLink = userService.generateReferralLink(user.id, botUsername);

  // Format profile message
  const profileMessage = `
👤 **Ваш профиль**

**Основная информация:**
🆔 ID: \`${user.id}\`
👤 Username: ${user.username ? `@${user.username}` : 'Не указан'}
💳 Кошелек: \`${user.wallet_address}\`
${user.maskedWallet ? `(${user.maskedWallet})` : ''}

**Статус:**
${user.is_verified ? '✅' : '❌'} Верификация: ${user.is_verified ? 'Пройдена' : 'Не пройдена'}
${user.is_banned ? '🚫 Аккаунт заблокирован' : '✅ Аккаунт активен'}

**Контакты:**
${user.phone ? `📞 Телефон: ${user.phone}` : '📞 Телефон: Не указан'}
${user.email ? `📧 Email: ${user.email}` : '📧 Email: Не указан'}

**Статистика:**
💰 Всего депозитов: ${stats?.totalDeposits || 0} USDT
💸 Заработано: ${stats?.totalEarned || 0} USDT
👥 Рефералов: ${stats?.referralCount || 0}
📊 Активных уровней: ${stats?.activatedLevels.length || 0}/5

**Реферальная ссылка:**
\`${referralLink}\`

📅 Дата регистрации: ${new Date(user.created_at).toLocaleDateString('ru-RU')}
  `.trim();

  if (ctx.callbackQuery && 'message' in ctx.callbackQuery) {
    await ctx.editMessageText(profileMessage, {
      parse_mode: 'Markdown',
      ...getBackButton('main_menu'),
    });
  } else {
    await ctx.reply(profileMessage, {
      parse_mode: 'Markdown',
      ...getBackButton('main_menu'),
    });
  }

  if (ctx.callbackQuery) {
    await ctx.answerCbQuery();
  }

  logger.debug('Profile viewed', {
    userId: user.id,
    telegramId: user.telegram_id,
  });
};

export default {
  handleProfile,
};
