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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      case "mid":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      case "low":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error || !note) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error || "Note not found"}</p>
        <Button variant="outline" onClick={() => router.push("/")}>
          Go Home
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
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
        </div>
      </header>

      {/* Content */}
      <main className="p-4 space-y-6">
        {/* Task metadata */}
        {(note.deadline || note.priority) && (
          <div className="flex flex-wrap gap-3">
            {note.deadline && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent text-sm">
                <Calendar className="h-4 w-4" />
                <span>{new Date(note.deadline).toLocaleDateString()}</span>
              </div>
            )}
            {note.priority && (
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border ${getPriorityColor(
                  note.priority
                )}`}
              >
                <Flag className="h-4 w-4" />
                <span className="capitalize">{note.priority} priority</span>
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
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ImageIcon className="h-4 w-4" />
              <span>Attached Image</span>
            </div>
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
