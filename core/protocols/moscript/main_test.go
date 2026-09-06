package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"strings"
	"testing"
)

func enc(s string) string {
	x, e := encodeWord(s)
	if e != nil {
		panic(e)
	}
	return x
}
func cp(n int) string         { return string(rune(0x1F700 + n)) }
func srcLine(s string) []byte { return []byte(s + "\n") }

func compileSrc(t *testing.T, s string) (*Program, *BytecodeFile) {
	t.Helper()
	tok, e := lex([]byte(s))
	if e != nil {
		t.Fatal(e)
	}
	p, e := parse(tok)
	if e != nil {
		t.Fatal(e)
	}
	caps, e := checkProgram(p)
	if e != nil {
		t.Fatal(e)
	}
	bc, e := compileProgram(p, caps)
	if e != nil {
		t.Fatal(e)
	}
	return p, bc
}
func runBC(t *testing.T, bc *BytecodeFile, allow ...string) (string, any, error) {
	t.Helper()
	var out bytes.Buffer
	vm, e := newVM(bc, allow, 100000, 64, ".", &out)
	if e != nil {
		return "", nil, e
	}
	r, e := vm.run()
	return out.String(), r, e
}

func TestABI64(t *testing.T) {
	a := abiEntries()
	if len(a) != 64 {
		t.Fatalf("got %d", len(a))
	}
	if a[0].Meaning != "A" || a[25].Meaning != "Z" || a[26].Meaning != "0" || a[63].Meaning != "OR" {
		t.Fatal("ABI mapping broken")
	}
}
func TestRejectLatin(t *testing.T) {
	_, e := lex([]byte("A"))
	if e == nil || !strings.Contains(e.Error(), "MO000") {
		t.Fatalf("expected MO000, got %v", e)
	}
}
func TestArithmeticAndPrint(t *testing.T) {
	// X: 2 + 3 * 4 ; PRINT(X)
	s := enc("X") + cp(41) + cp(28) + cp(49) + cp(29) + cp(51) + cp(30) + cp(47) + "\n" + enc("PRINT") + cp(42) + enc("X") + cp(43) + cp(47)
	_, bc := compileSrc(t, s)
	out, _, e := runBC(t, bc)
	if e != nil {
		t.Fatal(e)
	}
	if out != "14\n" {
		t.Fatalf("out=%q", out)
	}
}
func TestFunctionWhile(t *testing.T) {
	// FUNCTION INC(A){ RETURN A+1; } X:0; WHILE X<3 { X=INC(X); } PRINT(X)
	s := enc("FUNCTION") + " " + enc("INC") + cp(42) + enc("A") + cp(43) + " " + cp(44) + "\n" +
		enc("RETURN") + " " + enc("A") + cp(49) + cp(27) + cp(47) + "\n" + cp(45) + "\n" +
		enc("X") + cp(41) + cp(26) + cp(47) + "\n" +
		enc("WHILE") + " " + enc("X") + cp(54) + cp(29) + " " + cp(44) + "\n" +
		enc("X") + cp(48) + enc("INC") + cp(42) + enc("X") + cp(43) + cp(47) + "\n" + cp(45) + "\n" +
		enc("PRINT") + cp(42) + enc("X") + cp(43) + cp(47)
	_, bc := compileSrc(t, s)
	out, _, e := runBC(t, bc)
	if e != nil {
		t.Fatal(e)
	}
	if out != "3\n" {
		t.Fatalf("out=%q", out)
	}
}
func TestGateDenyAllow(t *testing.T) {
	// TRUE -> PRINT("OK")
	ok, _ := encodeWord("OK")
	s := enc("TRUE") + cp(36) + enc("PRINT") + cp(42) + cp(60) + ok + cp(60) + cp(43) + cp(47)
	_, bc := compileSrc(t, s)
	_, _, e := runBC(t, bc)
	if e == nil || !strings.Contains(e.Error(), "MO008") {
		t.Fatalf("expected deny, got %v", e)
	}
	out, _, e := runBC(t, bc, "gate.execute")
	if e != nil {
		t.Fatal(e)
	}
	if out != "OK\n" {
		t.Fatalf("out=%q", out)
	}
}
func TestCanonicalRoundTrip(t *testing.T) {
	s := enc("X") + cp(41) + cp(27) + cp(28) + cp(49) + cp(29) + cp(47)
	p, _ := compileSrc(t, s)
	c := canonical(p)
	p2, _ := compileSrc(t, c)
	if programHash(p) != programHash(p2) {
		t.Fatalf("roundtrip hash mismatch")
	}
}
func TestBytecodeTamper(t *testing.T) {
	s := enc("X") + cp(41) + cp(27) + cp(47)
	_, bc := compileSrc(t, s)
	raw, _ := json.Marshal(bc)
	var z BytecodeFile
	if e := json.Unmarshal(raw, &z); e != nil {
		t.Fatal(e)
	}
	z.Main.Code[0].Arg = float64(9)
	if z.BytecodeHash == bytecodeDigest(&z) {
		t.Fatal("tamper not detected")
	}
}
func TestScrollSignature(t *testing.T) {
	s := enc("X") + cp(41) + cp(27) + cp(47)
	_, bc := compileSrc(t, s)
	pub, priv, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	sc, e := sealBC(bc, priv)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = verifyScroll(sc, pub); e != nil {
		t.Fatal(e)
	}
	sc.ProgramHash = "00" + sc.ProgramHash[2:]
	if _, e = verifyScroll(sc, pub); e == nil {
		t.Fatal("tampered scroll verified")
	}
}
func TestStepLimit(t *testing.T) {
	// WHILE TRUE {}
	s := enc("WHILE") + " " + enc("TRUE") + " " + cp(44) + cp(45)
	_, bc := compileSrc(t, s)
	var out bytes.Buffer
	vm, e := newVM(bc, nil, 50, 16, ".", &out)
	if e != nil {
		t.Fatal(e)
	}
	_, e = vm.run()
	if e == nil || !strings.Contains(e.Error(), "MO010") {
		t.Fatalf("expected MO010, got %v", e)
	}
}

func TestForwardFunctionCall(t *testing.T) {
	// X: INC(2); FUNCTION INC(A) { RETURN A+1; } PRINT(X)
	s := enc("X") + cp(41) + enc("INC") + cp(42) + cp(28) + cp(43) + cp(47) + "\n" +
		enc("FUNCTION") + " " + enc("INC") + cp(42) + enc("A") + cp(43) + " " + cp(44) + "\n" +
		enc("RETURN") + " " + enc("A") + cp(49) + cp(27) + cp(47) + "\n" + cp(45) + "\n" +
		enc("PRINT") + cp(42) + enc("X") + cp(43) + cp(47)
	_, bc := compileSrc(t, s)
	out, _, e := runBC(t, bc)
	if e != nil {
		t.Fatal(e)
	}
	if out != "3\n" {
		t.Fatalf("out=%q", out)
	}
}
func TestCapabilityManifestFromAlias(t *testing.T) {
	// F: CLOCK; F()
	s := enc("F") + cp(41) + enc("CLOCK") + cp(47) + "\n" + enc("F") + cp(42) + cp(43) + cp(47)
	_, bc := compileSrc(t, s)
	if len(bc.Capabilities) != 1 || bc.Capabilities[0] != "clock.read" {
		t.Fatalf("caps=%v", bc.Capabilities)
	}
	_, _, e := runBC(t, bc)
	if e == nil || !strings.Contains(e.Error(), "MO008") {
		t.Fatalf("expected capability denial, got %v", e)
	}
}
