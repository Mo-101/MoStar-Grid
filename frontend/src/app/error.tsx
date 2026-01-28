"use client";

import { useEffect } from "react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error("APP_ERROR_BOUNDARY:", error);
    }, [error]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen text-white bg-black">
            <div className="p-8 border border-red-500 rounded-lg bg-red-950/30">
                <h2 className="mb-4 text-2xl font-bold text-red-500">Something went wrong!</h2>
                <pre className="p-4 mb-4 overflow-auto text-sm bg-black rounded max-w-2xl">
                    {error instanceof Error ? error.stack : JSON.stringify(error, null, 2)}
                </pre>
                <button
                    className="px-4 py-2 text-black transition bg-red-500 rounded hover:bg-red-400"
                    onClick={
                        // Attempt to recover by trying to re-render the segment
                        () => reset()
                    }
                >
                    Try again
                </button>
            </div>
        </div>
    );
}
