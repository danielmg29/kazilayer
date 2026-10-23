"use client";

import { useId, useState, type ReactNode } from "react";

type PaginatedCollectionProps<T> = {
  items: T[];
  children: (visibleItems: T[]) => ReactNode;
  itemLabel?: string;
  initialPageSize?: number;
  pageSizeOptions?: number[];
  className?: string;
  compact?: boolean;
  controlsPosition?: "top" | "bottom" | "both";
};

export function PaginatedCollection<T>({
  items,
  children,
  itemLabel = "items",
  initialPageSize = 5,
  pageSizeOptions = [5, 10, 25, 50],
  className = "",
  compact = false,
  controlsPosition = "both",
}: PaginatedCollectionProps<T>) {
  const selectId = useId();
  const options = Array.from(new Set([...pageSizeOptions, initialPageSize])).sort((a, b) => a - b);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [requestedPage, setRequestedPage] = useState(1);
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const page = Math.min(requestedPage, pageCount);
  const start = (page - 1) * pageSize;
  const end = Math.min(start + pageSize, items.length);

  function controls(position: "top" | "bottom") {
    const controlId = `${selectId}-${position}`;
    return <nav
      aria-label={`${itemLabel} pagination ${position}`}
      className={`flex flex-wrap items-center justify-between gap-3 border border-line bg-panel ${position === "bottom" ? "border-t-0" : "border-b-0"} ${compact ? "px-3 py-2" : "px-4 py-3"}`}
    >
      <p className="font-mono text-[10px] uppercase tracking-[.12em] text-muted" aria-live="polite">
        {items.length ? `${start + 1}-${end} of ${items.length}` : `0 ${itemLabel}`}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-2 text-[11px] font-semibold text-muted" htmlFor={controlId}>
          Show
          <select
            id={controlId}
            className="h-8 border border-line bg-panel px-2 text-xs text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setRequestedPage(1);
            }}
          >
            {options.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
          <span>{itemLabel}</span>
        </label>
        <button className="button-secondary h-8 px-3 text-xs" type="button" disabled={page === 1} onClick={() => setRequestedPage(page - 1)}>
          Previous
        </button>
        <span className="min-w-14 text-center font-mono text-[10px] text-muted">{page} / {pageCount}</span>
        <button className="button-secondary h-8 px-3 text-xs" type="button" disabled={page === pageCount} onClick={() => setRequestedPage(page + 1)}>
          Next
        </button>
      </div>
    </nav>;
  }

  return (
    <div className={className}>
      {controlsPosition === "top" || controlsPosition === "both" ? controls("top") : null}
      {children(items.slice(start, end))}
      {controlsPosition === "bottom" || controlsPosition === "both" ? controls("bottom") : null}
    </div>
  );
}
