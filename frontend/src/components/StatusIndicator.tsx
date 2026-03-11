interface Props {
  label: string;
}

export function StatusIndicator({ label }: Props) {
  return (
    <div className="status-indicator">
      <span className="pulse-dot" />
      <span className="status-label">{label}</span>
    </div>
  );
}
