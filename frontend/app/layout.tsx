import type { ReactNode } from "react";
import "./globals.css";
import AuthBar from "../components/AuthBar";
export const metadata={title:"Formula Intelligence V4.5.2",description:"Tra cứu nguyên liệu và sàng lọc tương thích công thức R&D"};
export default function RootLayout({children}:{children:ReactNode}){return <html lang="vi"><body><AuthBar/>{children}</body></html>}
