# MoScript v0.1.0 Core Runtime

**Product build:** v0.1.1  
**A product of MoStar Intelligent System LTD**  
**Registration:** RC: 9753604


This is an actual native MoScript executable and source tree, built from the v0.1 RFC.

Implemented:
- Frozen 64-glyph ABI (`U+1F700`–`U+1F73F`)
- Strict UTF-8/core-glyph validation; Latin source is rejected
- Lexer and parser
- Definitions, assignment, expressions, lists, indexing
- `IF`/`ELSE`, `WHILE`, `FOR ... IN`, functions, `RETURN`, `BREAK`, `CONTINUE`
- Static semantic/type checks
- Canonical glyph pretty-printing and deterministic program identity
- Stack bytecode compiler (`.mobc`) with bytecode integrity hash
- Bounded VM with step/call/output/collection limits
- Deny-by-default capabilities
- `gate.execute`, `clock.read`, `filesystem.read`, `filesystem.write`
- Filesystem capability sandbox rooted at `--workspace`
- Ed25519 key generation, sealed `.moscroll` artifacts, signature verification, trusted-key execution
- Native Linux x86-64 and Windows x86-64 builds

This core runtime deliberately does not embed broker, shell, network, AI, ThroneLock, Resonance, or registry adapters. Those are external trust-domain integrations and should not be faked inside the language core.

## ABI

A-Z: U+1F700..U+1F719
0-9: U+1F71A..U+1F723

Frozen structural assignments:
- U+1F724 gate
- U+1F725 >=
- U+1F726 decimal join
- U+1F727 [
- U+1F728 ]
- U+1F729 define
- U+1F72A (
- U+1F72B )
- U+1F72C {
- U+1F72D }
- U+1F72E ,
- U+1F72F ;
- U+1F730 assignment
- U+1F731 +
- U+1F732 -
- U+1F733 *
- U+1F734 /
- U+1F735 %
- U+1F736 <
- U+1F737 >
- U+1F738 <=
- U+1F739 ==
- U+1F73A !=
- U+1F73B NOT
- U+1F73C string delimiter
- U+1F73D comment marker
- U+1F73E AND
- U+1F73F OR

## CLI

```text
moscript version
moscript abi
moscript check program.ms
moscript tokens program.ms
moscript ast program.ms
moscript canonical program.ms
moscript hash program.ms
moscript compile -o program.mobc program.ms
moscript run program.ms

moscript keygen --private private.key --public public.key
moscript seal --key private.key -o program.moscroll program.ms
moscript verify --pub public.key program.moscroll
moscript run-scroll --pub public.key program.moscroll
```

Capabilities must be explicitly enabled:
```text
moscript run --allow gate.execute program.ms
moscript run --allow clock.read program.ms
moscript run --allow filesystem.read --workspace ./sandbox program.ms
```

## Security properties

- Source cannot contain arbitrary non-core Unicode or Latin characters.
- No network or shell primitive exists in the runtime.
- External capabilities are denied by default.
- Filesystem access cannot escape the configured workspace root.
- Bytecode is integrity-checked before execution.
- Sealed scrolls use Ed25519 and can be pinned to a trusted public key.
- Execution is bounded by instruction and call-depth limits.

## Product Attribution

MoScript is a product of **MoStar Intelligent System LTD**, registration **RC: 9753604**.

This attribution update does not change the frozen MoScript v0.1 glyph ABI.
