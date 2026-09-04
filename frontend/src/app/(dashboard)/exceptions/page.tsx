'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowRight, ArrowUp, ChevronLeft, ChevronRight, CircleAlert, Download, Filter, Search, SlidersHorizontal, X } from 'lucide-react';
import api from '@/lib/api';
import Link from 'next/link';

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

function SkeletonTable({ columns = 7 }: { columns?: number }) {
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

export default function ExceptionsPage() {
  const [loading, setLoading] = useState(true);
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [sortBy, setSortBy] = useState<string>("detected_at");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.get('/exceptions')
      .then(res => {
        const unique = Array.from(new Map(res.data.map((item: any) => [item.id, item])).values());
        setExceptions(unique as any[]);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getPriority = (ex: any) => {
    if (ex.severity === 'CRITICAL') return 95;
    if (ex.severity === 'HIGH') return 80;
    return 50;
  };

  const rows = useMemo(() => exceptions
    .filter(row => {
      const haystack = Object.values(row).join(" ").toLowerCase();
      return haystack.includes(query.toLowerCase()) && (status === "All statuses" || row.status === status);
    })
    .sort((a, b) => {
      const av = sortBy === 'priority' ? getPriority(a) : a[sortBy];
      const bv = sortBy === 'priority' ? getPriority(b) : b[sortBy];
      const result = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
      return direction === "asc" ? result : -result;
    }), [exceptions, query, status, sortBy, direction]);

  const pagedRows = rows.slice((page - 1) * 15, page * 15);

  const sort = (key: string) => {
    if (sortBy === key) setDirection(direction === "asc" ? "desc" : "asc");
    else { setSortBy(key); setDirection("asc"); }
    setPage(1);
  };

  const exportRows = () => downloadCsv("ledgerlens-exceptions.csv", rows, ["id", "type", "amount", "financial_exposure", "severity", "confidence", "status", "detected_at"]);

  const critical = exceptions.filter(e => e.severity === 'CRITICAL').length;
  const review = exceptions.filter(e => e.status === 'PENDING' || e.status === 'PENDING_REVIEW').length;
  const autoResolved = exceptions.filter(e => e.status === 'AUTO_RESOLVED').length;
  const exposure = exceptions.reduce((acc, e) => acc + (e.financial_exposure || e.amount || 0), 0);

  return (
    <div className="table-page">
      <div className="table-heading">
        <div>
          <span className="eyebrow">Operations / {exceptions.length} issues detected</span>
          <h1>Exceptions</h1>
        </div>
        <button className="export-btn" onClick={exportRows}><Download size={14} /> Export CSV</button>
      </div>
      <p className="page-subtitle">Review the issues with the highest financial exposure and confidence-backed evidence.</p>

      <div className="exception-metrics">
        <div><span>Critical</span><b>{String(critical).padStart(2, '0')}</b><small>Severity</small></div>
        <div><span>Review</span><b>{String(review).padStart(2, '0')}</b><small>Pending review</small></div>
        <div><span>Auto-resolved</span><b>{String(autoResolved).padStart(2, '0')}</b><small>Closed automatically</small></div>
        <div><span>Exposure</span><b>{money(exposure)}</b><small>Across open issues</small></div>
      </div>

      {loading ? <SkeletonTable columns={7} /> : (
        <>
          <div className="table-toolbar">
            <label className="table-search">
              <Search size={15} />
              <input value={query} onChange={e => { setQuery(e.target.value); setPage(1); }} placeholder="Search ID, type, status..." />
            </label>
            <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
              <option>All statuses</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="PENDING">PENDING</option>
              <option value="AUTO_RESOLVED">AUTO_RESOLVED</option>
            </select>
          </div>
          <div className="data-table-wrap">
            <table className="data-table exception-table cols-id cols-type cols-amount cols-exposure cols-priority cols-confidence cols-status cols-detected">
              <thead>
                <tr>
                  <th data-col="id"><SortButton label="ID" active={sortBy === "id"} direction={direction} onClick={() => sort("id")} /></th>
                  <th data-col="type">Type</th>
                  <th data-col="amount"><SortButton label="Amount" active={sortBy === "amount"} direction={direction} onClick={() => sort("amount")} /></th>
                  <th data-col="exposure"><SortButton label="Exposure" active={sortBy === "financial_exposure"} direction={direction} onClick={() => sort("financial_exposure")} /></th>
                  <th data-col="priority"><SortButton label="Priority" active={sortBy === "priority"} direction={direction} onClick={() => sort("priority")} /></th>
                  <th data-col="confidence"><SortButton label="Confidence" active={sortBy === "confidence"} direction={direction} onClick={() => sort("confidence")} /></th>
                  <th data-col="status">Status</th>
                  <th data-col="detected">Detected</th>
                </tr>
              </thead>
              <tbody>
                {pagedRows.map(row => (
                  <tr key={row.id} className="clickable-row">
                    <td>
                      <Link href={`/exceptions/${row.id}`} style={{textDecoration:'none', color:'inherit', display:'block'}}>
                        <b>{row.id}</b>
                        <small>financial control</small>
                      </Link>
                    </td>
                    <td><span className="exception-type"><CircleAlert size={14} />{row.type?.replace(/_/g, ' ')}</span></td>
                    <td>{money(row.amount)}</td>
                    <td><b>{money(row.financial_exposure || row.amount)}</b></td>
                    <td><span className={`priority-score ${getPriority(row) >= 90 ? "high" : ""}`}>{getPriority(row)}<small>/100</small></span></td>
                    <td>
                      <span className="confidence-meter"><i style={{ width: `${Math.round((row.confidence || 0) * 100)}%` }} /></span>
                      <b className="confidence-number">{Math.round((row.confidence || 0) * 100)}%</b>
                    </td>
                    <td><span className={`status-pill ${(row.status || '').toLowerCase().replace("_", "")}`}>{row.status}</span></td>
                    <td>{new Date(row.detected_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length === 0 && (
              <div className="empty-table">
                <X size={18} />
                <b>No matching exceptions</b>
                <span>Try a different status or search term.</span>
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
