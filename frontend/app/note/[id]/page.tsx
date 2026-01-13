"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, Calendar, Flag, Image as ImageIcon } from "lucide-react";
import { getNote, Note } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function NotePage() {
  const params = useParams();
  const router = useRouter();
  const noteId = Number(params.id);

  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNote = async () => {
      try {
        const data = await getNote(noteId);
        setNote(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load note");
      } finally {
        setLoading(false);
      }
    };

    fetchNote();
  }, [noteId]);

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 0: // high
        return "bg-red-500/10 text-red-500 border-red-500/20";
      case 1: // mid
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      case 2: // low
        return "bg-green-500/10 text-green-500 border-green-500/20";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 0:
        return "High";
      case 1:
        return "Medium";
      case 2:
        return "Low";
      default:
        return "Unknown";
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-2rem)] flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error || !note) {
    return (
      <div className="min-h-[calc(100vh-2rem)] flex flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error || "Note not found"}</p>
        <Button variant="outline" onClick={() => router.push("/")}>
          Go Home
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-2rem)] bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-border backdrop-blur-sm bg-background/80">
        <div className="flex items-center gap-3 p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/folder/${note.folder_id}`)}
            className="shrink-0"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold truncate">{note.name}</h1>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/")}
            className="shrink-0"
          >
            Home
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 p-4 space-y-6 overflow-y-auto">
        {/* Task metadata */}
        {(note.deadline || note.priority !== null) && (
          <div className="flex flex-wrap gap-3">
            {note.deadline && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent text-sm">
                <Calendar className="h-4 w-4" />
                <span>
                  {new Date(note.deadline).toLocaleDateString("de-AT", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                  })}
                </span>
              </div>
            )}
            {note.priority !== null && (
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border ${getPriorityColor(
                  note.priority
                )}`}
              >
                <Flag className="h-4 w-4" />
                <span className="capitalize">
                  {getPriorityLabel(note.priority)} priority
                </span>
              </div>
            )}
          </div>
        )}

        {/* Note content */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="whitespace-pre-wrap text-foreground leading-relaxed">
            {note.content}
          </p>
        </div>

        {/* Image */}
        {note.image && (
          <div className="space-y-2">
            <div className="rounded-lg overflow-hidden border border-border">
              <img
                src={note.image.url}
                alt={note.image.caption || "Note image"}
                className="w-full h-auto"
              />
              {note.image.caption && (
                <p className="p-3 text-sm text-muted-foreground bg-muted">
                  {note.image.caption}
                </p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
