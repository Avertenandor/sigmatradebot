/**
 * Admin Withdrawals Handler
 * Handles withdrawal approval and rejection
 */

import { Context } from 'telegraf';
import { Markup } from 'telegraf';
import { AdminContext } from '../../middlewares/admin.middleware';
import { ERROR_MESSAGES } from '../../../utils/constants';
import userService from '../../../services/user.service';
import withdrawalService from '../../../services/withdrawal.service';
import { notificationService } from '../../../services/notification.service';
import { blockchainService } from '../../../services/blockchain.service';
import { createLogger, logAdminAction } from '../../../utils/logger.util';
import { requireAuthenticatedAdmin } from './utils';

const logger = createLogger('AdminWithdrawalsHandler');

/**
 * Handle pending withdrawals list (admin only)
 */
export const handlePendingWithdrawals = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  try {
    const pendingWithdrawals = await withdrawalService.getPendingWithdrawals();

    let message = `💸 **Ожидающие заявки на вывод**\n\n`;

    if (pendingWithdrawals.length === 0) {
      message += 'Нет ожидающих заявок.';
      await ctx.editMessageText(message, {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('◀️ Назад', 'admin_panel')],
        ]),
      });
      await ctx.answerCbQuery();
      return;
    }

    message += `Всего заявок: **${pendingWithdrawals.length}**\n\n`;

    pendingWithdrawals.forEach((withdrawal, index) => {
      const date = new Date(withdrawal.created_at).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });

      message += `**${index + 1}. Заявка #${withdrawal.id}**\n`;
      message += `💰 Сумма: ${parseFloat(withdrawal.amount).toFixed(2)} USDT\n`;
      message += `👤 Пользователь ID: ${withdrawal.user_id}\n`;
      if (withdrawal.user?.username) {
        message += `📱 @${withdrawal.user.username}\n`;
      }
      message += `💳 Кошелек: \`${withdrawal.to_address}\`\n`;
      message += `📅 Дата: ${date}\n`;
      message += `\n`;
    });

    const buttons: any[][] = [];

    // Add approve/reject buttons for each withdrawal (first 5)
    const displayCount = Math.min(pendingWithdrawals.length, 5);
    for (let i = 0; i < displayCount; i++) {
      const withdrawal = pendingWithdrawals[i];
      buttons.push([
        Markup.button.callback(
          `✅ #${withdrawal.id} Одобрить`,
          `admin_approve_withdrawal_${withdrawal.id}`
        ),
        Markup.button.callback(
          `❌ #${withdrawal.id} Отклонить`,
          `admin_reject_withdrawal_${withdrawal.id}`
        ),
      ]);
    }

    buttons.push([Markup.button.callback('◀️ Назад', 'admin_panel')]);

    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });

    await ctx.answerCbQuery();

    logAdminAction(ctx.from!.id, 'view_pending_withdrawals', {
      count: pendingWithdrawals.length,
    });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при загрузке заявок');
    logger.error('Failed to get pending withdrawals', {
      adminId: ctx.from!.id,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};

/**
 * Handle approve withdrawal (admin only)
 */
export const handleApproveWithdrawal = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  // Extract withdrawal ID from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const match = callbackData.match(/^admin_approve_withdrawal_(\d+)$/);

  if (!match) {
    await ctx.answerCbQuery('❌ Неверный формат');
    return;
  }

  const withdrawalId = parseInt(match[1]);

  try {
    // Get withdrawal details
    const withdrawal = await withdrawalService.getWithdrawalById(withdrawalId);

    if (!withdrawal) {
      await ctx.answerCbQuery('❌ Заявка не найдена');
      return;
    }

    // Send real blockchain transaction
    const paymentResult = await blockchainService.sendPayment(
      withdrawal.to_address,
      parseFloat(withdrawal.amount)
    );

    if (!paymentResult.success) {
      await ctx.answerCbQuery(`❌ Ошибка отправки: ${paymentResult.error || 'Неизвестная ошибка'}`);
      logger.error('Failed to send withdrawal payment', {
        withdrawalId,
        error: paymentResult.error,
      });
      return;
    }

    const txHash = paymentResult.txHash!;
    const { success, error } = await withdrawalService.approveWithdrawal(withdrawalId, txHash);

    if (!success) {
      await ctx.answerCbQuery(`❌ Ошибка: ${error}`);
      return;
    }

    // Send notification to user about withdrawal approval
    const user = await userService.findById(withdrawal.user_id);
    if (user) {
      await notificationService.notifyWithdrawalProcessed(
        user.telegram_id,
        parseFloat(withdrawal.amount),
        txHash
      ).catch((err) => {
        logger.error('Failed to send withdrawal processed notification', { error: err });
      });
    }

    await ctx.answerCbQuery('✅ Заявка одобрена!');

    // Update message
    await ctx.editMessageText(
      `✅ **Заявка #${withdrawalId} одобрена**\n\n` +
      `💰 Сумма: ${parseFloat(withdrawal.amount).toFixed(2)} USDT\n` +
      `👤 Пользователь ID: ${withdrawal.user_id}\n` +
      `💳 Кошелек: \`${withdrawal.to_address}\`\n` +
      `🔗 TX: \`${txHash}\`\n\n` +
      `Средства отправлены пользователю.`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('📋 Список заявок', 'admin_pending_withdrawals')],
          [Markup.button.callback('◀️ Админ-панель', 'admin_panel')],
        ]),
      }
    );

    logAdminAction(ctx.from!.id, 'approve_withdrawal', {
      withdrawalId,
      userId: withdrawal.user_id,
      amount: withdrawal.amount,
    });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при обработке');
    logger.error('Failed to approve withdrawal', {
      adminId: ctx.from!.id,
      withdrawalId,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};

/**
 * Handle reject withdrawal (admin only)
 */
export const handleRejectWithdrawal = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isAdmin) {
    await ctx.answerCbQuery(ERROR_MESSAGES.ADMIN_ONLY);
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  // Extract withdrawal ID from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const match = callbackData.match(/^admin_reject_withdrawal_(\d+)$/);

  if (!match) {
    await ctx.answerCbQuery('❌ Неверный формат');
    return;
  }

  const withdrawalId = parseInt(match[1]);

  try {
    // Get withdrawal details
    const withdrawal = await withdrawalService.getWithdrawalById(withdrawalId);

    if (!withdrawal) {
      await ctx.answerCbQuery('❌ Заявка не найдена');
      return;
    }

    const { success, error } = await withdrawalService.rejectWithdrawal(withdrawalId);

    if (!success) {
      await ctx.answerCbQuery(`❌ Ошибка: ${error}`);
      return;
    }

    // Send notification to user about withdrawal rejection
    const user = await userService.findById(withdrawal.user_id);
    if (user) {
      await notificationService.notifyWithdrawalRejected(
        user.telegram_id,
        parseFloat(withdrawal.amount)
      ).catch((err) => {
        logger.error('Failed to send withdrawal rejected notification', { error: err });
      });
    }

    await ctx.answerCbQuery('✅ Заявка отклонена');

    // Update message
    await ctx.editMessageText(
      `❌ **Заявка #${withdrawalId} отклонена**\n\n` +
      `💰 Сумма: ${parseFloat(withdrawal.amount).toFixed(2)} USDT\n` +
      `👤 Пользователь ID: ${withdrawal.user_id}\n` +
      `💳 Кошелек: \`${withdrawal.to_address}\`\n\n` +
      `Средства возвращены на баланс пользователя.`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('📋 Список заявок', 'admin_pending_withdrawals')],
          [Markup.button.callback('◀️ Админ-панель', 'admin_panel')],
        ]),
      }
    );

    logAdminAction(ctx.from!.id, 'reject_withdrawal', {
      withdrawalId,
      userId: withdrawal.user_id,
      amount: withdrawal.amount,
    });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при обработке');
    logger.error('Failed to reject withdrawal', {
      adminId: ctx.from!.id,
      withdrawalId,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};
