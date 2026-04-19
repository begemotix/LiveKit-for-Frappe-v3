import { Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { cn } from '@/lib/utils';
import '@/styles/globals.css';

export const metadata = {
  title: 'LiveKit Embeded Voice Agent',
  description: 'LiveKit Embeded Voice Agent',
};

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

const commitMono = localFont({
  src: [
    {
      path: '../public/fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../public/fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../public/fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../public/fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
  variable: '--font-commit-mono',
});

interface RootLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export async function RootLayout({ children, className }: RootLayoutProps) {
  const brandingStyles = {
    '--primary': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR,
    '--primary-hover': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR,
    '--widget-primary': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR,
    '--widget-primary-hover': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR,
    '--widget-primary-dark': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR_DARK,
    '--widget-primary-hover-dark': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR_DARK,
  } as React.CSSProperties;

  // Filter out undefined values to avoid "undefined" string in style attribute
  const cleanStyles = Object.fromEntries(
    Object.entries(brandingStyles).filter(([, v]) => v !== undefined)
  );

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn('scroll-smooth', className)}
      style={cleanStyles}
    >
      <body
        className={cn(publicSans.variable, commitMono.variable, 'overflow-x-hidden antialiased')}
      >
        {children}
      </body>
    </html>
  );
}
