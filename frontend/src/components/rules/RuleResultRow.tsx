/**
 * RuleResultRow - Single rule evaluation result row
 */
import { TableRow, TableCell } from '@carbon/react';
import { RuleResultTag } from '../status/RuleResultTag';
import type { RuleEvaluationItem } from '../../types/transaction';

interface RuleResultRowProps {
  result: RuleEvaluationItem;
}

export function RuleResultRow({ result }: RuleResultRowProps) {
  return (
    <TableRow data-testid={`rule-result-${result.rule_code}`}>
      <TableCell className="cds--type-mono">{result.rule_code}</TableCell>
      <TableCell>
        <RuleResultTag outcome={result.outcome} />
      </TableCell>
      <TableCell className="cds--type-mono" style={{ textAlign: 'right' }}>
        {result.score}
      </TableCell>
    </TableRow>
  );
}
