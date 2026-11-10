import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title:'Cosmetic R&D | Phòng nghiên cứu công thức', description:'Phân tích INCI, nồng độ nguyên liệu, nguồn khoa học và công thức giả thuyết theo sáu thị trường',icons:{icon:'/favicon.svg'} };
export default function RootLayout({children}: Readonly<{children:React.ReactNode}>) {return <html lang="vi"><body>{children}</body></html>}
