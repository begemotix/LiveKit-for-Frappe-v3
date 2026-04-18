import React from 'react';

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function Layout({ children }: RootLayoutProps) {
  const brandingStyles = {
    '--widget-primary': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR,
    '--widget-primary-hover': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR,
    '--widget-primary-dark': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR_DARK,
    '--widget-primary-hover-dark': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR_DARK,
  } as React.CSSProperties;

  // Filter out undefined values to avoid "undefined" string in style attribute
  const cleanStyles = Object.fromEntries(
    Object.entries(brandingStyles).filter(([_, v]) => v !== undefined)
  );

  return (
    <html lang="en" style={cleanStyles}>
      <body>{children}</body>
    </html>
  );
}
