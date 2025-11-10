/**
 * SigmaTrade Bot - Main Entry Point
 * Initializes database, bot, and all services
 */

import { config } from './config';
import { createLogger } from './utils/logger.util';
import { initializeDatabase, closeDatabase } from './database/data-source';
import { initializeBot, startBot, stopBot } from './bot';

const logger = createLogger('Main');

/**
 * Main application startup
 */
async function main() {
  try {
    // Display startup banner
    console.log(`
╔═══════════════════════════════════════════════════════╗
║           SigmaTrade DeFi Telegram Bot                ║
║              Starting up...                            ║
╚═══════════════════════════════════════════════════════╝
    `);

    logger.info('Starting SigmaTrade Bot', {
      env: config.env,
      nodeVersion: process.version,
    });

    // Step 1: Initialize database
    logger.info('Initializing database...');
    await initializeDatabase();
    logger.info('✅ Database initialized');

    // Step 2: Initialize bot
    logger.info('Initializing Telegram bot...');
    const bot = initializeBot();
    logger.info('✅ Bot initialized');

    // Step 3: Start bot
    logger.info('Starting bot...');
    await startBot(bot);
    logger.info('✅ Bot started successfully');

    console.log(`
╔═══════════════════════════════════════════════════════╗
║        🚀 SigmaTrade Bot is running! 🚀              ║
║                                                       ║
║  Environment: ${config.env.padEnd(40)}║
║  Database: Connected                                  ║
║  Bot: Active                                          ║
║                                                       ║
║  Press Ctrl+C to stop                                 ║
╚═══════════════════════════════════════════════════════╝
    `);

    // Setup graceful shutdown
    setupGracefulShutdown(bot);

  } catch (error) {
    logger.error('Fatal error during startup', {
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });

    console.error('❌ Failed to start bot:', error);
    process.exit(1);
  }
}

/**
 * Setup graceful shutdown handlers
 */
function setupGracefulShutdown(bot: any) {
  const shutdown = async (signal: string) => {
    console.log(`\n\nReceived ${signal}, starting graceful shutdown...`);

    logger.info(`Received ${signal}, shutting down gracefully...`);

    try {
      // Step 1: Stop accepting new updates
      logger.info('Stopping bot...');
      await stopBot(bot);
      logger.info('✅ Bot stopped');

      // Step 2: Close database connections
      logger.info('Closing database...');
      await closeDatabase();
      logger.info('✅ Database closed');

      console.log(`
╔═══════════════════════════════════════════════════════╗
║      SigmaTrade Bot shut down successfully            ║
╚═══════════════════════════════════════════════════════╝
      `);

      logger.info('Graceful shutdown completed');
      process.exit(0);
    } catch (error) {
      logger.error('Error during shutdown', {
        error: error instanceof Error ? error.message : String(error),
      });

      console.error('❌ Error during shutdown:', error);
      process.exit(1);
    }
  };

  // Handle termination signals
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  // Handle uncaught errors
  process.on('uncaughtException', (error) => {
    logger.error('Uncaught exception', {
      error: error.message,
      stack: error.stack,
    });

    console.error('❌ Uncaught exception:', error);

    // Attempt graceful shutdown
    shutdown('uncaughtException');
  });

  process.on('unhandledRejection', (reason) => {
    logger.error('Unhandled rejection', {
      reason: reason instanceof Error ? reason.message : String(reason),
      stack: reason instanceof Error ? reason.stack : undefined,
    });

    console.error('❌ Unhandled rejection:', reason);

    // Attempt graceful shutdown
    shutdown('unhandledRejection');
  });
}

// Start the application
main();
