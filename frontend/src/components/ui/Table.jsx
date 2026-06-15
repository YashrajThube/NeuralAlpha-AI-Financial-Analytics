import { cn } from '../../lib/utils'

export default function Table({ columns, rows, className = '', emptyMessage = 'No records found yet.' }) {
  return (
    <div className={cn('overflow-x-auto rounded-xl border border-white/10', className)}>
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-white/5 text-xs uppercase tracking-wide text-gray-400">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 font-semibold">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr key={row.id || index} className="border-t border-white/10 text-gray-200">
                {columns.map((column) => (
                  <td key={`${column.key}-${index}`} className="px-4 py-3">
                    {column.render ? column.render(row[column.key], row) : row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr className="border-t border-white/10 text-gray-300">
              <td colSpan={columns.length} className="px-4 py-6 text-center text-sm">
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
