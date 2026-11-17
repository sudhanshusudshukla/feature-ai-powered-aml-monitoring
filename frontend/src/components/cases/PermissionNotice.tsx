/**
 * PermissionNotice component
 * Shows blocking notice when user cannot make decisions
 * Matches wireframe_08 permission notice design
 */

export interface PermissionNoticeProps {
  message: string;
  type?: 'info' | 'warning' | 'error';
}

export function PermissionNotice({ message, type = 'info' }: PermissionNoticeProps) {
  const getBorderColor = () => {
    switch (type) {
      case 'warning':
        return 'var(--cds-support-warning)';
      case 'error':
        return 'var(--cds-support-error)';
      default:
        return 'var(--cds-support-info)';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '!';
      case 'error':
        return '×';
      default:
        return 'i';
    }
  };

  const getBackgroundColor = () => {
    switch (type) {
      case 'warning':
        return 'var(--cds-support-warning)';
      case 'error':
        return 'var(--cds-support-error)';
      default:
        return 'var(--cds-support-info)';
    }
  };

  const getTextColor = () => {
    return type === 'warning' ? 'var(--cds-text-primary)' : 'var(--cds-text-on-color)';
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        padding: '12px 16px',
        background: 'var(--cds-layer-01)',
        border: '1px solid var(--cds-border-subtle-01)',
        borderLeft: `3px solid ${getBorderColor()}`,
        marginBottom: '8px',
      }}
      role="status"
    >
      <div
        style={{
          flex: 'none',
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          background: getBackgroundColor(),
          color: getTextColor(),
          fontSize: '11px',
          lineHeight: '16px',
          textAlign: 'center',
          fontWeight: 600,
        }}
      >
        {getIcon()}
      </div>
      <div>
        <b style={{ fontWeight: 600 }}>{message}</b>
      </div>
    </div>
  );
}
