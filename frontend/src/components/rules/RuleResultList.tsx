/**
 * RuleResultList - Table of rule evaluation results
 */
import {
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
} from '@carbon/react';
import { RuleResultRow } from './RuleResultRow';
import type { RuleEvaluationItem } from '../../types/transaction';

interface RuleResultListProps {
  results: RuleEvaluationItem[];
  ariaLabel?: string;
}

export function RuleResultList({ results, ariaLabel = 'Evaluation results returned in the response' }: RuleResultListProps) {
  return (
    <Table size="sm" aria-label={ariaLabel}>
      <TableHead>
        <TableRow>
          <TableHeader>ruleCode</TableHeader>
          <TableHeader>outcome</TableHeader>
          <TableHeader style={{ textAlign: 'right' }}>score</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {results.map((result) => (
          <RuleResultRow key={result.rule_code} result={result} />
        ))}
      </TableBody>
    </Table>
  );
}
