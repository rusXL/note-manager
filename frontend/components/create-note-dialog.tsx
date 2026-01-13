"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, ListTodo } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createNote, CreateNotePayload } from "@/lib/api";

interface CreateNoteDialogProps {
  folderId: number;
  onNoteCreated: () => void;
  isTask?: boolean;
}

export function CreateNoteDialog({
  folderId,
  onNoteCreated,
  isTask = false,
}: CreateNoteDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    content: "",
    deadline: "",
    priority: "",
    imageUrl: "",
    imageCaption: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload: CreateNotePayload = {
        name: formData.name,
        content: formData.content,
        folder_id: folderId,
      };

      if (formData.deadline) {
        payload.deadline = formData.deadline;
      }

      if (formData.priority) {
        payload.priority = parseInt(formData.priority) as 0 | 1 | 2;
      }

      if (formData.imageUrl) {
        payload.image = {
          url: formData.imageUrl,
          caption: formData.imageCaption || null,
        };
      }

      const createdNote = await createNote(payload);
      setOpen(false);
      setFormData({
        name: "",
        content: "",
        deadline: "",
        priority: "",
        imageUrl: "",
        imageCaption: "",
      });
      onNoteCreated();
      // Navigate to the created note
      router.push(`/note/${createdNote.id}`);
    } catch (error) {
      console.error("Failed to create note:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          size="icon"
          variant={isTask ? "secondary" : "default"}
          className="h-14 w-14 rounded-full shadow-lg"
        >
          {isTask ? (
            <ListTodo className="h-6 w-6" />
          ) : (
            <Plus className="h-6 w-6" />
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isTask ? "Create Task" : "Create Note"}</DialogTitle>
          <DialogDescription>
            {isTask
              ? "Add a new task with deadline and priority."
              : "Add a new note to this folder."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder={isTask ? "Task title" : "Note title"}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="content">Content *</Label>
            <Textarea
              id="content"
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              placeholder={
                isTask ? "Task description..." : "Write your note here..."
              }
              rows={4}
              required
            />
          </div>

          {isTask && (
            <>
              <div className="space-y-2">
                <Label htmlFor="deadline">Deadline *</Label>
                <Input
                  id="deadline"
                  type="date"
                  value={formData.deadline}
                  onChange={(e) =>
                    setFormData({ ...formData, deadline: e.target.value })
                  }
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="priority">Priority *</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) =>
                    setFormData({ ...formData, priority: value })
                  }
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">High</SelectItem>
                    <SelectItem value="1">Medium</SelectItem>
                    <SelectItem value="2">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          <div className="space-y-2">
            <Label htmlFor="imageUrl">Image URL (optional)</Label>
            <Input
              id="imageUrl"
              type="url"
              value={formData.imageUrl}
              onChange={(e) =>
                setFormData({ ...formData, imageUrl: e.target.value })
              }
              placeholder="https://example.com/image.jpg"
            />
          </div>

          {formData.imageUrl && (
            <div className="space-y-2">
              <Label htmlFor="imageCaption">Image Caption (optional)</Label>
              <Input
                id="imageCaption"
                value={formData.imageCaption}
                onChange={(e) =>
                  setFormData({ ...formData, imageCaption: e.target.value })
                }
                placeholder="Describe the image"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : isTask ? "Create Task" : "Create Note"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
