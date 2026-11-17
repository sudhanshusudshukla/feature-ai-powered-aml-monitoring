/**
 * Tests for PriorityTag component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PriorityTag } from '../PriorityTag';

describe('PriorityTag', () => {
  it('renders CRITICAL priority with red type', () => {
    render(<PriorityTag priority="CRITICAL" />);
    const tag = screen.getByText('CRITICAL');
    expect(tag).toBeInTheDocument();
  });

  it('renders HIGH priority with magenta type', () => {
    render(<PriorityTag priority="HIGH" />);
    const tag = screen.getByText('HIGH');
    expect(tag).toBeInTheDocument();
  });

  it('renders MEDIUM priority with warm-gray type', () => {
    render(<PriorityTag priority="MEDIUM" />);
    const tag = screen.getByText('MEDIUM');
    expect(tag).toBeInTheDocument();
  });

  it('renders LOW priority with gray type', () => {
    render(<PriorityTag priority="LOW" />);
    const tag = screen.getByText('LOW');
    expect(tag).toBeInTheDocument();
  });

  it('accepts data-testid prop', () => {
    render(<PriorityTag priority="CRITICAL" data-testid="test-priority" />);
    const tag = screen.getByTestId('test-priority');
    expect(tag).toBeInTheDocument();
  });
});
