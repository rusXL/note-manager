"use client";

import Link from "next/link";
import { FileText } from "lucide-react";

interface NoteItemProps {
  id: string;
  name: string;
}

export function NoteItem({ id, name }: NoteItemProps) {
  return (
    <Link
      href={`/note/${id}`}
      className="flex items-center gap-3 p-4 bg-card rounded-lg border border-border hover:bg-accent transition-colors"
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
        <FileText className="h-5 w-5 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{name}</p>
        <p className="text-sm text-muted-foreground">Tap to view</p>
      </div>
    </Link>
  );
}
