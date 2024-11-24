import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import Navigation from '@/components/layout/Navigation';
import Footer from '@/components/layout/Footer';
import { ClientProviders } from '@/components/providers/ClientProviders';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Cloud Storage',
  description: 'Intelligent cloud storage with deduplication',
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-gray-50">
      <body className={`${inter.className} h-full flex flex-col`}>
        <ErrorBoundary>
          <ClientProviders>
            <Navigation />
            <main className="flex-grow">
              {children}
            </main>
            <Footer />
          </ClientProviders>
        </ErrorBoundary>
      </body>
    </html>
  );
}