"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Bold, Italic, List } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useRef } from "react";

interface RichNoteEditorProps {
  content: string;
  onChange: (html: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
}

export function RichNoteEditor({
  content,
  onChange,
  placeholder = "Schrijf een notitie...",
  autoFocus = false,
  className,
}: RichNoteEditorProps) {
  const isUpdatingRef = useRef(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        code: false,
        codeBlock: false,
        blockquote: false,
        horizontalRule: false,
        hardBreak: false,
      }),
    ],
    content: content || "",
    editorProps: {
      attributes: {
        class:
          "min-h-[80px] px-3 py-2.5 text-sm outline-none prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0",
      },
    },
    onUpdate: ({ editor }) => {
      isUpdatingRef.current = true;
      onChange(editor.getHTML());
      isUpdatingRef.current = false;
    },
    immediatelyRender: false,
  });

  // Sync external content changes (e.g. phone note flow)
  useEffect(() => {
    if (editor && !isUpdatingRef.current) {
      const currentContent = editor.getHTML();
      if (content !== currentContent) {
        editor.commands.setContent(content || "");
      }
    }
  }, [content, editor]);

  if (!editor) {
    return (
      <div
        className={cn(
          "rounded-lg border border-input bg-background min-h-[118px]",
          className
        )}
      />
    );
  }

  if (autoFocus && !editor.isFocused) {
    editor.commands.focus();
  }

  const toolbarButtons = [
    {
      icon: Bold,
      label: "Vet",
      action: () => editor.chain().focus().toggleBold().run(),
      isActive: editor.isActive("bold"),
    },
    {
      icon: Italic,
      label: "Cursief",
      action: () => editor.chain().focus().toggleItalic().run(),
      isActive: editor.isActive("italic"),
    },
    {
      icon: List,
      label: "Opsomming",
      action: () => editor.chain().focus().toggleBulletList().run(),
      isActive: editor.isActive("bulletList"),
    },
  ];

  return (
    <div
      className={cn(
        "rounded-lg border border-input bg-background transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20",
        className
      )}
    >
      {/* Toolbar */}
      <div className="flex items-center gap-0.5 px-2 py-1.5 border-b border-input/50">
        {toolbarButtons.map((btn) => (
          <button
            key={btn.label}
            type="button"
            onClick={btn.action}
            title={btn.label}
            className={cn(
              "flex items-center justify-center h-7 w-7 rounded-md text-muted-foreground transition-colors",
              btn.isActive
                ? "bg-muted text-foreground"
                : "hover:bg-muted hover:text-foreground"
            )}
          >
            <btn.icon className="h-3.5 w-3.5" />
          </button>
        ))}
      </div>

      {/* Editor */}
      <div className="relative">
        {editor.isEmpty && (
          <div className="absolute top-0 left-0 px-3 py-2.5 text-sm text-muted-foreground pointer-events-none">
            {placeholder}
          </div>
        )}
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

/** Check if a note HTML string is effectively empty */
export function isNoteEmpty(html: string | undefined | null): boolean {
  if (!html) return true;
  return html.replace(/<[^>]*>/g, "").trim() === "";
}
