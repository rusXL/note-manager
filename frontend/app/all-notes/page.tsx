"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Home } from "lucide-react";
import { getAllNotes, NoteBase } from "@/lib/api";
import { NoteItem } from "@/components/note-item";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

export default function AllNotesPage() {
  const router = useRouter();

  const [notes, setNotes] = useState<NoteBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [withImage, setWithImage] = useState(false);
  const [withCaption, setWithCaption] = useState(false);
  const [priority, setPriority] = useState<string>("all"); // "all" | "0" | "1" | "2"

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      const priorityVal = priority === "all" ? null : Number(priority);
      const data = await getAllNotes({
        with_image: withImage,
        with_caption: withCaption,
        priority: priorityVal,
      });
      setNotes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notes");
    } finally {
      setLoading(false);
    }
  }, [withImage, withCaption, priority]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error}</p>
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
            onClick={() => router.back()}
            className="shrink-0"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold truncate">All Notes</h1>
            <p className="text-sm text-muted-foreground truncate">
              Browse and filter all your notes
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/")}
            className="shrink-0 gap-1"
          >
            <Home className="h-4 w-4" />
            Home
          </Button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 px-4 pb-4 overflow-x-auto">
          <div className="flex items-center gap-2">
            <Checkbox
              id="with-image"
              checked={withImage}
              onCheckedChange={(checked) => setWithImage(checked as boolean)}
            />
            <Label
              htmlFor="with-image"
              className="whitespace-nowrap cursor-pointer"
            >
              Image
            </Label>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="with-caption"
              checked={withCaption}
              onCheckedChange={(checked) => setWithCaption(checked as boolean)}
            />
            <Label
              htmlFor="with-caption"
              className="whitespace-nowrap cursor-pointer"
            >
              Caption
            </Label>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <Label className="whitespace-nowrap">Priority:</Label>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger className="w-[100px] h-8">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="0">High</SelectItem>
                <SelectItem value="1">Mid</SelectItem>
                <SelectItem value="2">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </header>

      {/* Notes list */}
      <main className="flex-1 p-4 space-y-3 overflow-y-auto">
        {loading ? (
          <div className="text-center py-12 text-muted-foreground">
            <div className="animate-pulse">Loading...</div>
          </div>
        ) : notes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No notes found</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        ) : (
          notes.map((note) => (
            <NoteItem key={note.id} id={note.id} name={note.name} />
          ))
        )}
      </main>
    </div>
  );
}
