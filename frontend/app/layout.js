import { Roboto, Roboto_Slab, Roboto_Flex, Roboto_Mono, Roboto_Serif } from "next/font/google";
import "./globals.css";

const roboto = Roboto({
  variable: "--font-roboto",
  weight: "300",
  subsets: ["latin"],
});

const robotoSlab = Roboto_Slab({
  variable: "--font-roboto-slab",
  subsets: ["latin"],
});

const robotoFlex = Roboto_Flex({
  variable: "--font-roboto-flex",
  subsets: ["latin"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

const robotoSerif = Roboto_Serif({
  variable: "--font-roboto-serif",
  subsets: ["latin"],
});

export const metadata = {
  title: "MartyChat • Your AI-Powered Psychology Assistant",
  description: "Your AI-Powered Psychology Assistant.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${roboto.variable} ${robotoSlab.variable} ${robotoFlex.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
