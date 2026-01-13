const API_URL = "http://localhost:8000";

// Types matching the backend models
export interface SubFolderBase {
  id: number;
  name: string;
  color: string;
  parent_folder_id: number;
}

export interface NoteBase {
  id: number;
  name: string;
}

export interface Folder {
  id: number;
  name: string;
  color: string;
  description: string | null;
  subfolders: SubFolderBase[];
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
  priority: "high" | "mid" | "low" | null;
  image: ImageBase | null;
}

export interface CreateNotePayload {
  name: string;
  content: string;
  folder_id: number;
  deadline?: string | null;
  priority?: "high" | "mid" | "low" | null;
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

export async function getFolder(id: number): Promise<Folder> {
  const res = await fetch(`${API_URL}/folder/${id}`);
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
