"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Folder as FolderIcon, ChevronLeft } from "lucide-react";
import { getFolder, Folder } from "@/lib/api";
import { NoteItem } from "@/components/note-item";
import { CreateNoteDialog } from "@/components/create-note-dialog";
import { Button } from "@/components/ui/button";

export default function FolderPage() {
  const params = useParams();
  const router = useRouter();
  const folderId = Number(params.id);

  const [folder, setFolder] = useState<Folder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFolder = useCallback(async () => {
    try {
      const data = await getFolder(folderId);
      setFolder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load folder");
    } finally {
      setLoading(false);
    }
  }, [folderId]);

  useEffect(() => {
    fetchFolder();
  }, [fetchFolder]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error || !folder) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error || "Folder not found"}</p>
        <Button variant="outline" onClick={() => router.push("/")}>
          Go Home
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-2rem)] bg-background">
      {/* Header */}
      <header
        className="sticky top-0 z-10 border-b border-border backdrop-blur-sm bg-background/80"
        style={{ borderTopColor: folder.color, borderTopWidth: "3px" }}
      >
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
            <h1 className="text-xl font-bold truncate">{folder.name}</h1>
            {folder.description && (
              <p className="text-sm text-muted-foreground truncate">
                {folder.description}
              </p>
            )}
          </div>
        </div>

        {/* Subfolders as tabs */}
        {folder.subfolders.length > 0 && (
          <div className="flex gap-2 px-4 pb-3 overflow-x-auto scrollbar-hide">
            {folder.subfolders.map((subfolder) => (
              <Link
                key={subfolder.id}
                href={`/folder/${subfolder.id}`}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent hover:bg-accent/80 transition-colors whitespace-nowrap text-sm font-medium"
                style={{ borderColor: subfolder.color, borderWidth: "1px" }}
              >
                <FolderIcon
                  className="h-4 w-4"
                  style={{ color: subfolder.color }}
                />
                {subfolder.name}
              </Link>
            ))}
          </div>
        )}
      </header>

      {/* Notes list */}
      <main className="flex-1 p-4 space-y-3 overflow-y-auto">
        {folder.notes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No notes yet</p>
            <p className="text-sm">Tap the + button to create one</p>
          </div>
        ) : (
          folder.notes.map((note) => (
            <NoteItem key={note.id} id={note.id} name={note.name} />
          ))
        )}
      </main>

      {/* Floating Action Buttons - fixed at bottom right */}
      <div className="absolute bottom-6 right-6 flex gap-4">
        <CreateNoteDialog
          folderId={folderId}
          onNoteCreated={fetchFolder}
          isTask
        />
        <CreateNoteDialog folderId={folderId} onNoteCreated={fetchFolder} />
      </div>
    </div>
  );
}
