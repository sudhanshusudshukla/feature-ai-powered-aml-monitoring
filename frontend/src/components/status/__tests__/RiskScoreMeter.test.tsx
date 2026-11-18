/**
 * Tests for RiskScoreMeter component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RiskScoreMeter } from '../RiskScoreMeter';

describe('RiskScoreMeter', () => {
  it('renders risk score with meter role', () => {
    render(<RiskScoreMeter score={87} priority="CRITICAL" />);
    
    const meter = screen.getByRole('meter');
    expect(meter).toBeInTheDocument();
    expect(meter).toHaveAttribute('aria-valuenow', '87');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
  });

  it('displays score value and priority tag', () => {
    render(<RiskScoreMeter score={87} priority="CRITICAL" />);
    
    expect(screen.getByText('87')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('shows priority band thresholds', () => {
    render(<RiskScoreMeter score={50} priority="MEDIUM" />);
    
    expect(screen.getByText('35 Medium')).toBeInTheDocument();
    expect(screen.getByText('60 High')).toBeInTheDocument();
    expect(screen.getByText('80 Critical')).toBeInTheDocument();
  });

  it('clamps score to 0-100 range', () => {
    const { rerender } = render(<RiskScoreMeter score={150} priority="CRITICAL" />);
    let meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '150');
    
    rerender(<RiskScoreMeter score={-10} priority="LOW" />);
    meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '-10');
  });
});
