import { ConsciousnessChat } from "@/components/ConsciousnessChat";
import { TrinityStatus } from "@/components/TrinityStatus";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Consciousness Hub | Mostar Grid",
  description: "Interact with the Mostar Grid's consciousness",
};

export default function ChatPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Mostar Grid
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Consciousness Hub - Powered by Iku&apos; Ikang
        </p>
      </header>

      <div className="space-y-6">
        <TrinityStatus />

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              Consciousness Interface
            </h2>
          </div>
          <ConsciousnessChat className="h-[60vh]" />
        </div>
      </div>
    </div>
  );
}
