/**
 * Admin Management Handler
 * Handles admin creation, listing, removal, and key regeneration
 */

import { Context } from 'telegraf';
import { Markup } from 'telegraf';
import { AdminContext } from '../../middlewares/admin.middleware';
import { SessionContext, updateSessionState } from '../../middlewares/session.middleware';
import { getCancelButton } from '../../keyboards';
import { BotState } from '../../../utils/constants';
import adminService from '../../../services/admin.service';
import { createLogger, logAdminAction } from '../../../utils/logger.util';
import { requireAuthenticatedAdmin } from './utils';

const logger = createLogger('AdminManagementHandler');

/**
 * Start promote admin
 */
export const handleStartPromoteAdmin = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isSuperAdmin) {
    await ctx.answerCbQuery('Только главный администратор может назначать админов');
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  await updateSessionState(
    ctx.from!.id,
    BotState.AWAITING_ADMIN_USER_TO_PROMOTE
  );

  const message = `
👑 **Назначить администратора**

Отправьте Telegram ID пользователя для назначения администратором.

Пример: \`123456789\`
  `.trim();

  await ctx.editMessageText(message, {
    parse_mode: 'Markdown',
    ...getCancelButton(),
  });

  await ctx.answerCbQuery();
};

/**
 * Handle promote admin input
 */
export const handlePromoteAdminInput = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext & SessionContext;

  if (!adminCtx.isSuperAdmin) {
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  if (adminCtx.session.state !== BotState.AWAITING_ADMIN_USER_TO_PROMOTE) {
    return;
  }

  const input = ctx.text?.trim();

  if (!input) {
    await ctx.reply('❌ Отправьте корректные данные');
    return;
  }

  // Parse format: telegramId [username] [role]
  // Example: "123456789 @username admin" or "123456789 admin" or "123456789"
  const parts = input.split(' ').filter(p => p.length > 0);

  if (parts.length === 0 || !/^\d+$/.test(parts[0])) {
    await ctx.reply(
      '❌ Неверный формат.\n\n' +
      'Правильный формат: `telegramId [@username] [role]`\n\n' +
      'Примеры:\n' +
      '• `123456789` - создать обычного админа\n' +
      '• `123456789 admin` - создать обычного админа\n' +
      '• `123456789 super_admin` - создать главного админа\n' +
      '• `123456789 @username admin` - с указанием username',
      { parse_mode: 'Markdown' }
    );
    return;
  }

  const telegramId = parseInt(parts[0], 10);

  // Determine username and role from remaining parts
  let username: string | undefined;
  let role: 'admin' | 'super_admin' = 'admin';

  for (let i = 1; i < parts.length; i++) {
    const part = parts[i];
    if (part.startsWith('@')) {
      username = part.substring(1);
    } else if (part === 'admin' || part === 'super_admin') {
      role = part as 'admin' | 'super_admin';
    }
  }

  await ctx.reply('⏳ Создаю администратора...');

  // Create admin with master key
  const { admin, masterKey, error } = await adminService.createAdmin({
    telegramId,
    username,
    role,
    createdBy: adminCtx.admin?.id || ctx.from!.id,
  });

  if (error || !admin || !masterKey) {
    await ctx.reply(`❌ Ошибка: ${error || 'Не удалось создать администратора'}`);
    logger.error('Failed to create admin', {
      createdBy: ctx.from!.id,
      targetTelegramId: telegramId,
      error,
    });
    return;
  }

  // Send master key to super admin (ONE TIME ONLY)
  const roleLabel = role === 'super_admin' ? 'Главный администратор' : 'Администратор';

  await ctx.reply(
    `✅ **Администратор создан успешно!**\n\n` +
    `👤 Telegram ID: ${telegramId}\n` +
    `🏷 Username: ${username ? '@' + username : 'не указан'}\n` +
    `👑 Роль: ${roleLabel}\n\n` +
    `🔐 **Мастер-ключ:** \`${masterKey}\`\n\n` +
    `⚠️ **ВАЖНО:**\n` +
    `• Сохраните этот мастер-ключ!\n` +
    `• Ключ показывается только один раз\n` +
    `• Передайте ключ новому администратору в безопасном канале\n` +
    `• Администратор должен использовать /admin_login для входа\n\n` +
    `Если ключ утерян, используйте команду для его сброса.`,
    { parse_mode: 'Markdown' }
  );

  logAdminAction(ctx.from!.id, 'created_admin', {
    targetAdminId: admin.id,
    targetTelegramId: telegramId,
    role,
  });

  // Reset session
  await updateSessionState(ctx.from!.id, BotState.IDLE);
};

/**
 * List all admins (super admin only)
 */
export const handleListAdmins = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isSuperAdmin) {
    await ctx.answerCbQuery('Только главный администратор может просматривать список админов');
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  try {
    const admins = await adminService.getAllAdmins();

    if (admins.length === 0) {
      await ctx.editMessageText(
        '📋 **Список администраторов**\n\n' +
        'Нет администраторов.',
        {
          parse_mode: 'Markdown',
          ...Markup.inlineKeyboard([
            [Markup.button.callback('◀️ Назад', 'admin_panel')],
          ]),
        }
      );
      await ctx.answerCbQuery();
      return;
    }

    let message = '📋 **Список администраторов**\n\n';

    for (const admin of admins) {
      const roleLabel = admin.role === 'super_admin' ? '👑 Главный админ' : '⚙️ Администратор';
      const createdDate = new Date(admin.created_at).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });

      message += `**ID ${admin.id}:** ${roleLabel}\n`;
      message += `• Telegram ID: \`${admin.telegram_id}\`\n`;
      if (admin.username) {
        message += `• Username: @${admin.username}\n`;
      }
      message += `• Создан: ${createdDate}\n`;
      if (admin.creator) {
        message += `• Создал: ${admin.creator.displayName}\n`;
      }
      message += `• Мастер-ключ: ${admin.master_key ? '✅ установлен' : '❌ не установлен'}\n`;
      message += `\n`;
    }

    const buttons: any[][] = [];

    // Add management buttons for each admin (first 5)
    const displayCount = Math.min(admins.length, 5);
    for (let i = 0; i < displayCount; i++) {
      const admin = admins[i];
      // Don't allow removing/regenerating for self
      if (admin.telegram_id === ctx.from!.id) continue;

      buttons.push([
        Markup.button.callback(
          `🔑 ID ${admin.id} Сбросить ключ`,
          `admin_regenerate_key_${admin.id}`
        ),
        Markup.button.callback(
          `🗑 ID ${admin.id} Удалить`,
          `admin_remove_${admin.id}`
        ),
      ]);
    }

    buttons.push([Markup.button.callback('◀️ Назад', 'admin_panel')]);

    await ctx.editMessageText(message, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons),
    });

    await ctx.answerCbQuery();

    logAdminAction(ctx.from!.id, 'list_admins', { count: admins.length });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при загрузке списка');
    logger.error('Failed to list admins', {
      adminId: ctx.from!.id,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};

/**
 * Remove admin (super admin only)
 */
export const handleRemoveAdmin = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isSuperAdmin) {
    await ctx.answerCbQuery('Только главный администратор может удалять админов');
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  // Extract admin ID from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const match = callbackData.match(/^admin_remove_(\d+)$/);

  if (!match) {
    await ctx.answerCbQuery('❌ Неверный формат');
    return;
  }

  const adminId = parseInt(match[1]);

  // Don't allow removing self
  if (adminCtx.admin?.id === adminId) {
    await ctx.answerCbQuery('❌ Нельзя удалить самого себя');
    return;
  }

  try {
    const { success, error } = await adminService.removeAdmin(adminId);

    if (!success) {
      await ctx.answerCbQuery(`❌ Ошибка: ${error || 'Не удалось удалить'}`);
      return;
    }

    await ctx.answerCbQuery('✅ Администратор удален');

    await ctx.editMessageText(
      `✅ **Администратор удален**\n\n` +
      `ID: ${adminId}\n\n` +
      `Все сессии администратора деактивированы.`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('📋 Список админов', 'admin_list_admins')],
          [Markup.button.callback('◀️ Админ-панель', 'admin_panel')],
        ]),
      }
    );

    logAdminAction(ctx.from!.id, 'remove_admin', { targetAdminId: adminId });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при удалении');
    logger.error('Failed to remove admin', {
      adminId: ctx.from!.id,
      targetAdminId: adminId,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};

/**
 * Regenerate master key for admin (super admin only)
 */
export const handleRegenerateMasterKey = async (ctx: Context) => {
  const adminCtx = ctx as AdminContext;

  if (!adminCtx.isSuperAdmin) {
    await ctx.answerCbQuery('Только главный администратор может сбрасывать ключи');
    return;
  }

  // Require authentication
  if (!(await requireAuthenticatedAdmin(ctx))) {
    return;
  }

  // Extract admin ID from callback data
  const callbackData = ctx.callbackQuery && 'data' in ctx.callbackQuery ? ctx.callbackQuery.data : '';
  const match = callbackData.match(/^admin_regenerate_key_(\d+)$/);

  if (!match) {
    await ctx.answerCbQuery('❌ Неверный формат');
    return;
  }

  const adminId = parseInt(match[1]);

  try {
    const { masterKey, error } = await adminService.regenerateMasterKey(adminId);

    if (error || !masterKey) {
      await ctx.answerCbQuery(`❌ Ошибка: ${error || 'Не удалось сгенерировать ключ'}`);
      return;
    }

    await ctx.answerCbQuery('✅ Новый мастер-ключ сгенерирован');

    await ctx.editMessageText(
      `🔑 **Мастер-ключ сброшен**\n\n` +
      `ID администратора: ${adminId}\n\n` +
      `🔐 **Новый мастер-ключ:** \`${masterKey}\`\n\n` +
      `⚠️ **ВАЖНО:**\n` +
      `• Сохраните этот мастер-ключ!\n` +
      `• Ключ показывается только один раз\n` +
      `• Все старые сессии администратора деактивированы\n` +
      `• Передайте новый ключ администратору в безопасном канале`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('📋 Список админов', 'admin_list_admins')],
          [Markup.button.callback('◀️ Админ-панель', 'admin_panel')],
        ]),
      }
    );

    logAdminAction(ctx.from!.id, 'regenerate_master_key', { targetAdminId: adminId });
  } catch (error) {
    await ctx.answerCbQuery('❌ Ошибка при генерации ключа');
    logger.error('Failed to regenerate master key', {
      adminId: ctx.from!.id,
      targetAdminId: adminId,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};
