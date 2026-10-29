import React, { useState, useMemo } from 'react';
import { Check, Copy, PanelRight, Terminal, Eye, WrapText } from 'lucide-react';

interface CodeBlockProps {
  language?: string;
  value: string;
  onOpenInCanvas?: (content: string, language: string) => void;
}

// Token categories for syntax styling
type TokenType = 'keyword' | 'string' | 'comment' | 'number' | 'function' | 'type' | 'tag' | 'operator' | 'plain';

interface Token {
  type: TokenType;
  text: string;
}

const KEYWORDS_JS = new Set([
  'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'do',
  'switch', 'case', 'break', 'continue', 'import', 'export', 'from', 'default',
  'class', 'extends', 'constructor', 'this', 'super', 'new', 'try', 'catch',
  'finally', 'throw', 'async', 'await', 'yield', 'typeof', 'instanceof', 'in',
  'of', 'void', 'delete'
]);

const KEYWORDS_PY = new Set([
  'def', 'return', 'if', 'elif', 'else', 'for', 'while', 'break', 'continue',
  'import', 'from', 'as', 'class', 'try', 'except', 'finally', 'raise', 'with',
  'pass', 'lambda', 'yield', 'global', 'nonlocal', 'assert', 'async', 'await'
]);

const KEYWORDS_SQL = new Set([
  'select', 'from', 'where', 'insert', 'into', 'update', 'delete', 'create',
  'table', 'drop', 'alter', 'join', 'inner', 'left', 'right', 'full', 'outer',
  'on', 'group', 'by', 'order', 'having', 'limit', 'offset', 'union', 'all',
  'as', 'distinct', 'case', 'when', 'then', 'else', 'end', 'and', 'or', 'not',
  'in', 'is', 'null', 'like', 'between'
]);

const BUILTINS_CONSTANTS = new Set([
  'true', 'false', 'null', 'undefined', 'NaN', 'Infinity', 'None', 'True', 'False'
]);

function tokenizeLine(line: string, lang: string): Token[] {
  const lowerLang = (lang || '').toLowerCase();
  const tokens: Token[] = [];
  let i = 0;
  const n = line.length;

  while (i < n) {
    // 1. Line Comments
    if (
      (line.startsWith('//', i) && lowerLang !== 'python' && lowerLang !== 'bash' && lowerLang !== 'sh') ||
      (line.startsWith('#', i) && (lowerLang === 'python' || lowerLang === 'bash' || lowerLang === 'sh' || lowerLang === 'yaml' || lowerLang === 'yml')) ||
      (line.startsWith('--', i) && (lowerLang === 'sql' || lowerLang === 'sqlite'))
    ) {
      tokens.push({ type: 'comment', text: line.slice(i) });
      break;
    }

    // 2. HTML/XML comment
    if (line.startsWith('<!--', i)) {
      const endIdx = line.indexOf('-->', i + 4);
      if (endIdx !== -1) {
        tokens.push({ type: 'comment', text: line.slice(i, endIdx + 3) });
        i = endIdx + 3;
        continue;
      } else {
        tokens.push({ type: 'comment', text: line.slice(i) });
        break;
      }
    }

    // 3. String literals ("...", '...', `...`)
    const char = line[i];
    if (char === '"' || char === "'" || char === '`') {
      const quote = char;
      let j = i + 1;
      let escaped = false;
      while (j < n) {
        if (!escaped && line[j] === quote) {
          j++;
          break;
        }
        if (line[j] === '\\' && !escaped) {
          escaped = true;
        } else {
          escaped = false;
        }
        j++;
      }
      tokens.push({ type: 'string', text: line.slice(i, j) });
      i = j;
      continue;
    }

    // 4. Numbers (decimal, hex, float)
    if (/\d/.test(char) || (char === '.' && i + 1 < n && /\d/.test(line[i + 1]))) {
      let j = i;
      while (j < n && /[\d.a-fA-FxX_]/.test(line[j])) {
        j++;
      }
      tokens.push({ type: 'number', text: line.slice(i, j) });
      i = j;
      continue;
    }

    // 5. Identifiers, Keywords, Functions
    if (/[a-zA-Z_$]/.test(char)) {
      let j = i;
      while (j < n && /[a-zA-Z0-9_$-]/.test(line[j])) {
        j++;
      }
      const word = line.slice(i, j);
      const wordLower = word.toLowerCase();

      // Check if followed by opening paren (function call/declaration)
      let isFunc = false;
      let k = j;
      while (k < n && /\s/.test(line[k])) k++;
      if (k < n && line[k] === '(') {
        isFunc = true;
      }

      if (BUILTINS_CONSTANTS.has(word)) {
        tokens.push({ type: 'number', text: word });
      } else if (
        KEYWORDS_JS.has(word) ||
        KEYWORDS_PY.has(word) ||
        KEYWORDS_SQL.has(wordLower)
      ) {
        tokens.push({ type: 'keyword', text: word });
      } else if (isFunc) {
        tokens.push({ type: 'function', text: word });
      } else if (/^[A-Z][a-zA-Z0-9_]*$/.test(word)) {
        tokens.push({ type: 'type', text: word });
      } else {
        tokens.push({ type: 'plain', text: word });
      }
      i = j;
      continue;
    }

    // 6. Operators & Punctuation
    if (/[=+\-*/%&|^!<>?:;,.~]/.test(char)) {
      tokens.push({ type: 'operator', text: char });
      i++;
      continue;
    }

    // 7. Whitespace and other characters
    tokens.push({ type: 'plain', text: char });
    i++;
  }

  return tokens;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  language = 'text',
  value,
  onOpenInCanvas,
}) => {
  const [copied, setCopied] = useState(false);
  const [wordWrap, setWordWrap] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const isPreviewable = ['html', 'svg', 'xml', 'markdown', 'md'].includes(language.toLowerCase());

  const lines = useMemo(() => {
    const rawLines = value.split('\n');
    return rawLines.map(line => tokenizeLine(line, language));
  }, [value, language]);

  const showLineNumbers = lines.length > 2;

  const getTokenClass = (type: TokenType): string => {
    switch (type) {
      case 'keyword':
        return 'text-purple-400 font-medium';
      case 'string':
        return 'text-emerald-400';
      case 'comment':
        return 'text-neutral-500 italic';
      case 'number':
        return 'text-amber-400 font-medium';
      case 'function':
        return 'text-sky-400 font-medium';
      case 'type':
        return 'text-cyan-300 font-medium';
      case 'operator':
        return 'text-neutral-400';
      default:
        return 'text-neutral-200';
    }
  };

  return (
    <div className="code-block relative my-3.5 rounded-xl border border-border/80 font-mono text-xs overflow-hidden bg-neutral-950 shadow-md">
      {/* Code Header Bar */}
      <div className="code-block-header flex items-center justify-between px-3.5 py-2 border-b border-border/60 bg-neutral-900/90 text-neutral-300">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-primary shrink-0" />
          <span className="font-semibold uppercase tracking-wider text-[11px] text-neutral-200">
            {language}
          </span>
          <span className="text-[10px] text-neutral-400 font-sans">
            {lines.length} {lines.length === 1 ? 'line' : 'lines'}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Toggle word wrap */}
          <button
            type="button"
            onClick={() => setWordWrap(!wordWrap)}
            aria-label={wordWrap ? 'Disable word wrap' : 'Enable word wrap'}
            className={`code-block-action flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-sans transition-colors ${
              wordWrap ? 'text-primary bg-primary/10' : 'text-neutral-400 hover:text-white hover:bg-neutral-800'
            }`}
            title={wordWrap ? 'Disable word wrap' : 'Enable word wrap'}
          >
            <WrapText className="w-3 h-3" />
            <span className="hidden sm:inline">Wrap</span>
          </button>

          {/* Open in Canvas Studio */}
          {onOpenInCanvas && (
            <button
              type="button"
              onClick={() => onOpenInCanvas(value, language)}
              aria-label={`Open ${language} code in Canvas Studio`}
              className="code-block-action flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-sans text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
              title="Open in Canvas Studio side-by-side"
            >
              {isPreviewable ? <Eye className="w-3 h-3 text-primary" /> : <PanelRight className="w-3 h-3 text-primary" />}
              <span>Canvas</span>
            </button>
          )}

          {/* Copy code */}
          <button
            type="button"
            onClick={handleCopy}
            aria-label={copied ? 'Code copied to clipboard' : 'Copy code to clipboard'}
            className="code-block-action flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-sans text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
            title="Copy code"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Body */}
      <pre
        className={`p-3.5 overflow-x-auto leading-relaxed scrollbar-thin text-xs font-mono text-neutral-200 ${
          wordWrap ? 'whitespace-pre-wrap break-words' : 'whitespace-pre'
        }`}
      >
        <code>
          {lines.map((lineTokens, lineIdx) => (
            <div key={lineIdx} className="table-row group/line hover:bg-neutral-900/40">
              {showLineNumbers && (
                <span className="table-cell pr-3.5 select-none text-right text-neutral-600 font-mono text-[11px] group-hover/line:text-neutral-400 w-8">
                  {lineIdx + 1}
                </span>
              )}
              <span className="table-cell">
                {lineTokens.length === 0 ? (
                  '\n'
                ) : (
                  lineTokens.map((t, tIdx) => (
                    <span key={tIdx} className={getTokenClass(t.type)}>
                      {t.text}
                    </span>
                  ))
                )}
              </span>
            </div>
          ))}
        </code>
      </pre>
    </div>
  );
};
