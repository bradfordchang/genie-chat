import { useState } from "react";

interface Props {
  sql: string;
  description?: string;
}

export function SqlBlock({ sql, description }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="sql-block">
      <button className="sql-toggle" onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? "+" : "-"} SQL Query
        {description && <span className="sql-desc"> — {description}</span>}
      </button>
      {!collapsed && <pre className="sql-code">{sql}</pre>}
    </div>
  );
}
