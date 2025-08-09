import React from 'react';
import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'News Editor Console',
  description: 'Панель редактора новостного портала'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <header style={{ padding: '1rem', borderBottom: '1px solid #ddd' }}>
          <nav>
            <Link href="/drafts" style={{ marginRight: '1rem' }}>Черновики</Link>
            <Link href="/settings">Настройки</Link>
          </nav>
        </header>
        <main style={{ padding: '1rem' }}>{children}</main>
      </body>
    </html>
  );
}