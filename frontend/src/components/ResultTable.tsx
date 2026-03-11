interface Props {
  columns: string[];
  rows: string[][];
  rowCount?: number;
}

export function ResultTable({ columns, rows, rowCount }: Props) {
  const showing = rows.length;
  const total = rowCount ?? rows.length;

  return (
    <div className="result-table-wrapper">
      {total > showing && (
        <div className="row-count">
          Showing {showing} of {total} rows
        </div>
      )}
      <div className="table-scroll">
        <table className="result-table">
          <thead>
            <tr>
              {columns.map((col, i) => (
                <th key={i}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{cell ?? ""}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
