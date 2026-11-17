/**
 * Risk score breakdown component showing calculation details
 */
import { PriorityTag } from '../status/PriorityTag';

interface ScoreBreakdownProps {
  baseScore: number;
  customerRiskAdjustment: number;
  geographyAdjustment: number;
  finalScore: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priorityRationale: string;
  pepApplied: boolean;
}

export function ScoreBreakdown({
  baseScore,
  customerRiskAdjustment,
  geographyAdjustment,
  finalScore,
  priority,
  priorityRationale,
  pepApplied,
}: ScoreBreakdownProps) {
  return (
    <div style={{ background: '#f4f4f4', padding: '16px' }}>
      <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
        Priority rationale
      </h2>
      
      <dl style={{
        margin: 0,
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        borderTop: '1px solid #c6c6c6'
      }}>
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Base score ({Math.round(baseScore / 10)} matched rules)
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'right' }}>
          {baseScore}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Customer risk adjustment
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'right' }}>
          +{customerRiskAdjustment}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Geography adjustment
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'right' }}>
          +{geographyAdjustment}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', fontWeight: 600 }}>
          Final score (capped 0–100)
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'right', fontWeight: 600 }}>
          {finalScore}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Priority
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'left' }}>
          <PriorityTag priority={priority} />
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          PEP / sanctioned floor
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'right' }}>
          {pepApplied ? 'Applied' : 'Not applied'}
        </dd>
      </dl>
      
      <p style={{ margin: '16px 0 8px' }}>
        <strong>Rationale</strong>
        <br />
        {priorityRationale}
      </p>
      
      <h3 style={{ fontSize: '16px', lineHeight: '24px', fontWeight: 600, margin: '16px 0 8px' }}>
        Priority bands
      </h3>
      <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 16px', alignItems: 'center', margin: 0 }}>
        <dt style={{ margin: 0 }}><PriorityTag priority="CRITICAL" /></dt>
        <dd style={{ margin: 0 }}>80 and above</dd>
        
        <dt style={{ margin: 0 }}><PriorityTag priority="HIGH" /></dt>
        <dd style={{ margin: 0 }}>60 to 79</dd>
        
        <dt style={{ margin: 0 }}><PriorityTag priority="MEDIUM" /></dt>
        <dd style={{ margin: 0 }}>35 to 59</dd>
        
        <dt style={{ margin: 0 }}><PriorityTag priority="LOW" /></dt>
        <dd style={{ margin: 0 }}>Below 35</dd>
      </dl>
    </div>
  );
}
