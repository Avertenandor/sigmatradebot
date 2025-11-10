/**
 * Blockchain Utility Functions
 * Common utilities for blockchain operations
 */

import { ethers } from 'ethers';
import { logger } from '../../utils/logger.util';
import { config } from '../../config';

// USDT BEP-20 ABI (ERC20 standard)
export const USDT_ABI = [
  'function decimals() view returns (uint8)',
  'function balanceOf(address account) view returns (uint256)',
  'function transfer(address to, uint256 amount) returns (bool)',
  'event Transfer(address indexed from, address indexed to, uint256 value)',
];

// Cached USDT decimals (always 18, but cached to avoid repeated RPC calls)
let usdtDecimalsCache: number | undefined;

/**
 * Get cached USDT decimals (fetches once on first call)
 */
export async function getUsdtDecimals(usdtContract: ethers.Contract): Promise<number> {
  if (usdtDecimalsCache === undefined) {
    usdtDecimalsCache = await usdtContract.decimals();
    logger.info(`✅ USDT decimals cached: ${usdtDecimalsCache}`);
  }
  return usdtDecimalsCache;
}

/**
 * Get USDT balance of an address
 */
export async function getBalance(
  address: string,
  usdtContract: ethers.Contract
): Promise<number> {
  try {
    const decimals = await getUsdtDecimals(usdtContract);
    const balance = await usdtContract.balanceOf(address);
    return parseFloat(ethers.formatUnits(balance, decimals));
  } catch (error) {
    logger.error(`❌ Error getting balance for ${address}:`, error);
    return 0;
  }
}

/**
 * Verify transaction exists and is confirmed
 */
export async function verifyTransaction(
  txHash: string,
  provider: ethers.JsonRpcProvider
): Promise<{
  exists: boolean;
  confirmed: boolean;
  blockNumber?: number;
}> {
  try {
    const receipt = await provider.getTransactionReceipt(txHash);

    if (!receipt) {
      return { exists: false, confirmed: false };
    }

    const currentBlock = await provider.getBlockNumber();
    const confirmations = currentBlock - receipt.blockNumber;

    return {
      exists: true,
      confirmed:
        receipt.status === 1 &&
        confirmations >= config.blockchain.confirmationBlocks,
      blockNumber: receipt.blockNumber,
    };
  } catch (error) {
    logger.error(`❌ Error verifying transaction ${txHash}:`, error);
    return { exists: false, confirmed: false };
  }
}
