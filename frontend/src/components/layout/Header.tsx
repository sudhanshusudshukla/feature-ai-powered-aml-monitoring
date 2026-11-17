/**
 * Header component using Carbon UI Shell
 */
import {
  Header as CarbonHeader,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  HeaderPanel,
  Tag,
} from '@carbon/react';
import { Information, Renew, Search, UserAvatar } from '@carbon/icons-react';
import { useState } from 'react';
import { useAuth } from '../../lib/auth-context';
import { useNavigate } from 'react-router-dom';

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [userPanelExpanded, setUserPanelExpanded] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <CarbonHeader aria-label="AML Transaction Monitoring">
        <HeaderName href="#" prefix="">
          AML Transaction Monitoring
        </HeaderName>

        <HeaderGlobalBar>
          <HeaderGlobalAction
            aria-label="Search"
            tooltipAlignment="end"
          >
            <Search size={20} />
          </HeaderGlobalAction>

          <HeaderGlobalAction
            aria-label="Help"
            tooltipAlignment="end"
          >
            <Information size={20} />
          </HeaderGlobalAction>

          <HeaderGlobalAction
            aria-label="Refresh"
            tooltipAlignment="end"
          >
            <Renew size={20} />
          </HeaderGlobalAction>

          {user && (
            <>
              <Tag type="outline" style={{ marginLeft: 'var(--cds-spacing-03)' }}>
                {user.role.replace('_', ' ')}
              </Tag>

              <HeaderGlobalAction
                aria-label="User menu"
                tooltipAlignment="end"
                isActive={userPanelExpanded}
                onClick={() => setUserPanelExpanded(!userPanelExpanded)}
              >
                <UserAvatar size={20} />
              </HeaderGlobalAction>
            </>
          )}
        </HeaderGlobalBar>
      </CarbonHeader>

      <HeaderPanel
        aria-label="User menu"
        expanded={userPanelExpanded}
      >
        <div style={{ padding: 'var(--cds-spacing-05)' }}>
          {user && (
            <>
              <h3 style={{ marginBottom: 'var(--cds-spacing-03)' }}>
                {user.full_name}
              </h3>
              <p style={{
                fontSize: '12px',
                color: 'var(--cds-text-secondary)',
                marginBottom: 'var(--cds-spacing-05)',
              }}>
                {user.username}
              </p>
              <p style={{
                fontSize: '12px',
                color: 'var(--cds-text-secondary)',
                marginBottom: 'var(--cds-spacing-06)',
              }}>
                Role: {user.role.replace('_', ' ')}
              </p>
              <button
                onClick={handleLogout}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--cds-link-primary)',
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '14px',
                }}
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </HeaderPanel>
    </>
  );
}
