/**
 * Transaction API methods
 */
import { apiClient } from './api-client';
import type {
  TransactionIngestRequest,
  TransactionIngestResponse,
  TransactionDetailResponse,
} from '../types/transaction';

export const transactionApi = {
  /**
   * Submit a transaction for screening
   */
  async submitTransaction(
    data: TransactionIngestRequest
  ): Promise<TransactionIngestResponse> {
    return apiClient.post<TransactionIngestResponse>('/v1/transactions/', data);
  },

  /**
   * Get transaction detail by ID
   */
  async getTransactionDetail(id: string): Promise<TransactionDetailResponse> {
    return apiClient.get<TransactionDetailResponse>(`/v1/transactions/${id}`);
  },
};
