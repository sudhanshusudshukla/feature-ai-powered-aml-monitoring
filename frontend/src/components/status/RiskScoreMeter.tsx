/**
 * Risk score meter visualization component
 */
import { PriorityTag } from './PriorityTag';

interface RiskScoreMeterProps {
  score: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export function RiskScoreMeter({ score, priority }: RiskScoreMeterProps) {
  const percentage = Math.min(100, Math.max(0, score));

  return (
    <div style={{ marginTop: '16px' }}>
      <p style={{ fontSize: '12px', lineHeight: '16px', color: '#525252', margin: '0 0 8px' }}>
        Risk score
      </p>
      
      {/* Meter bar */}
      <div
        role="meter"
        aria-label="Risk score"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`${score}, ${priority}`}
        style={{
          position: 'relative',
          height: '8px',
          background: '#e0e0e0',
          margin: '8px 0',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: `${percentage}%`,
            background: '#a2191f',
          }}
        />
        {/* Threshold markers */}
        <div style={{ position: 'absolute', top: '-4px', bottom: '-4px', width: '1px', background: '#161616', left: '35%' }} />
        <div style={{ position: 'absolute', top: '-4px', bottom: '-4px', width: '1px', background: '#161616', left: '60%' }} />
        <div style={{ position: 'absolute', top: '-4px', bottom: '-4px', width: '1px', background: '#161616', left: '80%' }} />
      </div>
      
      {/* Tick labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', lineHeight: '16px', color: '#525252' }}>
        <span>0</span>
        <span>35 Medium</span>
        <span>60 High</span>
        <span>80 Critical</span>
        <span>100</span>
      </div>
      
      {/* Score and priority */}
      <p style={{ margin: '8px 0 0' }}>
        <strong style={{ fontSize: '14px' }}>{score}</strong>{' '}
        <PriorityTag priority={priority} />
      </p>
    </div>
  );
}
