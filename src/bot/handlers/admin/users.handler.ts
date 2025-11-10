/**
 * Admin Users Handler
 * Handles user management (ban/unban)
 */

import { Context } from 'telegraf';
import { AdminContext } from '../../middlewares/admin.middleware';
import { SessionContext, updateSessionState } from '../../middlewares/session.middleware';
import { getCancelButton } from '../../keyboards';
import { BotState, ERROR_MESSAGES } from '../../../utils/constants';
import userService from '../../../services/user.service';
import { logAdminAction } from '../../../utils/logger.util';
import { requireAuthenticatedAdmin } from './utils';

/**
 * Start ban user
 */
export const handleStartBanUser = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  await updateSessionState(
    ctx.from!.id,
    BotState.AWAITING_ADMIN_USER_TO_BAN
  );

  const message = `
🚫 **Блокировка пользователя**

Отправьте username (с @) или Telegram ID пользователя для блокировки.

Пример: \`@username\` или \`123456789\`
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getCancelButton(),
  });

  await ctx.answerCbQuery();
};

/**
 * Handle ban user input
 */
export const handleBanUserInput = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isAdmin) {
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  if (adminCtx.session.state !== BotState.AWAITING_ADMIN_USER_TO_BAN) {
    return;
  }

  const identifier = ctx.text?.trim();

  if (!identifier) {
    await ctx.reply('❌ Отправьте username или ID');
    return;
  }

  // Find user
  let user;

  if (identifier.startsWith('@')) {
    const username = identifier.substring(1);
    user = await userService.findByUsername(username);
  } else if (/^\d+$/.test(identifier)) {
    const telegramId = parseInt(identifier, 10);
    user = await userService.findByTelegramId(telegramId);
  }

  if (!user) {
    await ctx.reply('❌ Пользователь не найден');
    return;
  }

  // Ban user
  const result = await userService.banUser(user.id);

  if (result.success) {
    await ctx.reply(
      `✅ Пользователь ${user.displayName} заблокирован`
    );

    logAdminAction(ctx.from!.id, 'banned_user', {
      targetUserId: user.id,
    });
  } else {
    await ctx.reply(`❌ Ошибка: ${result.error}`);
  }

  // Reset session
  await updateSessionState(ctx.from!.id, BotState.IDLE);
};

/**
 * Start unban user
 */
export const handleStartUnbanUser = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  await updateSessionState(
    ctx.from!.id,
    BotState.AWAITING_ADMIN_USER_TO_UNBAN
  );

  const message = `
✅ **Разблокировка пользователя**

Отправьте username (с @) или Telegram ID пользователя для разблокировки.

Пример: \`@username\` или \`123456789\`
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getCancelButton(),
  });

  await ctx.answerCbQuery();
};

/**
 * Handle unban user input
 */
export const handleUnbanUserInput = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isAdmin) {
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  if (adminCtx.session.state !== BotState.AWAITING_ADMIN_USER_TO_UNBAN) {
    return;
  }

  const identifier = ctx.text?.trim();

  if (!identifier) {
    await ctx.reply('❌ Отправьте username или ID');
    return;
  }

  // Find user
  let user;

  if (identifier.startsWith('@')) {
    const username = identifier.substring(1);
    user = await userService.findByUsername(username);
  } else if (/^\d+$/.test(identifier)) {
    const telegramId = parseInt(identifier, 10);
    user = await userService.findByTelegramId(telegramId);
  }

  if (!user) {
    await ctx.reply('❌ Пользователь не найден');
    return;
  }

  // Unban user
  const result = await userService.unbanUser(user.id);

  if (result.success) {
    await ctx.reply(
      `✅ Пользователь ${user.displayName} разблокирован`
    );

    logAdminAction(ctx.from!.id, 'unbanned_user', {
      targetUserId: user.id,
    });
  } else {
    await ctx.reply(`❌ Ошибка: ${result.error}`);
  }

  // Reset session
  await updateSessionState(ctx.from!.id, BotState.IDLE);
};
