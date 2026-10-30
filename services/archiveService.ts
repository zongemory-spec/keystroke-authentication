import type { ArchiveDocument } from '../types';

// Synthetic local fixture. Never send provider credentials to the browser.
export const getDemoArchiveContent = async (role: string): Promise<ArchiveDocument[]> => [
  { title: 'Synthetic archive', content: `Fictional teaching record for role ${role}. No real database or confidential data is used.`, classification: 'DEMO', date: '2025-01-01' },
  { title: 'Query construction exercise', content: 'Compare string concatenation with parameterized queries. This interface simulates selected patterns only.', classification: 'EDUCATIONAL', date: '2025-01-02' },
];
