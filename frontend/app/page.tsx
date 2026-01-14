"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { initData, migrateData } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [migrating, setMigrating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await initData();
      // Navigate to the root folder
      router.push(`/${result.root}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleMigrate = async () => {
    setMigrating(true);
    setError(null);
    try {
      const result = await migrateData();
      // Navigate to the root folder
      router.push(`/${result.root}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setMigrating(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-2rem)] flex flex-col items-center justify-center bg-background p-4">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Note Manager</h1>
          <p className="text-muted-foreground">
            A simple note-taking application
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            onClick={handleLoadData}
            disabled={loading || migrating}
            size="lg"
            className="min-w-[200px]"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Loading...
              </span>
            ) : (
              "Load Data"
            )}
          </Button>

          <Button
            onClick={handleMigrate}
            disabled={loading || migrating}
            size="lg"
            variant="secondary"
            className="min-w-[200px]"
          >
            {migrating ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Migrating...
              </span>
            ) : (
              "Migrate"
            )}
          </Button>
        </div>

        {error && <p className="text-destructive text-sm">{error}</p>}
      </div>
    </div>
  );
}
