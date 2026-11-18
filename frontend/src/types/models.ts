/**
 * TypeScript interfaces matching backend models
 */

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export enum UserRole {
  AML_ANALYST = 'AML_ANALYST',
  AML_OFFICER = 'AML_OFFICER',
  AML_MANAGER = 'AML_MANAGER',
  ADMINISTRATOR = 'ADMINISTRATOR',
  AUDITOR = 'AUDITOR',
}
