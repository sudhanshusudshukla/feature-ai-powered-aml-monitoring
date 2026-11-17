/**
 * Sidebar navigation component using Carbon SideNav
 */
import { SideNav, SideNavItems, SideNavLink } from '@carbon/react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

export function Sidebar() {
  const location = useLocation();
  const { user } = useAuth();

  // Role-based navigation filtering
  const navigationItems = [
    { path: '/dashboard', label: 'Dashboard', roles: ['AML_ANALYST', 'AML_OFFICER', 'AML_MANAGER', 'ADMINISTRATOR'] },
    { path: '/transactions', label: 'Transactions', roles: ['AML_ANALYST', 'AML_OFFICER', 'AML_MANAGER', 'ADMINISTRATOR'] },
    { path: '/alerts', label: 'Alerts', roles: ['AML_ANALYST', 'AML_OFFICER', 'AML_MANAGER'] },
    { path: '/cases', label: 'Cases', roles: ['AML_ANALYST', 'AML_OFFICER', 'AML_MANAGER'] },
    { path: '/rules', label: 'Rules', roles: ['AML_ANALYST', 'AML_OFFICER', 'AML_MANAGER', 'ADMINISTRATOR'] },
    { path: '/admin', label: 'Administration', roles: ['ADMINISTRATOR'] },
  ];

  const visibleItems = navigationItems.filter(
    (item) => !user || item.roles.includes(user.role)
  );

  return (
    <SideNav
      aria-label="Main navigation"
      expanded
      isFixedNav
    >
      <SideNavItems>
        {visibleItems.map((item) => (
          <SideNavLink
            key={item.path}
            renderIcon={() => null}
            as={Link}
            to={item.path}
            isActive={location.pathname === item.path}
          >
            {item.label}
          </SideNavLink>
        ))}
      </SideNavItems>
    </SideNav>
  );
}
