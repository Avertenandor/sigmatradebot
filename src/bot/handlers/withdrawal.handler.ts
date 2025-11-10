/**
 * Withdrawal Handler
 * Handles withdrawal requests
 */

import { Context } from 'telegraf';
import { Markup } from 'telegraf';
import { AuthContext } from '../middlewares/auth.middleware';
import { SessionContext, updateSessionState } from '../middlewares/session.middleware';
import { BotState } from '../../utils/constants';
import { getBackButton } from '../keyboards';
import userService from '../../services/user.service';
import withdrawalService from '../../services/withdrawal.service';
import { createLogger } from '../../utils/logger.util';

const logger = createLogger('WithdrawalHandler');

/**
 * Handle withdrawals menu
 */
export const handleWithdrawals = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get user balance
  const balance = await userService.getUserBalance(authCtx.user.id);

  const minAmount = withdrawalService.getMinWithdrawalAmount();

  const message = `
💸 **Вывод средств**

**Ваш баланс:**
💰 Доступно для вывода: **${balance?.availableBalance.toFixed(2) || 0} USDT**
⏳ В ожидании выплаты: ${balance?.pendingEarnings.toFixed(2) || 0} USDT

**Условия вывода:**
• Минимальная сумма: ${minAmount} USDT
• Вывод на ваш кошелек: \`${authCtx.user.wallet_address}\`
• Обработка: 15-30 минут

${balance && balance.availableBalance >= minAmount ? '✅ Вы можете запросить вывод' : '❌ Недостаточно средств для вывода'}
  `.trim();

  const buttons: any[][] = [];

  // Add request withdrawal button if balance is sufficient
  if (balance && balance.availableBalance >= minAmount) {
    buttons.push([
      Markup.button.callback('💸 Запросить вывод', 'request_withdrawal'),
    ]);
  }

  // Add withdrawal history button
  buttons.push([
    Markup.button.callback('📜 История выводов', 'withdrawal_history'),
  ]);

  // Add back button
  buttons.push([
    Markup.button.callback('🔙 Назад', 'main_menu'),
  ]);

  if (ctx.callbackQuery && 'message' in ctx.callbackQuery) {
    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });
  } else {
    await ctx.reply(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });
  }

  if (ctx.callbackQuery) {
    await ctx.answerCbQuery();
  }

  logger.debug('Withdrawals menu shown', {
    userId: authCtx.user.id,
    availableBalance: balance?.availableBalance || 0,
  });
};

/**
 * Handle request withdrawal
 */
export const handleRequestWithdrawal = async (ctx: Context) => {
  const authCtx = ctx as AuthContext & SessionContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get user balance
  const balance = await userService.getUserBalance(authCtx.user.id);
  const minAmount = withdrawalService.getMinWithdrawalAmount();

  if (!balance || balance.availableBalance < minAmount) {
    await ctx.answerCbQuery('Недостаточно средств для вывода');
    return;
  }

  // Update session state
  await updateSessionState(ctx.from!.id, BotState.AWAITING_WITHDRAWAL_AMOUNT);

  const message = `
💸 **Запрос на вывод**

Доступно для вывода: **${balance.availableBalance.toFixed(2)} USDT**
Минимальная сумма: ${minAmount} USDT

Укажите сумму для вывода (в USDT):
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...Markup.inlineKeyboard([
      [Markup.button.callback('❌ Отмена', 'withdrawals')],
    ]),
  });

  await ctx.answerCbQuery();

  logger.debug('Withdrawal request started', {
    userId: authCtx.user.id,
  });
};

/**
 * Handle withdrawal amount input
 */
export const handleWithdrawalAmountInput = async (ctx: Context) => {
  const authCtx = ctx as AuthContext & SessionContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.reply('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Check session state
  if (authCtx.session?.state !== BotState.AWAITING_WITHDRAWAL_AMOUNT) {
    return;
  }

  const input = ctx.text?.trim();
  if (!input) {
    await ctx.reply('Пожалуйста, укажите сумму');
    return;
  }

  // Parse amount
  const amount = parseFloat(input);
  if (isNaN(amount) || amount <= 0) {
    await ctx.reply('Неверный формат суммы. Укажите число больше 0');
    return;
  }

  // Request withdrawal
  const { transaction, error } = await withdrawalService.requestWithdrawal({
    userId: authCtx.user.id,
    amount,
  });

  if (error) {
    await ctx.reply(`❌ Ошибка: ${error}`, {
      ...Markup.inlineKeyboard([
        [Markup.button.callback('🔙 Назад', 'withdrawals')],
      ]),
    });
    await updateSessionState(ctx.from!.id, BotState.IDLE);
    return;
  }

  const successMessage = `
✅ **Заявка на вывод создана!**

💰 Сумма: ${amount.toFixed(2)} USDT
🆔 ID заявки: ${transaction?.id}
💳 Кошелек: \`${authCtx.user.wallet_address}\`

Заявка принята в обработку.
Средства будут отправлены в течение 15-30 минут.

Вы получите уведомление когда вывод будет выполнен.
  `.trim();

  await ctx.reply(successMessage, {
    parse_mode: 'Markdown',
    ...Markup.inlineKeyboard([
      [Markup.button.callback('📜 История выводов', 'withdrawal_history')],
      [Markup.button.callback('🔙 Главное меню', 'main_menu')],
    ]),
  });

  // Reset session state
  await updateSessionState(ctx.from!.id, BotState.IDLE);

  logger.info('Withdrawal request created', {
    userId: authCtx.user.id,
    transactionId: transaction?.id,
    amount,
  });
};

/**
 * Handle withdrawal history
 */
export const handleWithdrawalHistory = async (ctx: Context) => {
  const authCtx = ctx as AuthContext;

  if (!authCtx.isRegistered || !authCtx.user) {
    await ctx.answerCbQuery('Пожалуйста, сначала зарегистрируйтесь');
    return;
  }

  // Get page from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const page = parseInt(callbackData.split('_').pop() || '1', 10);

  // Get withdrawal history
  const { withdrawals, total, pages } = await withdrawalService.getUserWithdrawals(
    authCtx.user.id,
    { page, limit: 5 }
  );

  let message = `📜 **История выводов**\n\n`;

  if (withdrawals.length === 0) {
    message += 'У вас пока нет выводов.';
  } else {
    withdrawals.forEach((withdrawal, index) => {
      const emoji =
        withdrawal.status === 'confirmed'
          ? '✅'
          : withdrawal.status === 'pending'
          ? '⏳'
          : '❌';
      const date = new Date(withdrawal.created_at).toLocaleDateString('ru-RU');

      message += `${emoji} **${parseFloat(withdrawal.amount).toFixed(2)} USDT**\n`;
      message += `Дата: ${date}\n`;
      message += `Статус: ${withdrawal.status}\n`;

      if (withdrawal.tx_hash) {
        message += `TX: \`${withdrawal.tx_hash.substring(0, 10)}...${withdrawal.tx_hash.substring(withdrawal.tx_hash.length - 6)}\`\n`;
      }

      message += '\n';
    });

    message += `📊 Всего выводов: ${total}`;
  }

  const buttons: any[][] = [];

  // Add pagination if needed
  if (pages > 1) {
    const navButtons = [];
    if (page > 1) {
      navButtons.push(
        Markup.button.callback('⬅️ Назад', `withdrawal_history_${page - 1}`)
      );
    }
    navButtons.push(
      Markup.button.callback(`${page}/${pages}`, 'noop')
    );
    if (page < pages) {
      navButtons.push(
        Markup.button.callback('Вперед ➡️', `withdrawal_history_${page + 1}`)
      );
    }
    buttons.push(navButtons);
  }

  buttons.push([
    Markup.button.callback('🔙 Назад', 'withdrawals'),
  ]);

  if (ctx.callbackQuery && 'message' in ctx.callbackQuery) {
    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });
  } else {
    await ctx.reply(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });
  }

  if (ctx.callbackQuery) {
    await ctx.answerCbQuery();
  }

  logger.debug('Withdrawal history shown', {
    userId: authCtx.user.id,
    page,
    totalWithdrawals: total,
  });
};

export default {
  handleWithdrawals,
  handleRequestWithdrawal,
  handleWithdrawalAmountInput,
  handleWithdrawalHistory,
};
