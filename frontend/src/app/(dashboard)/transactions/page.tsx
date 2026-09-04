'use client';

import { useEffect, useState, useMemo } from 'react';
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Download, Filter, Search, SlidersHorizontal, ArrowUpRight, ShieldCheck } from 'lucide-react';
import api from '@/lib/api';

const money = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
function csvCell(value: unknown) { return `"${String(value ?? "").replaceAll('"', '""')}"`; }
function downloadCsv(filename: string, rows: Record<string, unknown>[], columns: string[]) {
  const body = [columns, ...rows.map(row => columns.map(column => row[column]))].map(row => row.map(csvCell).join(",")).join("\n");
  const blob = new Blob([body], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function SkeletonTable({ columns = 6 }: { columns?: number }) {
  return (
    <div className="table-skeleton" aria-label="Loading table">
      <div className="skeleton-toolbar"><span /><span /></div>
      {Array.from({ length: 6 }).map((_, r) => <div className="skeleton-row" key={r}>{Array.from({ length: columns }).map((__, c) => <i key={c} />)}</div>)}
    </div>
  );
}

function SortButton({ label, active, direction, onClick }: { label: string; active: boolean; direction: "asc" | "desc"; onClick: () => void }) {
  return <button className={`sort-button ${active ? "sorted" : ""}`} onClick={onClick}>{label}{active ? (direction === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />) : <SlidersHorizontal size={11} />}</button>;
}

export default function TransactionsPage() {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [sortBy, setSortBy] = useState<string>("payment_ts");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.get('/transactions/latest')
      .then(res => setTransactions(res.data.transactions || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const rows = useMemo(() => transactions
    .filter(row => {
      const haystack = Object.values(row).join(" ").toLowerCase();
      return haystack.includes(query.toLowerCase()) && (status === "All statuses" || row.status === status);
    })
    .sort((a, b) => {
      const av = a[sortBy], bv = b[sortBy];
      const result = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
      return direction === "asc" ? result : -result;
    }), [transactions, query, status, sortBy, direction]);

  const pagedRows = rows.slice((page - 1) * 15, page * 15);

  const sort = (key: string) => {
    if (sortBy === key) setDirection(direction === "asc" ? "desc" : "asc");
    else { setSortBy(key); setDirection("asc"); }
    setPage(1);
  };

  const exportRows = () => downloadCsv("ledgerlens-transactions.csv", rows, ["id", "order_id", "method", "amount", "status", "payment_ts"]);

  return (
    <div className="table-page">
      <div className="table-heading">
        <div>
          <span className="eyebrow">Operations / {rows.length} of {transactions.length} records</span>
          <h1>Transaction explorer</h1>
        </div>
        <button className="export-btn" onClick={exportRows}><Download size={14} /> Export CSV</button>
      </div>
      <p className="page-subtitle">Trace every record across payment, settlement, refund, and bank sources.</p>

      {loading ? <SkeletonTable /> : (
        <>
          <div className="table-toolbar">
            <label className="table-search">
              <Search size={15} />
              <input value={query} onChange={e => { setQuery(e.target.value); setPage(1); }} placeholder="Search transaction, order..." />
            </label>
            <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
              <option>All statuses</option>
              <option value="captured">captured</option>
              <option value="failed">failed</option>
              <option value="pending">pending</option>
            </select>
          </div>
          <div className="data-table-wrap">
            <table className="data-table cols-id cols-order cols-payment cols-amount cols-status cols-date">
              <thead>
                <tr>
                  <th data-col="id"><SortButton label="Transaction" active={sortBy === "id"} direction={direction} onClick={() => sort("id")} /></th>
                  <th data-col="order"><SortButton label="Order" active={sortBy === "order_id"} direction={direction} onClick={() => sort("order_id")} /></th>
                  <th data-col="payment">Method</th>
                  <th data-col="amount"><SortButton label="Amount" active={sortBy === "amount"} direction={direction} onClick={() => sort("amount")} /></th>
                  <th data-col="status">Status</th>
                  <th data-col="date"><SortButton label="Date" active={sortBy === "payment_ts"} direction={direction} onClick={() => sort("payment_ts")} /></th>
                </tr>
              </thead>
              <tbody>
                {pagedRows.map(row => (
                  <tr key={row.id} className="clickable-row">
                    <td data-col="id"><b>{row.id}</b></td>
                    <td data-col="order">{row.order_id || 'N/A'}</td>
                    <td data-col="payment"><span className="dot-status good">{row.method || 'UNKNOWN'}</span></td>
                    <td data-col="amount"><b>{money(row.amount)}</b></td>
                    <td data-col="status"><span className={`status-pill ${row.status.toLowerCase()}`}>{row.status}</span></td>
                    <td data-col="date">{new Date(row.payment_ts).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length === 0 && (
              <div className="empty-table">
                <Search size={18} />
                <b>No matching records</b>
                <span>Try clearing a filter or searching for another identifier.</span>
              </div>
            )}
          </div>
          
          <div className="table-pager">
            <span>Showing {rows.length === 0 ? 0 : (page - 1) * 15 + 1}–{Math.min(rows.length, page * 15)} of {rows.length} results</span>
            <div>
              <button disabled={page === 1} onClick={() => setPage(Math.max(1, page - 1))}><ChevronLeft size={15} /></button>
              <span className="page-number">{page}</span>
              <button disabled={rows.length <= page * 15} onClick={() => setPage(page + 1)}><ChevronRight size={15} /></button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
