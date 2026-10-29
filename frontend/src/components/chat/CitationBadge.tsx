import React, { useState } from 'react';
import { Citation } from '../../types';
import { ExternalLink, BookOpen } from 'lucide-react';

interface CitationBadgeProps {
  citation: Citation;
  index: number;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, index }) => {
  const [popoverOpen, setPopoverOpen] = useState(false);

  return (
    <div className="relative inline-block mr-2 mb-1.5">
      <button
        onClick={() => setPopoverOpen(!popoverOpen)}
        onMouseEnter={() => setPopoverOpen(true)}
        onMouseLeave={() => setPopoverOpen(false)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border border-border/80 bg-secondary/60 hover:bg-secondary text-foreground/80 hover:text-foreground transition-all"
      >
        <BookOpen className="w-3 h-3 text-primary" />
        <span className="font-medium truncate max-w-[140px]">{citation.title || `Source ${index + 1}`}</span>
      </button>

      {popoverOpen && (
        <div
          onMouseEnter={() => setPopoverOpen(true)}
          onMouseLeave={() => setPopoverOpen(false)}
          className="absolute bottom-full left-0 mb-2 z-40 w-72 p-3 rounded-lg border border-border bg-popover text-popover-foreground shadow-xl text-xs backdrop-blur-md animate-in fade-in"
        >
          <div className="font-semibold text-primary mb-1 flex items-center justify-between">
            <span className="truncate">{citation.title}</span>
            {citation.url && !citation.url.startsWith('doc://') && !citation.url.startsWith('local://') && (
              <a
                href={citation.url}
                target="_blank"
                rel="noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors p-0.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
          {citation.snippet && (
            <p className="text-muted-foreground text-[11px] leading-relaxed line-clamp-4">
              "{citation.snippet}"
            </p>
          )}
          {citation.url && (
            <div className="mt-2 pt-1 border-t border-border/50 text-[10px] text-muted-foreground truncate">
              {citation.url}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
