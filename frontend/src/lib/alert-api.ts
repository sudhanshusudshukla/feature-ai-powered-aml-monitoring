/**
 * Alert API client functions
 */
import { apiClient } from './api-client';
import { AlertDetail } from '../types/alert';

export async function getAlertDetail(alertId: number): Promise<AlertDetail> {
  return apiClient.get<AlertDetail>(`/v1/alerts/${alertId}`);
}
