import type { ModelRuntimeDescriptor, RegisteredModelAdapter } from "./model-runtime";

const MODEL_INVOCATION_CAPABILITY = Symbol("MOSTAR_GRID_MODEL_INVOCATION");

export class GridModelInvocationContext {
  private constructor(
    private readonly capability: symbol,
    readonly modelId: string,
    readonly bindingRoot: string,
    readonly snapshotDigest: string,
  ) {}
  static issueFromMindConduit(input: {
    modelId: string;
    bindingRoot: string;
    snapshotDigest: string;
  }): GridModelInvocationContext {
    return new GridModelInvocationContext(
      MODEL_INVOCATION_CAPABILITY,
      input.modelId,
      input.bindingRoot,
      input.snapshotDigest,
    );
  }
  assertValid(): void {
    if (this.capability !== MODEL_INVOCATION_CAPABILITY)
      throw new Error("DIRECT_MODEL_INVOCATION_FORBIDDEN");
  }
}

export interface GovernedModelAdapter<Request, Response> extends RegisteredModelAdapter {
  readonly descriptor: ModelRuntimeDescriptor;
  invoke(context: GridModelInvocationContext, request: Request): Promise<Response>;
}

export class GridModelAdapter<Request, Result> implements GovernedModelAdapter<Request, Result> {
  readonly conduitOnly = true as const;
  readonly runtimeDescriptor: ModelRuntimeDescriptor;
  constructor(
    readonly adapterId: string,
    readonly descriptor: ModelRuntimeDescriptor,
    private readonly runtime: { invoke(request: Request): Promise<Result> },
  ) {
    this.runtimeDescriptor = descriptor;
  }
  async invoke(ctx: GridModelInvocationContext, request: Request): Promise<Result> {
    if (!(ctx instanceof GridModelInvocationContext)) {
      throw new Error("DIRECT_MODEL_INVOCATION_FORBIDDEN");
    }
    ctx.assertValid();
    if (ctx.modelId !== this.descriptor.modelId) throw new Error("MODEL_CONTEXT_MISMATCH");
    return this.runtime.invoke(request);
  }
}
