/**
 * Admin Handler Utilities
 * Common utilities for admin handlers
 */

import { Context } from 'telegraf';
import { AdminContext } from '../../middlewares/admin.middleware';
import { config } from '../../../config';

/**
 * Check if admin is authenticated (or is super admin from config)
 * Returns true if authenticated, false if not (and sends error message)
 */
export const requireAuthenticatedAdmin = async (ctx: Context): Promise<boolean> => {
  const adminCtx = ctx as AdminContext;

  // Super admin from config doesn't need session
  if (adminCtx.isSuperAdmin && ctx.from?.id === config.telegram.superAdminId) {
    return true;
  }

  if (!adminCtx.isAuthenticated) {
    if (ctx.callbackQuery) {
      await ctx.answerCbQuery('🔐 Требуется вход. Используйте /admin_login', { show_alert: true });
    } else {
      await ctx.reply(
        '🔐 Требуется аутентификация.\n\n' +
        'Используйте команду /admin_login для входа с мастер-ключом.'
      );
    }
    return false;
  }

  return true;
};

// Rate limiting for broadcasts: Map of adminId -> last broadcast timestamp
export const broadcastRateLimits = new Map<number, number>();
export const BROADCAST_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes
