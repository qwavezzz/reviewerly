import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect root to the drafts page
  redirect('/drafts');
}