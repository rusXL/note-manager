"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Folder as FolderIcon, ChevronLeft } from "lucide-react";
import { getFolder, Folder } from "@/lib/api";
import { NoteItem } from "@/components/note-item";
import { CreateNoteDialog } from "@/components/create-note-dialog";
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

export default function FolderPage() {
  const params = useParams();
  const router = useRouter();
  const folderId = params.id as string;

  const [folder, setFolder] = useState<Folder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [withImage, setWithImage] = useState(false);
  const [withCaption, setWithCaption] = useState(false);
  const [priority, setPriority] = useState<string>("all"); // "all" | "0" | "1" | "2"

  const fetchFolder = useCallback(async () => {
    try {
      const priorityVal = priority === "all" ? null : Number(priority);
      const data = await getFolder(folderId, {
        with_image: withImage,
        with_caption: withCaption,
        priority: priorityVal,
      });
      setFolder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load folder");
    } finally {
      setLoading(false);
    }
  }, [folderId, withImage, withCaption, priority]);

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
            onClick={() =>
              folder.parent_folder_id
                ? router.push(`/folder/${folder.parent_folder_id}`)
                : router.push("/")
            }
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
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/")}
            className="shrink-0"
          >
            Home
          </Button>
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

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 border-b bg-muted/20 overflow-x-auto">
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
