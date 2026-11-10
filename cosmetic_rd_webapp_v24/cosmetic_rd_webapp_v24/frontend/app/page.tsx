import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { cookieName, validSession } from '@/lib/auth';
import Workspace from '@/components/Workspace';
export default async function Home() {
  const session = (await cookies()).get(cookieName)?.value;
  if (!validSession(session)) redirect('/login');
  return <Workspace />;
}
