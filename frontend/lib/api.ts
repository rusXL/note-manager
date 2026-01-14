const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types matching the backend models
export interface FolderBase {
  id: number;
  name: string;
  color: string;
  parent_folder_id: number | null;
}

export interface NoteBase {
  id: number;
  name: string;
}

export interface Folder extends FolderBase {
  description: string | null;
  subfolders: FolderBase[];
  notes: NoteBase[];
}

export interface ImageBase {
  note_id: number | null;
  url: string;
  caption: string | null;
}

export interface Note {
  id: number;
  name: string;
  folder_id: number;
  content: string;
  deadline: string | null;
  priority: 0 | 1 | 2 | null;
  image: ImageBase | null;
}

export interface CreateNotePayload {
  name: string;
  content: string;
  folder_id: number;
  deadline?: string | null;
  priority?: 0 | 1 | 2 | null;
  image?: {
    url: string;
    caption?: string | null;
  } | null;
}

export async function initData(): Promise<{ root: string }> {
  const res = await fetch(`${API_URL}/init`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to initialize data");
  return res.json();
}

export async function getFolder(
  id: number,
  filters?: {
    with_image?: boolean;
    with_caption?: boolean;
    priority?: number | null;
  }
): Promise<Folder> {
  const params = new URLSearchParams();
  if (filters?.with_image) params.append("with_image", "true");
  if (filters?.with_caption) params.append("with_caption", "true");
  if (filters?.priority !== undefined && filters?.priority !== null) {
    params.append("priority", filters.priority.toString());
  }

  const res = await fetch(`${API_URL}/folder/${id}?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch folder");
  return res.json();
}

export async function getNote(id: number): Promise<Note> {
  const res = await fetch(`${API_URL}/note/${id}`);
  if (!res.ok) throw new Error("Failed to fetch note");
  return res.json();
}

export async function createNote(data: CreateNotePayload): Promise<Note> {
  const res = await fetch(`${API_URL}/note`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create note");
  return res.json();
}
