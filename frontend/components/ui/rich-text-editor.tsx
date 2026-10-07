"use client";

import { useRef, useState } from "react";

export function RichTextEditor({ name, label, defaultValue = "" }: { name: string; label: string; defaultValue?: string }) {
  const editor = useRef<HTMLDivElement>(null);
  const [value, setValue] = useState(defaultValue);

  function command(action: "bold" | "italic" | "insertUnorderedList" | "insertOrderedList") {
    editor.current?.focus();
    document.execCommand(action);
    setValue(editor.current?.innerHTML ?? "");
  }

  return (
    <div className="field-label">
      <span>{label}<small className="ml-2 font-mono text-[9px] uppercase text-muted">Restricted rich text</small></span>
      <div className="rich-editor">
        <div className="rich-editor-toolbar" aria-label={`${label} formatting`}>
          <button type="button" onClick={() => command("bold")} aria-label="Bold"><b>B</b></button>
          <button type="button" onClick={() => command("italic")} aria-label="Italic"><i>I</i></button>
          <button type="button" onClick={() => command("insertUnorderedList")} aria-label="Bulleted list">• List</button>
          <button type="button" onClick={() => command("insertOrderedList")} aria-label="Numbered list">1. List</button>
        </div>
        <div ref={editor} className="rich-editor-content" contentEditable suppressContentEditableWarning onInput={(event) => setValue(event.currentTarget.innerHTML)} dangerouslySetInnerHTML={{ __html: defaultValue }} />
        <input type="hidden" name={name} value={value} />
      </div>
    </div>
  );
}
