import React from 'react';
import Link from 'next/link';

interface Draft {
  id: number;
  slug: string;
  title: string;
  reliability_score: number | null;
  created_at: string;
  status: string;
}

async function fetchDrafts(): Promise<Draft[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const url = `${baseUrl}/v1/editor/drafts?status=in_review&min_score=0`;
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) {
    throw new Error('Failed to fetch drafts');
  }
  return res.json();
}

export default async function DraftsPage() {
  const drafts = await fetchDrafts();
  return (
    <div>
      <h1>Черновики</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ borderBottom: '1px solid #ddd', padding: '0.5rem' }}>ID</th>
            <th style={{ borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Заголовок</th>
            <th style={{ borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Балл</th>
            <th style={{ borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Статус</th>
          </tr>
        </thead>
        <tbody>
          {drafts.map(draft => (
            <tr key={draft.id}>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>{draft.id}</td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>
                <Link href={`/drafts/${draft.id}`}>{draft.title}</Link>
              </td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>
                {draft.reliability_score !== null ? draft.reliability_score.toFixed(2) : '–'}
              </td>
              <td style={{ borderBottom: '1px solid #eee', padding: '0.5rem' }}>{draft.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}