export type QueryParams = Readonly<Record<string, unknown>>;

export interface Neo4jReadDriver {
  runRead<T>(
    cypher: string,
    params: QueryParams,
    options: Readonly<{ timeoutMs: number; maxRows: number }>,
  ): Promise<readonly T[]>;
}
export interface RegisteredQuery<P extends QueryParams, R> {
  readonly key: string;
  readonly cypher: string;
  readonly timeoutMs: number;
  readonly maxRows: number;
  readonly allowedOrigins: readonly string[];
  validateParams(value: unknown): asserts value is P;
  validateRows(value: unknown): asserts value is readonly R[];
}
export interface CypherRetrievalRequest {
  readonly query_key: string;
  readonly params: unknown;
  readonly requestOrigin: string;
}

export class SecondWoundViolation extends Error {
  readonly code = "SECOND_WOUND_VIOLATION";
  constructor(
    readonly reason:
      | "INVALID_RETRIEVAL_SHAPE"
      | "UNREGISTERED_QUERY"
      | "UNAUTHORIZED_QUERY_ORIGIN"
      | "INVALID_QUERY_PARAMS"
      | "QUERY_RESULT_LIMIT_EXCEEDED",
    readonly detail: string,
  ) {
    super(`${reason}: ${detail}`);
    this.name = "SecondWoundViolation";
  }
}

export class CanonicalQueryRegistry {
  readonly #queries = new Map<string, RegisteredQuery<QueryParams, unknown>>();
  #sealed = false;
  register<P extends QueryParams, R>(query: RegisteredQuery<P, R>): void {
    if (this.#sealed) throw new Error("QUERY_REGISTRY_ALREADY_SEALED");
    if (this.#queries.has(query.key)) throw new Error(`DUPLICATE_QUERY_KEY:${query.key}`);
    this.#queries.set(query.key, query as RegisteredQuery<QueryParams, unknown>);
  }
  seal(): void {
    if (!this.#queries.size) throw new Error("EMPTY_QUERY_REGISTRY");
    this.#sealed = true;
  }
  isSealed(): boolean {
    return this.#sealed;
  }
  get(key: string) {
    return this.#queries.get(key);
  }
}

export class CypherGuard {
  constructor(
    private readonly registry: CanonicalQueryRegistry,
    private readonly driver: Neo4jReadDriver,
  ) {}
  async retrieve<R>(input: CypherRetrievalRequest): Promise<readonly R[]> {
    this.assertStrictShape(input);
    if (!this.registry.isSealed())
      throw new SecondWoundViolation(
        "UNREGISTERED_QUERY",
        "Canonical query registry is not sealed.",
      );
    const template: RegisteredQuery<QueryParams, unknown> | undefined = this.registry.get(
      input.query_key,
    );
    if (!template)
      throw new SecondWoundViolation(
        "UNREGISTERED_QUERY",
        `No canon-approved query template for key=${JSON.stringify(input.query_key)}`,
      );
    if (!template.allowedOrigins.includes(input.requestOrigin))
      throw new SecondWoundViolation(
        "UNAUTHORIZED_QUERY_ORIGIN",
        `Origin ${input.requestOrigin} is denied.`,
      );
    try {
      template.validateParams(input.params);
    } catch (error) {
      throw new SecondWoundViolation(
        "INVALID_QUERY_PARAMS",
        error instanceof Error ? error.message : "Parameter validation failed.",
      );
    }
    const rows = await this.driver.runRead<R>(template.cypher, input.params as QueryParams, {
      timeoutMs: template.timeoutMs,
      maxRows: template.maxRows,
    });
    if (rows.length > template.maxRows)
      throw new SecondWoundViolation(
        "QUERY_RESULT_LIMIT_EXCEEDED",
        `${template.key} returned ${rows.length}; maximum=${template.maxRows}.`,
      );
    template.validateRows(rows);
    return rows;
  }
  private assertStrictShape(value: unknown): asserts value is CypherRetrievalRequest {
    if (!value || typeof value !== "object")
      throw new SecondWoundViolation(
        "INVALID_RETRIEVAL_SHAPE",
        "Retrieval request must be an object.",
      );
    const input = value as Record<string, unknown>;
    for (const forbidden of ["cypher", "query", "statement", "rawCypher", "raw_cypher"]) {
      if (forbidden in input)
        throw new SecondWoundViolation(
          "INVALID_RETRIEVAL_SHAPE",
          `Freeform query field ${forbidden} is forbidden.`,
        );
    }
    const allowed = new Set(["query_key", "params", "requestOrigin"]);
    for (const key of Object.keys(input))
      if (!allowed.has(key))
        throw new SecondWoundViolation(
          "INVALID_RETRIEVAL_SHAPE",
          `Unexpected retrieval field ${key}.`,
        );
    if (
      typeof input.query_key !== "string" ||
      !input.query_key ||
      typeof input.requestOrigin !== "string" ||
      !input.requestOrigin
    )
      throw new SecondWoundViolation(
        "INVALID_RETRIEVAL_SHAPE",
        "query_key and requestOrigin are required strings.",
      );
  }
}
