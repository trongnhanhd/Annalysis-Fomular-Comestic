import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title:'Cosmetic R&D Intelligence', description:'Phân tích INCI và quản lý bằng chứng R&D mỹ phẩm' };
export default function RootLayout({children}: Readonly<{children:React.ReactNode}>) {
  return <html lang="vi"><body>{children}</body></html>;
}
