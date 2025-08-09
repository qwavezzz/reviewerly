"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface DraftDetail {
  id: number;
  slug: string;
  title: string;
  reliability_score: number | null;
  created_at: string;
  status: string;
}

export default function DraftDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [draft, setDraft] = useState<DraftDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await fetch(
        `${apiBase}/v1/editor/drafts?status=in_review&min_score=0`,
        { cache: 'no-cache' }
      );
      const data = await res.json();
      const found = data.find((d: DraftDetail) => d.id === parseInt(id, 10));
      setDraft(found);
      setLoading(false);
    }
    load();
  }, [id]);

  async function handleApprove() {
    await fetch(`${apiBase}/v1/post/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_id: parseInt(id, 10) })
    });
    router.refresh();
  }

  async function handlePublish() {
    await fetch(`${apiBase}/v1/post/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ post_id: parseInt(id, 10), channels: ['cms', 'telegram'] })
    });
    router.push('/drafts');
  }

  if (loading) return <p>Загрузка...</p>;
  if (!draft) return <p>Черновик не найден</p>;
  return (
    <div>
      <h1>{draft.title}</h1>
      <p>ID: {draft.id}</p>
      <p>Балл: {draft.reliability_score ?? '—'}</p>
      <p>Статус: {draft.status}</p>
      <div style={{ marginTop: '1rem' }}>
        {draft.status !== 'approved' && (
          <button onClick={handleApprove} style={{ marginRight: '0.5rem' }}>
            Одобрить
          </button>
        )}
        {draft.status === 'approved' && (
          <button onClick={handlePublish}>Опубликовать</button>
        )}
      </div>
    </div>
  );
}