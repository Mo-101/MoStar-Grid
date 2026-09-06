export type ModelCapability =
  | "GENERATIVE_TEXT"
  | "GENERATIVE_MULTIMODAL"
  | "EMBEDDING"
  | "CLASSIFIER"
  | "RERANKER"
  | "FORECASTER"
  | "SPECIALIST"
  | "AGENTIC"
  | "OTHER";

export interface ModelRuntimeDescriptor {
  runtimeId: string;
  modelId?: string;
  provider?: string;
  family?: string;
  capability: ModelCapability;
  transport: "LOCAL_LIBRARY" | "LOCAL_HTTP" | "REMOTE_HTTP" | "GRPC" | "SUBPROCESS" | "OTHER";
  production: boolean;
}

export interface RegisteredModelAdapter {
  adapterId: string;
  runtimeDescriptor: ModelRuntimeDescriptor;
  conduitOnly: true;
}

export const MODEL_INVOCATION_SCOPE = Object.freeze({
  scope: "ALL_PRESENT_AND_FUTURE_MODELS",
  prohibitedNameScoping: true,
  examplesAreNonExhaustive: true,
  law: "Any production component capable of model inference must be reachable only through MindConduit.",
} as const);
