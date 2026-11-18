/**
 * Layout component wrapping pages with Header, Sidebar, and main content area
 */
import { ReactNode } from 'react';
import { Theme, Content } from '@carbon/react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <Theme theme="white">
      <Header />
      <Sidebar />
      <Content id="main-content" style={{ padding: 'var(--cds-spacing-07)' }}>
        {children}
      </Content>
    </Theme>
  );
}
