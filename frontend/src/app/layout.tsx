import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { CartProvider } from "@/context/CartContext";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "CampoDirecto — Productos del campo a tu mesa",
    template: "%s | CampoDirecto",
  },
  description:
    "Conectamos productores campesinos con consumidores urbanos. Productos frescos, orgánicos y de temporada, directamente del campo a tu hogar.",
  keywords: [
    "campo",
    "productos campesinos",
    "orgánico",
    "fresco",
    "temporada",
    "ecommerce",
    "colombia",
    "agricultura",
  ],
  openGraph: {
    type: "website",
    locale: "es_CO",
    siteName: "CampoDirecto",
    title: "CampoDirecto — Productos del campo a tu mesa",
    description:
      "Conectamos productores campesinos con consumidores urbanos. Productos frescos, orgánicos y de temporada.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={`${inter.variable} ${playfair.variable}`}>
      <body className="min-h-screen flex flex-col">
        <AuthProvider>
          <CartProvider>
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </CartProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
