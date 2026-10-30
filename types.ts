
export interface User {
  id: number;
  username: string;
  role: string;
  secret_data: string;
}

export interface SQLQueryResult {
  success: boolean;
  rows: User[];
  executedQuery: string;
  error?: string;
  simulation?: "normal" | "tautology" | "comment";
}

export enum SecurityView {
  LOGIN = 'LOGIN',
  DASHBOARD = 'DASHBOARD',
  LAB_GUIDE = 'LAB_GUIDE'
}

export interface ArchiveDocument {
  title: string;
  content: string;
  classification: string;
  date: string;
}
