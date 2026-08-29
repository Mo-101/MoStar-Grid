package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"io"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const (
	Version        = "0.1.0" // language/runtime compatibility version
	BuildVersion   = "0.1.1" // product build version
	ProductName    = "MoScript"
	Producer       = "MoStar Intelligent System LTD"
	Registration   = "RC: 9753604"
	LanguageABI    = "MOSCRIPT_GLYPH_ABI_V0_1"
	CoreStart      = rune(0x1F700)
	CoreEnd        = rune(0x1F73F)
	DefaultSteps   = 1_000_000
	DefaultDepth   = 128
	MaxCollection  = 100_000
	MaxOutputBytes = 1_048_576
)

// ---------------- ABI ----------------

type ABIEntry struct {
	Index     int    `json:"index"`
	Codepoint string `json:"codepoint"`
	Glyph     string `json:"glyph"`
	Class     string `json:"class"`
	Meaning   string `json:"meaning"`
}

var structural = map[rune]string{
	0x1F724: "GATE",
	0x1F725: "GTE",
	0x1F726: "DECIMAL_JOIN",
	0x1F727: "LBRACKET",
	0x1F728: "RBRACKET",
	0x1F729: "DEFINE",
	0x1F72A: "LPAREN",
	0x1F72B: "RPAREN",
	0x1F72C: "LBRACE",
	0x1F72D: "RBRACE",
	0x1F72E: "COMMA",
	0x1F72F: "SEMICOLON",
	0x1F730: "ASSIGN",
	0x1F731: "PLUS",
	0x1F732: "MINUS",
	0x1F733: "STAR",
	0x1F734: "SLASH",
	0x1F735: "MOD",
	0x1F736: "LT",
	0x1F737: "GT",
	0x1F738: "LTE",
	0x1F739: "EQ",
	0x1F73A: "NE",
	0x1F73B: "NOT",
	0x1F73C: "STRING",
	0x1F73D: "COMMENT",
	0x1F73E: "AND",
	0x1F73F: "OR",
}

func abiEntries() []ABIEntry {
	out := make([]ABIEntry, 0, 64)
	for i := 0; i < 64; i++ {
		r := CoreStart + rune(i)
		class, meaning := "", ""
		switch {
		case i < 26:
			class = "letter"
			meaning = string(rune('A' + i))
		case i < 36:
			class = "digit"
			meaning = strconv.Itoa(i - 26)
		default:
			class = "structural"
			meaning = structural[r]
		}
		out = append(out, ABIEntry{
			Index: i, Codepoint: fmt.Sprintf("U+%04X", r), Glyph: string(r), Class: class, Meaning: meaning,
		})
	}
	return out
}

func abiHash() string {
	b, _ := json.Marshal(abiEntries())
	h := sha256.Sum256(append([]byte(LanguageABI+"\n"), b...))
	return hex.EncodeToString(h[:])
}

func encodeWord(s string) (string, error) {
	var b strings.Builder
	for _, r := range strings.ToUpper(s) {
		switch {
		case r >= 'A' && r <= 'Z':
			b.WriteRune(CoreStart + (r - 'A'))
		case r >= '0' && r <= '9':
			b.WriteRune(CoreStart + 26 + (r - '0'))
		case r == ' ':
			b.WriteRune(' ')
		default:
			return "", fmt.Errorf("cannot encode %q in core word alphabet", string(r))
		}
	}
	return b.String(), nil
}

func decodeLetterDigit(r rune) (string, bool) {
	switch {
	case r >= CoreStart && r <= CoreStart+25:
		return string(rune('A') + (r - CoreStart)), true
	case r >= CoreStart+26 && r <= CoreStart+35:
		return string(rune('0') + (r - (CoreStart + 26))), true
	}
	return "", false
}

// ---------------- Errors & positions ----------------

type Pos struct {
	Line   int `json:"line"`
	Column int `json:"column"`
	Byte   int `json:"byte"`
}

type MoError struct {
	Code    string `json:"code"`
	Phase   string `json:"phase"`
	Message string `json:"message"`
	Pos     *Pos   `json:"source,omitempty"`
}

func (e *MoError) Error() string {
	if e.Pos != nil {
		return fmt.Sprintf("%s [%s] line %d col %d: %s", e.Code, e.Phase, e.Pos.Line, e.Pos.Column, e.Message)
	}
	return fmt.Sprintf("%s [%s]: %s", e.Code, e.Phase, e.Message)
}

func moerr(code, phase, msg string, pos *Pos) error {
	return &MoError{Code: code, Phase: phase, Message: msg, Pos: pos}
}

// ---------------- Lexer ----------------

type TokenKind string

const (
	TKEOF      TokenKind = "EOF"
	TKNewline  TokenKind = "NEWLINE"
	TKIdent    TokenKind = "IDENT"
	TKNumber   TokenKind = "NUMBER"
	TKString   TokenKind = "STRING"
	TKTrue     TokenKind = "TRUE"
	TKFalse    TokenKind = "FALSE"
	TKNull     TokenKind = "NULL"
	TKIf       TokenKind = "IF"
	TKElse     TokenKind = "ELSE"
	TKWhile    TokenKind = "WHILE"
	TKFor      TokenKind = "FOR"
	TKIn       TokenKind = "IN"
	TKFunction TokenKind = "FUNCTION"
	TKReturn   TokenKind = "RETURN"
	TKBreak    TokenKind = "BREAK"
	TKContinue TokenKind = "CONTINUE"
)

type Token struct {
	Kind   TokenKind `json:"kind"`
	Lexeme string    `json:"lexeme,omitempty"`
	Value  string    `json:"value,omitempty"`
	Pos    Pos       `json:"pos"`
}

var reserved = map[string]TokenKind{
	"IF": TKIf, "ELSE": TKElse, "WHILE": TKWhile, "FOR": TKFor, "IN": TKIn,
	"FUNCTION": TKFunction, "RETURN": TKReturn, "BREAK": TKBreak, "CONTINUE": TKContinue,
	"TRUE": TKTrue, "FALSE": TKFalse, "NULL": TKNull,
}

func lex(src []byte) ([]Token, error) {
	if !utf8.Valid(src) {
		return nil, moerr("MO000", "lex", "invalid UTF-8", nil)
	}
	runes := []rune(string(src))
	tokens := []Token{}
	line, col, byteOff := 1, 1, 0

	pos := func() Pos { return Pos{Line: line, Column: col, Byte: byteOff} }
	advance := func(r rune) {
		byteOff += utf8.RuneLen(r)
		if r == '\n' {
			line++
			col = 1
		} else {
			col++
		}
	}

	for i := 0; i < len(runes); {
		r := runes[i]
		p := pos()
		if r == '\r' {
			return nil, moerr("MO000", "lex", "CR line endings are prohibited; use LF", &p)
		}
		if r == '\n' {
			tokens = append(tokens, Token{Kind: TKNewline, Pos: p})
			advance(r)
			i++
			continue
		}
		if r == ' ' || r == '\t' {
			advance(r)
			i++
			continue
		}
		if r < CoreStart || r > CoreEnd {
			return nil, moerr("MO000", "lex", fmt.Sprintf("non-core glyph %q (U+%04X)", string(r), r), &p)
		}

		if r == 0x1F73D { // comment marker through newline
			for i < len(runes) && runes[i] != '\n' {
				advance(runes[i])
				i++
			}
			continue
		}

		if r >= CoreStart && r <= CoreStart+25 {
			start := i
			var decoded strings.Builder
			for i < len(runes) {
				x := runes[i]
				if x >= CoreStart && x <= CoreStart+25 {
					s, _ := decodeLetterDigit(x)
					decoded.WriteString(s)
				} else if x >= CoreStart+26 && x <= CoreStart+35 {
					s, _ := decodeLetterDigit(x)
					decoded.WriteString(s)
				} else {
					break
				}
				advance(x)
				i++
			}
			val := decoded.String()
			kind := TKIdent
			if k, ok := reserved[val]; ok {
				kind = k
			}
			tokens = append(tokens, Token{Kind: kind, Lexeme: string(runes[start:i]), Value: val, Pos: p})
			continue
		}

		if r >= CoreStart+26 && r <= CoreStart+35 {
			start := i
			var decoded strings.Builder
			seenJoin := false
			for i < len(runes) {
				x := runes[i]
				if x >= CoreStart+26 && x <= CoreStart+35 {
					s, _ := decodeLetterDigit(x)
					decoded.WriteString(s)
					advance(x)
					i++
					continue
				}
				if x == 0x1F726 && !seenJoin {
					seenJoin = true
					decoded.WriteByte('.')
					advance(x)
					i++
					continue
				}
				break
			}
			raw := decoded.String()
			if strings.HasSuffix(raw, ".") {
				return nil, moerr("MO001", "lex", "malformed decimal", &p)
			}
			tokens = append(tokens, Token{Kind: TKNumber, Lexeme: string(runes[start:i]), Value: raw, Pos: p})
			continue
		}

		if r == 0x1F73C { // string delimiter
			advance(r)
			i++
			var decoded strings.Builder
			start := i
			for i < len(runes) && runes[i] != 0x1F73C {
				x := runes[i]
				if x == '\n' || x == '\r' {
					return nil, moerr("MO002", "lex", "unterminated string", &p)
				}
				if x == ' ' {
					decoded.WriteRune(' ')
				} else if s, ok := decodeLetterDigit(x); ok {
					decoded.WriteString(s)
				} else {
					return nil, moerr("MO000", "lex", "string contains unsupported glyph; v0.1 strings allow encoded A-Z, 0-9, and spaces", &p)
				}
				advance(x)
				i++
			}
			if i >= len(runes) {
				return nil, moerr("MO002", "lex", "unterminated string", &p)
			}
			_ = start
			advance(runes[i])
			i++
			tokens = append(tokens, Token{Kind: TKString, Value: decoded.String(), Pos: p})
			continue
		}

		if name, ok := structural[r]; ok {
			tokens = append(tokens, Token{Kind: TokenKind(name), Lexeme: string(r), Pos: p})
			advance(r)
			i++
			continue
		}
		return nil, moerr("MO000", "lex", "unassigned core glyph", &p)
	}
	tokens = append(tokens, Token{Kind: TKEOF, Pos: pos()})
	return tokens, nil
}

// ---------------- AST ----------------

type Expr interface{ exprNode() }
type Stmt interface{ stmtNode() }

type Program struct {
	Kind       string `json:"kind"`
	Statements []Stmt `json:"statements"`
}

type Identifier struct {
	Kind string `json:"kind"`
	Name string `json:"name"`
	Pos  Pos    `json:"pos"`
}

func (*Identifier) exprNode() {}

type NumberLiteral struct {
	Kind    string  `json:"kind"`
	Raw     string  `json:"raw"`
	Value   float64 `json:"value"`
	Integer bool    `json:"integer"`
	Pos     Pos     `json:"pos"`
}

func (*NumberLiteral) exprNode() {}

type StringLiteral struct {
	Kind  string `json:"kind"`
	Value string `json:"value"`
	Pos   Pos    `json:"pos"`
}

func (*StringLiteral) exprNode() {}

type BoolLiteral struct {
	Kind  string `json:"kind"`
	Value bool   `json:"value"`
	Pos   Pos    `json:"pos"`
}

func (*BoolLiteral) exprNode() {}

type NullLiteral struct {
	Kind string `json:"kind"`
	Pos  Pos    `json:"pos"`
}

func (*NullLiteral) exprNode() {}

type ListLiteral struct {
	Kind  string `json:"kind"`
	Items []Expr `json:"items"`
	Pos   Pos    `json:"pos"`
}

func (*ListLiteral) exprNode() {}

type UnaryExpr struct {
	Kind  string `json:"kind"`
	Op    string `json:"operator"`
	Right Expr   `json:"right"`
	Pos   Pos    `json:"pos"`
}

func (*UnaryExpr) exprNode() {}

type BinaryExpr struct {
	Kind  string `json:"kind"`
	Op    string `json:"operator"`
	Left  Expr   `json:"left"`
	Right Expr   `json:"right"`
	Pos   Pos    `json:"pos"`
}

func (*BinaryExpr) exprNode() {}

type CallExpr struct {
	Kind   string `json:"kind"`
	Callee Expr   `json:"callee"`
	Args   []Expr `json:"args"`
	Pos    Pos    `json:"pos"`
}

func (*CallExpr) exprNode() {}

type IndexExpr struct {
	Kind   string `json:"kind"`
	Target Expr   `json:"target"`
	Index  Expr   `json:"index"`
	Pos    Pos    `json:"pos"`
}

func (*IndexExpr) exprNode() {}

type DefineStmt struct {
	Kind  string `json:"kind"`
	Name  string `json:"name"`
	Value Expr   `json:"value"`
	Pos   Pos    `json:"pos"`
}

func (*DefineStmt) stmtNode() {}

type AssignStmt struct {
	Kind  string `json:"kind"`
	Name  string `json:"name"`
	Value Expr   `json:"value"`
	Pos   Pos    `json:"pos"`
}

func (*AssignStmt) stmtNode() {}

type ExprStmt struct {
	Kind string `json:"kind"`
	Expr Expr   `json:"expression"`
	Pos  Pos    `json:"pos"`
}

func (*ExprStmt) stmtNode() {}

type GateStmt struct {
	Kind      string `json:"kind"`
	Condition Expr   `json:"condition"`
	Target    Expr   `json:"target"`
	Pos       Pos    `json:"pos"`
}

func (*GateStmt) stmtNode() {}

type BlockStmt struct {
	Kind       string `json:"kind"`
	Statements []Stmt `json:"statements"`
	Pos        Pos    `json:"pos"`
}

func (*BlockStmt) stmtNode() {}

type IfStmt struct {
	Kind      string     `json:"kind"`
	Condition Expr       `json:"condition"`
	Then      *BlockStmt `json:"then"`
	Else      *BlockStmt `json:"else,omitempty"`
	Pos       Pos        `json:"pos"`
}

func (*IfStmt) stmtNode() {}

type WhileStmt struct {
	Kind      string     `json:"kind"`
	Condition Expr       `json:"condition"`
	Body      *BlockStmt `json:"body"`
	Pos       Pos        `json:"pos"`
}

func (*WhileStmt) stmtNode() {}

type ForStmt struct {
	Kind     string     `json:"kind"`
	Name     string     `json:"name"`
	Iterable Expr       `json:"iterable"`
	Body     *BlockStmt `json:"body"`
	Pos      Pos        `json:"pos"`
}

func (*ForStmt) stmtNode() {}

type FunctionStmt struct {
	Kind   string     `json:"kind"`
	Name   string     `json:"name"`
	Params []string   `json:"params"`
	Body   *BlockStmt `json:"body"`
	Pos    Pos        `json:"pos"`
}

func (*FunctionStmt) stmtNode() {}

type ReturnStmt struct {
	Kind  string `json:"kind"`
	Value Expr   `json:"value,omitempty"`
	Pos   Pos    `json:"pos"`
}

func (*ReturnStmt) stmtNode() {}

type BreakStmt struct {
	Kind string `json:"kind"`
	Pos  Pos    `json:"pos"`
}

func (*BreakStmt) stmtNode() {}

type ContinueStmt struct {
	Kind string `json:"kind"`
	Pos  Pos    `json:"pos"`
}

func (*ContinueStmt) stmtNode() {}

// ---------------- Parser ----------------

type Parser struct {
	t []Token
	i int
}

func parse(tokens []Token) (*Program, error) {
	p := &Parser{t: tokens}
	out := &Program{Kind: "Program"}
	p.skipSeps()
	for !p.at(TKEOF) {
		s, err := p.statement()
		if err != nil {
			return nil, err
		}
		out.Statements = append(out.Statements, s)
		p.skipSeps()
	}
	return out, nil
}
func (p *Parser) cur() Token          { return p.t[p.i] }
func (p *Parser) at(k TokenKind) bool { return p.cur().Kind == k }
func (p *Parser) next() Token {
	x := p.cur()
	if p.i < len(p.t)-1 {
		p.i++
	}
	return x
}
func (p *Parser) match(k ...TokenKind) bool {
	for _, x := range k {
		if p.at(x) {
			p.next()
			return true
		}
	}
	return false
}
func (p *Parser) need(k TokenKind, msg string) (Token, error) {
	if !p.at(k) {
		c := p.cur()
		return Token{}, moerr("MO002", "parse", msg, &c.Pos)
	}
	return p.next(), nil
}
func (p *Parser) skipSeps() {
	for p.match(TKNewline, TokenKind("SEMICOLON")) {
	}
}
func (p *Parser) endStmt() error {
	if p.match(TokenKind("SEMICOLON"), TKNewline, TKEOF) {
		p.skipSeps()
		return nil
	}
	if p.at(TokenKind("RBRACE")) {
		return nil
	}
	c := p.cur()
	return moerr("MO002", "parse", "expected statement terminator", &c.Pos)
}

func (p *Parser) statement() (Stmt, error) {
	switch p.cur().Kind {
	case TKIf:
		return p.ifStmt()
	case TKWhile:
		return p.whileStmt()
	case TKFor:
		return p.forStmt()
	case TKFunction:
		return p.functionStmt()
	case TKReturn:
		return p.returnStmt()
	case TKBreak:
		t := p.next()
		if err := p.endStmt(); err != nil {
			return nil, err
		}
		return &BreakStmt{Kind: "BreakStatement", Pos: t.Pos}, nil
	case TKContinue:
		t := p.next()
		if err := p.endStmt(); err != nil {
			return nil, err
		}
		return &ContinueStmt{Kind: "ContinueStatement", Pos: t.Pos}, nil
	}
	if p.at(TKIdent) && p.i+1 < len(p.t) {
		if p.t[p.i+1].Kind == TokenKind("DEFINE") {
			name := p.next()
			p.next()
			e, err := p.expression(0)
			if err != nil {
				return nil, err
			}
			if err = p.endStmt(); err != nil {
				return nil, err
			}
			return &DefineStmt{Kind: "Definition", Name: name.Value, Value: e, Pos: name.Pos}, nil
		}
		if p.t[p.i+1].Kind == TokenKind("ASSIGN") {
			name := p.next()
			p.next()
			e, err := p.expression(0)
			if err != nil {
				return nil, err
			}
			if err = p.endStmt(); err != nil {
				return nil, err
			}
			return &AssignStmt{Kind: "Assignment", Name: name.Value, Value: e, Pos: name.Pos}, nil
		}
	}
	e, err := p.expression(0)
	if err != nil {
		return nil, err
	}
	if p.match(TokenKind("GATE")) {
		target, err := p.expression(0)
		if err != nil {
			return nil, err
		}
		if err = p.endStmt(); err != nil {
			return nil, err
		}
		return &GateStmt{Kind: "GateStatement", Condition: e, Target: target, Pos: p.cur().Pos}, nil
	}
	if err = p.endStmt(); err != nil {
		return nil, err
	}
	return &ExprStmt{Kind: "ExpressionStatement", Expr: e, Pos: p.cur().Pos}, nil
}

func (p *Parser) block() (*BlockStmt, error) {
	t, err := p.need(TokenKind("LBRACE"), "expected block open")
	if err != nil {
		return nil, err
	}
	b := &BlockStmt{Kind: "Block", Pos: t.Pos}
	p.skipSeps()
	for !p.at(TokenKind("RBRACE")) && !p.at(TKEOF) {
		s, err := p.statement()
		if err != nil {
			return nil, err
		}
		b.Statements = append(b.Statements, s)
		p.skipSeps()
	}
	if _, err = p.need(TokenKind("RBRACE"), "expected block close"); err != nil {
		return nil, err
	}
	return b, nil
}

func (p *Parser) ifStmt() (Stmt, error) {
	t := p.next()
	cond, err := p.expression(0)
	if err != nil {
		return nil, err
	}
	p.skipSeps()
	then, err := p.block()
	if err != nil {
		return nil, err
	}
	p.skipSeps()
	var els *BlockStmt
	if p.match(TKElse) {
		p.skipSeps()
		els, err = p.block()
		if err != nil {
			return nil, err
		}
	}
	return &IfStmt{Kind: "IfStatement", Condition: cond, Then: then, Else: els, Pos: t.Pos}, nil
}
func (p *Parser) whileStmt() (Stmt, error) {
	t := p.next()
	cond, err := p.expression(0)
	if err != nil {
		return nil, err
	}
	p.skipSeps()
	body, err := p.block()
	if err != nil {
		return nil, err
	}
	return &WhileStmt{Kind: "WhileStatement", Condition: cond, Body: body, Pos: t.Pos}, nil
}
func (p *Parser) forStmt() (Stmt, error) {
	t := p.next()
	name, err := p.need(TKIdent, "expected loop identifier")
	if err != nil {
		return nil, err
	}
	if _, err = p.need(TKIn, "expected IN"); err != nil {
		return nil, err
	}
	iter, err := p.expression(0)
	if err != nil {
		return nil, err
	}
	p.skipSeps()
	body, err := p.block()
	if err != nil {
		return nil, err
	}
	return &ForStmt{Kind: "ForStatement", Name: name.Value, Iterable: iter, Body: body, Pos: t.Pos}, nil
}
func (p *Parser) functionStmt() (Stmt, error) {
	t := p.next()
	name, err := p.need(TKIdent, "expected function name")
	if err != nil {
		return nil, err
	}
	if _, err = p.need(TokenKind("LPAREN"), "expected function parameter list"); err != nil {
		return nil, err
	}
	var params []string
	if !p.at(TokenKind("RPAREN")) {
		for {
			x, e := p.need(TKIdent, "expected parameter name")
			if e != nil {
				return nil, e
			}
			params = append(params, x.Value)
			if !p.match(TokenKind("COMMA")) {
				break
			}
		}
	}
	if _, err = p.need(TokenKind("RPAREN"), "expected ')'"); err != nil {
		return nil, err
	}
	p.skipSeps()
	body, err := p.block()
	if err != nil {
		return nil, err
	}
	return &FunctionStmt{Kind: "FunctionDeclaration", Name: name.Value, Params: params, Body: body, Pos: t.Pos}, nil
}
func (p *Parser) returnStmt() (Stmt, error) {
	t := p.next()
	if p.at(TKNewline) || p.at(TokenKind("SEMICOLON")) || p.at(TokenKind("RBRACE")) || p.at(TKEOF) {
		if !p.at(TokenKind("RBRACE")) {
			if err := p.endStmt(); err != nil {
				return nil, err
			}
		}
		return &ReturnStmt{Kind: "ReturnStatement", Pos: t.Pos}, nil
	}
	v, err := p.expression(0)
	if err != nil {
		return nil, err
	}
	if err = p.endStmt(); err != nil {
		return nil, err
	}
	return &ReturnStmt{Kind: "ReturnStatement", Value: v, Pos: t.Pos}, nil
}

var prec = map[TokenKind]int{
	TokenKind("OR"): 1, TokenKind("AND"): 2,
	TokenKind("EQ"): 3, TokenKind("NE"): 3,
	TokenKind("LT"): 4, TokenKind("LTE"): 4, TokenKind("GT"): 4, TokenKind("GTE"): 4,
	TokenKind("PLUS"): 5, TokenKind("MINUS"): 5,
	TokenKind("STAR"): 6, TokenKind("SLASH"): 6, TokenKind("MOD"): 6,
}
var opName = map[TokenKind]string{
	TokenKind("OR"): "or", TokenKind("AND"): "and", TokenKind("EQ"): "eq", TokenKind("NE"): "ne",
	TokenKind("LT"): "lt", TokenKind("LTE"): "lte", TokenKind("GT"): "gt", TokenKind("GTE"): "gte",
	TokenKind("PLUS"): "add", TokenKind("MINUS"): "sub", TokenKind("STAR"): "mul", TokenKind("SLASH"): "div", TokenKind("MOD"): "mod",
}

func (p *Parser) expression(min int) (Expr, error) {
	left, err := p.prefix()
	if err != nil {
		return nil, err
	}
	for {
		if p.at(TokenKind("LPAREN")) {
			if 8 < min {
				break
			}
			callPos := p.cur().Pos
			p.next()
			var args []Expr
			if !p.at(TokenKind("RPAREN")) {
				for {
					a, e := p.expression(0)
					if e != nil {
						return nil, e
					}
					args = append(args, a)
					if !p.match(TokenKind("COMMA")) {
						break
					}
				}
			}
			if _, e := p.need(TokenKind("RPAREN"), "expected ')' after arguments"); e != nil {
				return nil, e
			}
			left = &CallExpr{Kind: "CallExpression", Callee: left, Args: args, Pos: callPos}
			continue
		}
		if p.at(TokenKind("LBRACKET")) {
			if 8 < min {
				break
			}
			q := p.next()
			idx, e := p.expression(0)
			if e != nil {
				return nil, e
			}
			if _, e = p.need(TokenKind("RBRACKET"), "expected ']'"); e != nil {
				return nil, e
			}
			left = &IndexExpr{Kind: "IndexExpression", Target: left, Index: idx, Pos: q.Pos}
			continue
		}
		pr, ok := prec[p.cur().Kind]
		if !ok || pr < min {
			break
		}
		o := p.next()
		right, e := p.expression(pr + 1)
		if e != nil {
			return nil, e
		}
		left = &BinaryExpr{Kind: "BinaryExpression", Op: opName[o.Kind], Left: left, Right: right, Pos: o.Pos}
	}
	return left, nil
}

func (p *Parser) prefix() (Expr, error) {
	t := p.next()
	switch t.Kind {
	case TKIdent:
		return &Identifier{Kind: "Identifier", Name: t.Value, Pos: t.Pos}, nil
	case TKNumber:
		v, e := strconv.ParseFloat(t.Value, 64)
		if e != nil {
			return nil, moerr("MO001", "parse", "malformed number", &t.Pos)
		}
		return &NumberLiteral{Kind: "NumberLiteral", Raw: t.Value, Value: v, Integer: !strings.Contains(t.Value, "."), Pos: t.Pos}, nil
	case TKString:
		return &StringLiteral{Kind: "StringLiteral", Value: t.Value, Pos: t.Pos}, nil
	case TKTrue:
		return &BoolLiteral{Kind: "BooleanLiteral", Value: true, Pos: t.Pos}, nil
	case TKFalse:
		return &BoolLiteral{Kind: "BooleanLiteral", Value: false, Pos: t.Pos}, nil
	case TKNull:
		return &NullLiteral{Kind: "NullLiteral", Pos: t.Pos}, nil
	case TokenKind("MINUS"):
		r, e := p.expression(7)
		if e != nil {
			return nil, e
		}
		return &UnaryExpr{Kind: "UnaryExpression", Op: "neg", Right: r, Pos: t.Pos}, nil
	case TokenKind("NOT"):
		r, e := p.expression(7)
		if e != nil {
			return nil, e
		}
		return &UnaryExpr{Kind: "UnaryExpression", Op: "not", Right: r, Pos: t.Pos}, nil
	case TokenKind("LPAREN"):
		e, er := p.expression(0)
		if er != nil {
			return nil, er
		}
		if _, er = p.need(TokenKind("RPAREN"), "expected ')'"); er != nil {
			return nil, er
		}
		return e, nil
	case TokenKind("LBRACKET"):
		var xs []Expr
		if !p.at(TokenKind("RBRACKET")) {
			for {
				x, e := p.expression(0)
				if e != nil {
					return nil, e
				}
				xs = append(xs, x)
				if !p.match(TokenKind("COMMA")) {
					break
				}
			}
		}
		if _, e := p.need(TokenKind("RBRACKET"), "expected ']'"); e != nil {
			return nil, e
		}
		return &ListLiteral{Kind: "ListLiteral", Items: xs, Pos: t.Pos}, nil
	}
	return nil, moerr("MO002", "parse", "expected expression", &t.Pos)
}

// ---------------- Static checker ----------------

type Type string

const (
	TAny      Type = "Any"
	TInt      Type = "Integer"
	TDecimal  Type = "Decimal"
	TBool     Type = "Boolean"
	TText     Type = "Text"
	TNull     Type = "Null"
	TList     Type = "List"
	TFunction Type = "Function"
)

type Checker struct {
	scopes   []map[string]Type
	loop     int
	function int
	required map[string]bool
}

func checkProgram(p *Program) ([]string, error) {
	c := &Checker{scopes: []map[string]Type{{}}, required: map[string]bool{}}
	for _, b := range []string{"PRINT", "LEN", "ABS", "MIN", "MAX", "CLOCK", "READFILE", "WRITEFILE"} {
		c.scopes[0][b] = TFunction
	}
	for _, s := range p.Statements {
		if f, ok := s.(*FunctionStmt); ok {
			if _, exists := c.scopes[0][f.Name]; exists {
				return nil, moerr("MO004", "typecheck", "duplicate definition "+f.Name, &f.Pos)
			}
			c.scopes[0][f.Name] = TFunction
		}
	}
	for _, s := range p.Statements {
		if err := c.stmt(s); err != nil {
			return nil, err
		}
	}
	var caps []string
	for k := range c.required {
		caps = append(caps, k)
	}
	sort.Strings(caps)
	return caps, nil
}
func (c *Checker) lookup(n string) (Type, bool) {
	for i := len(c.scopes) - 1; i >= 0; i-- {
		if t, ok := c.scopes[i][n]; ok {
			return t, true
		}
	}
	return "", false
}
func (c *Checker) define(n string, t Type, p Pos) error {
	m := c.scopes[len(c.scopes)-1]
	if _, ok := m[n]; ok {
		return moerr("MO004", "typecheck", "duplicate definition "+n, &p)
	}
	m[n] = t
	return nil
}
func (c *Checker) stmt(s Stmt) error {
	switch x := s.(type) {
	case *DefineStmt:
		t, e := c.expr(x.Value)
		if e != nil {
			return e
		}
		return c.define(x.Name, t, x.Pos)
	case *AssignStmt:
		if _, ok := c.lookup(x.Name); !ok {
			return moerr("MO003", "typecheck", "unknown identifier "+x.Name, &x.Pos)
		}
		_, e := c.expr(x.Value)
		return e
	case *ExprStmt:
		_, e := c.expr(x.Expr)
		return e
	case *GateStmt:
		t, e := c.expr(x.Condition)
		if e != nil {
			return e
		}
		if t != TBool && t != TAny {
			return moerr("MO005", "typecheck", "gate condition must be Boolean", &x.Pos)
		}
		c.required["gate.execute"] = true
		_, e = c.expr(x.Target)
		return e
	case *BlockStmt:
		for _, z := range x.Statements {
			if e := c.stmt(z); e != nil {
				return e
			}
		}
		return nil
	case *IfStmt:
		t, e := c.expr(x.Condition)
		if e != nil {
			return e
		}
		if t != TBool && t != TAny {
			return moerr("MO005", "typecheck", "if condition must be Boolean", &x.Pos)
		}
		if e = c.stmt(x.Then); e != nil {
			return e
		}
		if x.Else != nil {
			return c.stmt(x.Else)
		}
		return nil
	case *WhileStmt:
		t, e := c.expr(x.Condition)
		if e != nil {
			return e
		}
		if t != TBool && t != TAny {
			return moerr("MO005", "typecheck", "while condition must be Boolean", &x.Pos)
		}
		c.loop++
		e = c.stmt(x.Body)
		c.loop--
		return e
	case *ForStmt:
		t, e := c.expr(x.Iterable)
		if e != nil {
			return e
		}
		if t != TList && t != TAny {
			return moerr("MO005", "typecheck", "for iterable must be List", &x.Pos)
		}
		c.scopes = append(c.scopes, map[string]Type{x.Name: TAny})
		c.loop++
		e = c.stmt(x.Body)
		c.loop--
		c.scopes = c.scopes[:len(c.scopes)-1]
		return e
	case *FunctionStmt:
		c.scopes = append(c.scopes, map[string]Type{})
		for _, p := range x.Params {
			c.scopes[len(c.scopes)-1][p] = TAny
		}
		c.function++
		e := c.stmt(x.Body)
		c.function--
		c.scopes = c.scopes[:len(c.scopes)-1]
		return e
	case *ReturnStmt:
		if c.function == 0 {
			return moerr("MO002", "typecheck", "return outside function", &x.Pos)
		}
		if x.Value != nil {
			_, e := c.expr(x.Value)
			return e
		}
		return nil
	case *BreakStmt:
		if c.loop == 0 {
			return moerr("MO002", "typecheck", "break outside loop", &x.Pos)
		}
		return nil
	case *ContinueStmt:
		if c.loop == 0 {
			return moerr("MO002", "typecheck", "continue outside loop", &x.Pos)
		}
		return nil
	}
	return errors.New("internal checker error")
}
func isNum(t Type) bool { return t == TInt || t == TDecimal || t == TAny }
func (c *Checker) expr(e Expr) (Type, error) {
	switch x := e.(type) {
	case *Identifier:
		switch x.Name {
		case "CLOCK":
			c.required["clock.read"] = true
		case "READFILE":
			c.required["filesystem.read"] = true
		case "WRITEFILE":
			c.required["filesystem.write"] = true
		}
		t, ok := c.lookup(x.Name)
		if !ok {
			return "", moerr("MO003", "typecheck", "unknown identifier "+x.Name, &x.Pos)
		}
		return t, nil
	case *NumberLiteral:
		if x.Integer {
			return TInt, nil
		}
		return TDecimal, nil
	case *StringLiteral:
		return TText, nil
	case *BoolLiteral:
		return TBool, nil
	case *NullLiteral:
		return TNull, nil
	case *ListLiteral:
		for _, z := range x.Items {
			if _, e := c.expr(z); e != nil {
				return "", e
			}
		}
		return TList, nil
	case *UnaryExpr:
		t, e := c.expr(x.Right)
		if e != nil {
			return "", e
		}
		if x.Op == "neg" && !isNum(t) {
			return "", moerr("MO005", "typecheck", "unary '-' requires number", &x.Pos)
		}
		if x.Op == "not" && t != TBool && t != TAny {
			return "", moerr("MO005", "typecheck", "NOT requires Boolean", &x.Pos)
		}
		if x.Op == "not" {
			return TBool, nil
		}
		return t, nil
	case *BinaryExpr:
		a, e1 := c.expr(x.Left)
		if e1 != nil {
			return "", e1
		}
		b, e2 := c.expr(x.Right)
		if e2 != nil {
			return "", e2
		}
		switch x.Op {
		case "add":
			if a == TText && b == TText {
				return TText, nil
			}
			fallthrough
		case "sub", "mul", "div", "mod":
			if !isNum(a) || !isNum(b) {
				return "", moerr("MO005", "typecheck", "arithmetic requires numbers", &x.Pos)
			}
			if a == TDecimal || b == TDecimal || x.Op == "div" {
				return TDecimal, nil
			}
			return TInt, nil
		case "lt", "lte", "gt", "gte":
			if !isNum(a) || !isNum(b) {
				return "", moerr("MO005", "typecheck", "comparison requires numbers", &x.Pos)
			}
			return TBool, nil
		case "eq", "ne":
			return TBool, nil
		case "and", "or":
			if a != TBool && a != TAny {
				return "", moerr("MO005", "typecheck", "boolean operator requires Boolean", &x.Pos)
			}
			if b != TBool && b != TAny {
				return "", moerr("MO005", "typecheck", "boolean operator requires Boolean", &x.Pos)
			}
			return TBool, nil
		}
	case *CallExpr:
		if id, ok := x.Callee.(*Identifier); ok {
			switch id.Name {
			case "CLOCK":
				c.required["clock.read"] = true
			case "READFILE":
				c.required["filesystem.read"] = true
			case "WRITEFILE":
				c.required["filesystem.write"] = true
			}
		}
		if _, e := c.expr(x.Callee); e != nil {
			return "", e
		}
		for _, a := range x.Args {
			if _, e := c.expr(a); e != nil {
				return "", e
			}
		}
		return TAny, nil
	case *IndexExpr:
		t, e := c.expr(x.Target)
		if e != nil {
			return "", e
		}
		if t != TList && t != TText && t != TAny {
			return "", moerr("MO005", "typecheck", "index target must be List or Text", &x.Pos)
		}
		it, e := c.expr(x.Index)
		if e != nil {
			return "", e
		}
		if it != TInt && it != TAny {
			return "", moerr("MO005", "typecheck", "index must be Integer", &x.Pos)
		}
		return TAny, nil
	}
	return TAny, nil
}

// ---------------- Canonical source & hashing ----------------

func g(cp int) string          { return string(rune(cp)) }
func encIdent(s string) string { x, _ := encodeWord(s); return x }
func encNumber(v float64, integer bool) string {
	var s string
	if integer {
		s = strconv.FormatInt(int64(v), 10)
	} else {
		s = strconv.FormatFloat(v, 'f', -1, 64)
		if !strings.Contains(s, ".") {
			s += ".0"
		}
	}
	var b strings.Builder
	for _, r := range s {
		if r == '.' {
			b.WriteRune(0x1F726)
		} else if r >= '0' && r <= '9' {
			b.WriteRune(CoreStart + 26 + (r - '0'))
		}
	}
	return b.String()
}
func canonExpr(e Expr) string {
	switch x := e.(type) {
	case *Identifier:
		return encIdent(x.Name)
	case *NumberLiteral:
		return encNumber(x.Value, x.Integer)
	case *StringLiteral:
		v, _ := encodeWord(x.Value)
		return g(0x1F73C) + v + g(0x1F73C)
	case *BoolLiteral:
		if x.Value {
			return encIdent("TRUE")
		}
		return encIdent("FALSE")
	case *NullLiteral:
		return encIdent("NULL")
	case *ListLiteral:
		var a []string
		for _, z := range x.Items {
			a = append(a, canonExpr(z))
		}
		return g(0x1F727) + strings.Join(a, g(0x1F72E)) + g(0x1F728)
	case *UnaryExpr:
		op := g(0x1F732)
		if x.Op == "not" {
			op = g(0x1F73B)
		}
		return op + g(0x1F72A) + canonExpr(x.Right) + g(0x1F72B)
	case *BinaryExpr:
		ops := map[string]int{"add": 0x1F731, "sub": 0x1F732, "mul": 0x1F733, "div": 0x1F734, "mod": 0x1F735, "lt": 0x1F736, "gt": 0x1F737, "lte": 0x1F738, "gte": 0x1F725, "eq": 0x1F739, "ne": 0x1F73A, "and": 0x1F73E, "or": 0x1F73F}
		return g(0x1F72A) + canonExpr(x.Left) + g(ops[x.Op]) + canonExpr(x.Right) + g(0x1F72B)
	case *CallExpr:
		var a []string
		for _, z := range x.Args {
			a = append(a, canonExpr(z))
		}
		return canonExpr(x.Callee) + g(0x1F72A) + strings.Join(a, g(0x1F72E)) + g(0x1F72B)
	case *IndexExpr:
		return canonExpr(x.Target) + g(0x1F727) + canonExpr(x.Index) + g(0x1F728)
	}
	return ""
}
func canonBlock(b *BlockStmt, indent string) string {
	var out strings.Builder
	out.WriteString(g(0x1F72C))
	out.WriteByte('\n')
	for _, s := range b.Statements {
		out.WriteString(indent + "  " + canonStmt(s, indent+"  "))
		if !strings.HasSuffix(out.String(), "\n") {
			out.WriteByte('\n')
		}
	}
	out.WriteString(indent + g(0x1F72D))
	return out.String()
}
func canonStmt(s Stmt, indent string) string {
	end := g(0x1F72F)
	switch x := s.(type) {
	case *DefineStmt:
		return encIdent(x.Name) + g(0x1F729) + canonExpr(x.Value) + end
	case *AssignStmt:
		return encIdent(x.Name) + g(0x1F730) + canonExpr(x.Value) + end
	case *ExprStmt:
		return canonExpr(x.Expr) + end
	case *GateStmt:
		return canonExpr(x.Condition) + g(0x1F724) + canonExpr(x.Target) + end
	case *IfStmt:
		z := encIdent("IF") + " " + canonExpr(x.Condition) + " " + canonBlock(x.Then, indent)
		if x.Else != nil {
			z += " " + encIdent("ELSE") + " " + canonBlock(x.Else, indent)
		}
		return z
	case *WhileStmt:
		return encIdent("WHILE") + " " + canonExpr(x.Condition) + " " + canonBlock(x.Body, indent)
	case *ForStmt:
		return encIdent("FOR") + " " + encIdent(x.Name) + " " + encIdent("IN") + " " + canonExpr(x.Iterable) + " " + canonBlock(x.Body, indent)
	case *FunctionStmt:
		var ps []string
		for _, p := range x.Params {
			ps = append(ps, encIdent(p))
		}
		return encIdent("FUNCTION") + " " + encIdent(x.Name) + g(0x1F72A) + strings.Join(ps, g(0x1F72E)) + g(0x1F72B) + " " + canonBlock(x.Body, indent)
	case *ReturnStmt:
		if x.Value == nil {
			return encIdent("RETURN") + end
		}
		return encIdent("RETURN") + " " + canonExpr(x.Value) + end
	case *BreakStmt:
		return encIdent("BREAK") + end
	case *ContinueStmt:
		return encIdent("CONTINUE") + end
	case *BlockStmt:
		return canonBlock(x, indent)
	}
	return ""
}
func canonical(p *Program) string {
	var b strings.Builder
	for _, s := range p.Statements {
		b.WriteString(canonStmt(s, ""))
		b.WriteByte('\n')
	}
	return b.String()
}
func programHash(p *Program) string {
	data := []byte(LanguageABI + "\n" + Version + "\n" + abiHash() + "\n" + canonical(p))
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}

// ---------------- Bytecode compiler ----------------

type Instr struct {
	Op  string `json:"op"`
	Arg any    `json:"arg,omitempty"`
	Pos *Pos   `json:"pos,omitempty"`
}
type Chunk struct {
	Params []string `json:"params,omitempty"`
	Code   []Instr  `json:"code"`
}
type BytecodeFile struct {
	Format          string           `json:"format"`
	LanguageVersion string           `json:"language_version"`
	ABIHash         string           `json:"abi_hash"`
	ProgramHash     string           `json:"program_hash"`
	Capabilities    []string         `json:"capabilities"`
	Main            Chunk            `json:"main"`
	Functions       map[string]Chunk `json:"functions"`
	BytecodeHash    string           `json:"bytecode_hash"`
}
type Compiler struct {
	bc    *BytecodeFile
	loops []loopPatch
	seq   int
}
type loopPatch struct {
	start     int
	breaks    []int
	continues []int
}

func compileProgram(p *Program, caps []string) (*BytecodeFile, error) {
	bc := &BytecodeFile{Format: "mobc-0.1", LanguageVersion: Version, ABIHash: abiHash(), ProgramHash: programHash(p), Capabilities: caps, Functions: map[string]Chunk{}}
	c := &Compiler{bc: bc}
	main := Chunk{}
	// Top-level functions are installed before ordinary statements. This makes
	// forward calls deterministic and matches the static symbol pre-pass.
	for _, s := range p.Statements {
		if _, ok := s.(*FunctionStmt); ok {
			if err := c.stmt(&main, s); err != nil {
				return nil, err
			}
		}
	}
	for _, s := range p.Statements {
		if _, ok := s.(*FunctionStmt); ok {
			continue
		}
		if err := c.stmt(&main, s); err != nil {
			return nil, err
		}
	}
	main.Code = append(main.Code, Instr{Op: "HALT"})
	bc.Main = main
	bc.BytecodeHash = bytecodeDigest(bc)
	return bc, nil
}
func bytecodeDigest(b *BytecodeFile) string {
	cp := *b
	cp.BytecodeHash = ""
	data, _ := json.Marshal(cp)
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}
func emit(ch *Chunk, op string, arg any, p *Pos) int {
	if n, ok := arg.(int); ok {
		arg = float64(n)
	}
	ch.Code = append(ch.Code, Instr{Op: op, Arg: arg, Pos: p})
	return len(ch.Code) - 1
}
func patch(ch *Chunk, i int, target int) { ch.Code[i].Arg = float64(target) }

func (c *Compiler) stmt(ch *Chunk, s Stmt) error {
	switch x := s.(type) {
	case *DefineStmt:
		if err := c.expr(ch, x.Value); err != nil {
			return err
		}
		emit(ch, "DEF", x.Name, &x.Pos)
	case *AssignStmt:
		if err := c.expr(ch, x.Value); err != nil {
			return err
		}
		emit(ch, "STORE", x.Name, &x.Pos)
	case *ExprStmt:
		if err := c.expr(ch, x.Expr); err != nil {
			return err
		}
		emit(ch, "POP", nil, &x.Pos)
	case *GateStmt:
		if err := c.expr(ch, x.Condition); err != nil {
			return err
		}
		j := emit(ch, "JMP_FALSE", 0, &x.Pos)
		emit(ch, "CAP", "gate.execute", &x.Pos)
		if err := c.expr(ch, x.Target); err != nil {
			return err
		}
		emit(ch, "POP", nil, &x.Pos)
		patch(ch, j, len(ch.Code))
	case *BlockStmt:
		for _, z := range x.Statements {
			if err := c.stmt(ch, z); err != nil {
				return err
			}
		}
	case *IfStmt:
		if err := c.expr(ch, x.Condition); err != nil {
			return err
		}
		jf := emit(ch, "JMP_FALSE", 0, &x.Pos)
		if err := c.stmt(ch, x.Then); err != nil {
			return err
		}
		if x.Else != nil {
			je := emit(ch, "JMP", 0, &x.Pos)
			patch(ch, jf, len(ch.Code))
			if err := c.stmt(ch, x.Else); err != nil {
				return err
			}
			patch(ch, je, len(ch.Code))
		} else {
			patch(ch, jf, len(ch.Code))
		}
	case *WhileStmt:
		start := len(ch.Code)
		if err := c.expr(ch, x.Condition); err != nil {
			return err
		}
		jf := emit(ch, "JMP_FALSE", 0, &x.Pos)
		c.loops = append(c.loops, loopPatch{start: start})
		if err := c.stmt(ch, x.Body); err != nil {
			return err
		}
		lp := c.loops[len(c.loops)-1]
		c.loops = c.loops[:len(c.loops)-1]
		emit(ch, "JMP", start, &x.Pos)
		end := len(ch.Code)
		patch(ch, jf, end)
		for _, i := range lp.breaks {
			patch(ch, i, end)
		}
		for _, i := range lp.continues {
			patch(ch, i, start)
		}
	case *ForStmt:
		c.seq++
		iter := fmt.Sprintf("$ITER%d", c.seq)
		idx := fmt.Sprintf("$IDX%d", c.seq)
		if err := c.expr(ch, x.Iterable); err != nil {
			return err
		}
		emit(ch, "SET", iter, &x.Pos)
		emit(ch, "PUSH", float64(0), &x.Pos)
		emit(ch, "SET", idx, &x.Pos)
		start := len(ch.Code)
		emit(ch, "LOAD", idx, &x.Pos)
		emit(ch, "LOAD", iter, &x.Pos)
		emit(ch, "LEN", nil, &x.Pos)
		emit(ch, "LT", nil, &x.Pos)
		jf := emit(ch, "JMP_FALSE", 0, &x.Pos)
		emit(ch, "LOAD", iter, &x.Pos)
		emit(ch, "LOAD", idx, &x.Pos)
		emit(ch, "INDEX", nil, &x.Pos)
		emit(ch, "SET", x.Name, &x.Pos)
		c.loops = append(c.loops, loopPatch{start: start})
		if err := c.stmt(ch, x.Body); err != nil {
			return err
		}
		lp := c.loops[len(c.loops)-1]
		c.loops = c.loops[:len(c.loops)-1]
		cont := len(ch.Code)
		emit(ch, "LOAD", idx, &x.Pos)
		emit(ch, "PUSH", float64(1), &x.Pos)
		emit(ch, "ADD", nil, &x.Pos)
		emit(ch, "STORE", idx, &x.Pos)
		emit(ch, "JMP", start, &x.Pos)
		end := len(ch.Code)
		patch(ch, jf, end)
		for _, i := range lp.breaks {
			patch(ch, i, end)
		}
		for _, i := range lp.continues {
			patch(ch, i, cont)
		}
	case *FunctionStmt:
		fch := Chunk{Params: x.Params}
		saved := c.loops
		c.loops = nil
		if err := c.stmt(&fch, x.Body); err != nil {
			return err
		}
		c.loops = saved
		emit(&fch, "PUSH", nil, &x.Pos)
		emit(&fch, "RETURN", nil, &x.Pos)
		c.bc.Functions[x.Name] = fch
		emit(ch, "DEF_FUNC", x.Name, &x.Pos)
	case *ReturnStmt:
		if x.Value == nil {
			emit(ch, "PUSH", nil, &x.Pos)
		} else {
			if err := c.expr(ch, x.Value); err != nil {
				return err
			}
		}
		emit(ch, "RETURN", nil, &x.Pos)
	case *BreakStmt:
		if len(c.loops) == 0 {
			return moerr("MO002", "compile", "break outside loop", &x.Pos)
		}
		i := emit(ch, "JMP", 0, &x.Pos)
		c.loops[len(c.loops)-1].breaks = append(c.loops[len(c.loops)-1].breaks, i)
	case *ContinueStmt:
		if len(c.loops) == 0 {
			return moerr("MO002", "compile", "continue outside loop", &x.Pos)
		}
		i := emit(ch, "JMP", 0, &x.Pos)
		c.loops[len(c.loops)-1].continues = append(c.loops[len(c.loops)-1].continues, i)
	}
	return nil
}
func (c *Compiler) expr(ch *Chunk, e Expr) error {
	switch x := e.(type) {
	case *Identifier:
		emit(ch, "LOAD", x.Name, &x.Pos)
	case *NumberLiteral:
		emit(ch, "PUSH", x.Value, &x.Pos)
	case *StringLiteral:
		emit(ch, "PUSH", x.Value, &x.Pos)
	case *BoolLiteral:
		emit(ch, "PUSH", x.Value, &x.Pos)
	case *NullLiteral:
		emit(ch, "PUSH", nil, &x.Pos)
	case *ListLiteral:
		for _, z := range x.Items {
			if err := c.expr(ch, z); err != nil {
				return err
			}
		}
		emit(ch, "LIST", len(x.Items), &x.Pos)
	case *UnaryExpr:
		if err := c.expr(ch, x.Right); err != nil {
			return err
		}
		if x.Op == "neg" {
			emit(ch, "NEG", nil, &x.Pos)
		} else {
			emit(ch, "NOT", nil, &x.Pos)
		}
	case *BinaryExpr:
		if err := c.expr(ch, x.Left); err != nil {
			return err
		}
		if err := c.expr(ch, x.Right); err != nil {
			return err
		}
		ops := map[string]string{"add": "ADD", "sub": "SUB", "mul": "MUL", "div": "DIV", "mod": "MOD", "lt": "LT", "lte": "LTE", "gt": "GT", "gte": "GTE", "eq": "EQ", "ne": "NE", "and": "AND", "or": "OR"}
		emit(ch, ops[x.Op], nil, &x.Pos)
	case *CallExpr:
		if err := c.expr(ch, x.Callee); err != nil {
			return err
		}
		for _, a := range x.Args {
			if err := c.expr(ch, a); err != nil {
				return err
			}
		}
		emit(ch, "CALL", len(x.Args), &x.Pos)
	case *IndexExpr:
		if err := c.expr(ch, x.Target); err != nil {
			return err
		}
		if err := c.expr(ch, x.Index); err != nil {
			return err
		}
		emit(ch, "INDEX", nil, &x.Pos)
	}
	return nil
}

// ---------------- VM ----------------

type FuncRef struct{ Name string }
type BuiltinRef struct{ Name string }
type Frame struct {
	ch     *Chunk
	ip     int
	locals map[string]any
	stack  []any
	name   string
}
type VM struct {
	bc                        *BytecodeFile
	globals                   map[string]any
	frames                    []*Frame
	allowed                   map[string]bool
	declared                  map[string]bool
	steps, maxSteps, maxDepth int
	workspace                 string
	out                       io.Writer
	outputBytes               int
}

func newVM(bc *BytecodeFile, allow []string, maxSteps, maxDepth int, workspace string, out io.Writer) (*VM, error) {
	if bc.LanguageVersion != Version {
		return nil, moerr("MO019", "vm", "unsupported language version", nil)
	}
	if bc.ABIHash != abiHash() {
		return nil, moerr("MO018", "vm", "ABI hash mismatch", nil)
	}
	if bc.BytecodeHash != bytecodeDigest(bc) {
		return nil, moerr("MO018", "vm", "bytecode hash mismatch", nil)
	}
	m := map[string]bool{}
	for _, x := range allow {
		if x != "" {
			m[x] = true
		}
	}
	d := map[string]bool{}
	for _, x := range bc.Capabilities {
		d[x] = true
	}
	abs, err := filepath.Abs(workspace)
	if err != nil {
		return nil, err
	}
	return &VM{bc: bc, globals: map[string]any{}, allowed: m, declared: d, maxSteps: maxSteps, maxDepth: maxDepth, workspace: abs, out: out}, nil
}
func (v *VM) cap(name string) error {
	if !v.declared[name] {
		return moerr("MO008", "runtime", "capability not declared by program: "+name, nil)
	}
	if !v.allowed[name] {
		return moerr("MO008", "runtime", "capability denied: "+name, nil)
	}
	return nil
}
func (v *VM) run() (any, error) {
	main := v.bc.Main
	f := &Frame{ch: &main, locals: v.globals, name: "<main>"}
	v.frames = []*Frame{f}
	return v.loop()
}
func (v *VM) push(f *Frame, x any) { f.stack = append(f.stack, x) }
func (v *VM) pop(f *Frame) (any, error) {
	if len(f.stack) == 0 {
		return nil, errors.New("VM stack underflow")
	}
	x := f.stack[len(f.stack)-1]
	f.stack = f.stack[:len(f.stack)-1]
	return x, nil
}
func (v *VM) loop() (any, error) {
	var last any
	for len(v.frames) > 0 {
		if v.steps >= v.maxSteps {
			return nil, moerr("MO010", "runtime", "execution step limit exceeded", nil)
		}
		v.steps++
		f := v.frames[len(v.frames)-1]
		if f.ip >= len(f.ch.Code) {
			v.frames = v.frames[:len(v.frames)-1]
			continue
		}
		in := f.ch.Code[f.ip]
		f.ip++
		err := v.exec(f, in, &last)
		if err != nil {
			if me, ok := err.(*MoError); ok && me.Pos == nil && in.Pos != nil {
				me.Pos = in.Pos
			}
			return nil, err
		}
	}
	return last, nil
}
func num(x any) (float64, bool) { f, ok := x.(float64); return f, ok }
func truth(x any) (bool, bool)  { b, ok := x.(bool); return b, ok }
func (v *VM) lookup(f *Frame, n string) (any, bool) {
	if x, ok := f.locals[n]; ok {
		return x, true
	}
	if x, ok := v.globals[n]; ok {
		return x, true
	}
	switch n {
	case "PRINT", "LEN", "ABS", "MIN", "MAX", "CLOCK", "READFILE", "WRITEFILE":
		return BuiltinRef{Name: n}, true
	}
	if _, ok := v.bc.Functions[n]; ok {
		return FuncRef{Name: n}, true
	}
	return nil, false
}
func (v *VM) exec(f *Frame, in Instr, last *any) error {
	binNum := func(fn func(float64, float64) (any, error)) error {
		b, e := v.pop(f)
		if e != nil {
			return e
		}
		a, e := v.pop(f)
		if e != nil {
			return e
		}
		af, aok := num(a)
		bf, bok := num(b)
		if !aok || !bok {
			return moerr("MO005", "runtime", "numeric operands required", in.Pos)
		}
		r, e := fn(af, bf)
		if e != nil {
			return e
		}
		v.push(f, r)
		return nil
	}
	switch in.Op {
	case "HALT":
		v.frames = v.frames[:len(v.frames)-1]
		return nil
	case "PUSH":
		v.push(f, in.Arg)
	case "POP":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		*last = x
	case "LOAD":
		n := in.Arg.(string)
		x, ok := v.lookup(f, n)
		if !ok {
			return moerr("MO003", "runtime", "unknown identifier "+n, in.Pos)
		}
		v.push(f, x)
	case "DEF":
		n := in.Arg.(string)
		if _, ok := f.locals[n]; ok {
			return moerr("MO004", "runtime", "duplicate definition "+n, in.Pos)
		}
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		f.locals[n] = x
	case "SET":
		n := in.Arg.(string)
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		f.locals[n] = x
	case "STORE":
		n := in.Arg.(string)
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		if _, ok := f.locals[n]; ok {
			f.locals[n] = x
		} else if _, ok := v.globals[n]; ok {
			v.globals[n] = x
		} else {
			return moerr("MO003", "runtime", "unknown identifier "+n, in.Pos)
		}
	case "DEF_FUNC":
		v.globals[in.Arg.(string)] = FuncRef{Name: in.Arg.(string)}
	case "NEG":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		a, ok := num(x)
		if !ok {
			return moerr("MO005", "runtime", "NEG requires number", in.Pos)
		}
		v.push(f, -a)
	case "NOT":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		a, ok := truth(x)
		if !ok {
			return moerr("MO005", "runtime", "NOT requires Boolean", in.Pos)
		}
		v.push(f, !a)
	case "ADD":
		b, e := v.pop(f)
		if e != nil {
			return e
		}
		a, e := v.pop(f)
		if e != nil {
			return e
		}
		if af, ok := num(a); ok {
			if bf, ok := num(b); ok {
				v.push(f, af+bf)
				return nil
			}
		}
		if as, ok := a.(string); ok {
			if bs, ok := b.(string); ok {
				v.push(f, as+bs)
				return nil
			}
		}
		return moerr("MO005", "runtime", "ADD requires two numbers or two texts", in.Pos)
	case "SUB":
		return binNum(func(a, b float64) (any, error) { return a - b, nil })
	case "MUL":
		return binNum(func(a, b float64) (any, error) { return a * b, nil })
	case "DIV":
		return binNum(func(a, b float64) (any, error) {
			if b == 0 {
				return nil, moerr("MO006", "runtime", "division by zero", in.Pos)
			}
			return a / b, nil
		})
	case "MOD":
		return binNum(func(a, b float64) (any, error) {
			if b == 0 {
				return nil, moerr("MO006", "runtime", "division by zero", in.Pos)
			}
			return math.Mod(a, b), nil
		})
	case "LT":
		return binNum(func(a, b float64) (any, error) { return a < b, nil })
	case "LTE":
		return binNum(func(a, b float64) (any, error) { return a <= b, nil })
	case "GT":
		return binNum(func(a, b float64) (any, error) { return a > b, nil })
	case "GTE":
		return binNum(func(a, b float64) (any, error) { return a >= b, nil })
	case "EQ":
		b, e := v.pop(f)
		if e != nil {
			return e
		}
		a, e := v.pop(f)
		if e != nil {
			return e
		}
		v.push(f, reflect.DeepEqual(a, b))
	case "NE":
		b, e := v.pop(f)
		if e != nil {
			return e
		}
		a, e := v.pop(f)
		if e != nil {
			return e
		}
		v.push(f, !reflect.DeepEqual(a, b))
	case "AND", "OR":
		b, e := v.pop(f)
		if e != nil {
			return e
		}
		a, e := v.pop(f)
		if e != nil {
			return e
		}
		aa, aok := truth(a)
		bb, bok := truth(b)
		if !aok || !bok {
			return moerr("MO005", "runtime", "boolean operands required", in.Pos)
		}
		if in.Op == "AND" {
			v.push(f, aa && bb)
		} else {
			v.push(f, aa || bb)
		}
	case "LIST":
		n := int(in.Arg.(float64))
		if n > MaxCollection {
			return moerr("MO012", "runtime", "collection limit exceeded", in.Pos)
		}
		if len(f.stack) < n {
			return errors.New("VM stack underflow")
		}
		xs := append([]any(nil), f.stack[len(f.stack)-n:]...)
		f.stack = f.stack[:len(f.stack)-n]
		v.push(f, xs)
	case "LEN":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		switch z := x.(type) {
		case []any:
			v.push(f, float64(len(z)))
		case string:
			v.push(f, float64(len([]rune(z))))
		default:
			return moerr("MO005", "runtime", "LEN requires List or Text", in.Pos)
		}
	case "INDEX":
		idx, e := v.pop(f)
		if e != nil {
			return e
		}
		target, e := v.pop(f)
		if e != nil {
			return e
		}
		iv, ok := num(idx)
		if !ok || iv != math.Trunc(iv) {
			return moerr("MO005", "runtime", "index must be integer", in.Pos)
		}
		i := int(iv)
		switch z := target.(type) {
		case []any:
			if i < 0 || i >= len(z) {
				return moerr("MO009", "runtime", "index out of range", in.Pos)
			}
			v.push(f, z[i])
		case string:
			r := []rune(z)
			if i < 0 || i >= len(r) {
				return moerr("MO009", "runtime", "index out of range", in.Pos)
			}
			v.push(f, string(r[i]))
		default:
			return moerr("MO005", "runtime", "index target must be List or Text", in.Pos)
		}
	case "JMP":
		f.ip = int(in.Arg.(float64))
	case "JMP_FALSE":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		b, ok := truth(x)
		if !ok {
			return moerr("MO005", "runtime", "condition must be Boolean", in.Pos)
		}
		if !b {
			f.ip = int(in.Arg.(float64))
		}
	case "CAP":
		if e := v.cap(in.Arg.(string)); e != nil {
			return e
		}
	case "CALL":
		n := int(in.Arg.(float64))
		if len(f.stack) < n+1 {
			return errors.New("VM stack underflow")
		}
		args := append([]any(nil), f.stack[len(f.stack)-n:]...)
		f.stack = f.stack[:len(f.stack)-n]
		callee, e := v.pop(f)
		if e != nil {
			return e
		}
		switch fn := callee.(type) {
		case BuiltinRef:
			r, e := v.builtin(fn.Name, args, in.Pos)
			if e != nil {
				return e
			}
			v.push(f, r)
		case FuncRef:
			ch, ok := v.bc.Functions[fn.Name]
			if !ok {
				return moerr("MO003", "runtime", "unknown function "+fn.Name, in.Pos)
			}
			if len(args) != len(ch.Params) {
				return moerr("MO009", "runtime", "wrong argument count for "+fn.Name, in.Pos)
			}
			if len(v.frames) >= v.maxDepth {
				return moerr("MO011", "runtime", "call depth exceeded", in.Pos)
			}
			loc := map[string]any{}
			for i, p := range ch.Params {
				loc[p] = args[i]
			}
			cc := ch
			v.frames = append(v.frames, &Frame{ch: &cc, locals: loc, name: fn.Name})
		default:
			return moerr("MO005", "runtime", "value is not callable", in.Pos)
		}
	case "RETURN":
		x, e := v.pop(f)
		if e != nil {
			return e
		}
		v.frames = v.frames[:len(v.frames)-1]
		if len(v.frames) > 0 {
			v.push(v.frames[len(v.frames)-1], x)
		} else {
			*last = x
		}
	default:
		return moerr("MO013", "runtime", "invalid opcode "+in.Op, in.Pos)
	}
	return nil
}
func (v *VM) safePath(p string) (string, error) {
	if filepath.IsAbs(p) {
		return "", moerr("MO008", "conduit", "absolute paths are denied", nil)
	}
	full, err := filepath.Abs(filepath.Join(v.workspace, p))
	if err != nil {
		return "", err
	}
	rel, err := filepath.Rel(v.workspace, full)
	if err != nil {
		return "", err
	}
	if rel == ".." || strings.HasPrefix(rel, ".."+string(os.PathSeparator)) {
		return "", moerr("MO008", "conduit", "path escapes workspace", nil)
	}
	return full, nil
}
func (v *VM) builtin(name string, args []any, p *Pos) (any, error) {
	switch name {
	case "PRINT":
		var parts []string
		for _, a := range args {
			parts = append(parts, fmt.Sprint(a))
		}
		s := strings.Join(parts, " ") + "\n"
		v.outputBytes += len(s)
		if v.outputBytes > MaxOutputBytes {
			return nil, moerr("MO010", "runtime", "output limit exceeded", p)
		}
		_, e := io.WriteString(v.out, s)
		return nil, e
	case "LEN":
		if len(args) != 1 {
			return nil, moerr("MO009", "runtime", "LEN expects 1 argument", p)
		}
		switch z := args[0].(type) {
		case []any:
			return float64(len(z)), nil
		case string:
			return float64(len([]rune(z))), nil
		}
		return nil, moerr("MO005", "runtime", "LEN requires List or Text", p)
	case "ABS":
		if len(args) != 1 {
			return nil, moerr("MO009", "runtime", "ABS expects 1 argument", p)
		}
		x, ok := num(args[0])
		if !ok {
			return nil, moerr("MO005", "runtime", "ABS requires number", p)
		}
		return math.Abs(x), nil
	case "MIN", "MAX":
		if len(args) < 1 {
			return nil, moerr("MO009", "runtime", name+" expects arguments", p)
		}
		best, ok := num(args[0])
		if !ok {
			return nil, moerr("MO005", "runtime", name+" requires numbers", p)
		}
		for _, a := range args[1:] {
			x, ok := num(a)
			if !ok {
				return nil, moerr("MO005", "runtime", name+" requires numbers", p)
			}
			if name == "MIN" && x < best || name == "MAX" && x > best {
				best = x
			}
		}
		return best, nil
	case "CLOCK":
		if len(args) != 0 {
			return nil, moerr("MO009", "runtime", "CLOCK expects 0 arguments", p)
		}
		if e := v.cap("clock.read"); e != nil {
			return nil, e
		}
		return float64(time.Now().Unix()), nil
	case "READFILE":
		if len(args) != 1 {
			return nil, moerr("MO009", "runtime", "READFILE expects 1 argument", p)
		}
		if e := v.cap("filesystem.read"); e != nil {
			return nil, e
		}
		s, ok := args[0].(string)
		if !ok {
			return nil, moerr("MO005", "runtime", "READFILE path must be Text", p)
		}
		full, e := v.safePath(s)
		if e != nil {
			return nil, e
		}
		b, e := os.ReadFile(full)
		if e != nil {
			return nil, moerr("MO009", "conduit", e.Error(), p)
		}
		if len(b) > MaxOutputBytes {
			return nil, moerr("MO010", "conduit", "file exceeds read limit", p)
		}
		return string(b), nil
	case "WRITEFILE":
		if len(args) != 2 {
			return nil, moerr("MO009", "runtime", "WRITEFILE expects 2 arguments", p)
		}
		if e := v.cap("filesystem.write"); e != nil {
			return nil, e
		}
		path, ok := args[0].(string)
		if !ok {
			return nil, moerr("MO005", "runtime", "WRITEFILE path must be Text", p)
		}
		data, ok := args[1].(string)
		if !ok {
			return nil, moerr("MO005", "runtime", "WRITEFILE data must be Text", p)
		}
		if len(data) > MaxOutputBytes {
			return nil, moerr("MO010", "conduit", "write exceeds limit", p)
		}
		full, e := v.safePath(path)
		if e != nil {
			return nil, e
		}
		if e = os.WriteFile(full, []byte(data), 0600); e != nil {
			return nil, moerr("MO009", "conduit", e.Error(), p)
		}
		return nil, nil
	}
	return nil, moerr("MO003", "runtime", "unknown builtin "+name, p)
}

// ---------------- Scroll sealing ----------------

type Scroll struct {
	Format          string   `json:"format"`
	LanguageVersion string   `json:"language_version"`
	ABIHash         string   `json:"abi_hash"`
	ProgramHash     string   `json:"program_hash"`
	BytecodeHash    string   `json:"bytecode_hash"`
	Capabilities    []string `json:"capabilities"`
	CreatedAt       string   `json:"created_at"`
	PublicKey       string   `json:"public_key"`
	Bytecode        string   `json:"bytecode"`
	Signature       string   `json:"signature"`
}

func scrollPayload(s *Scroll, raw []byte) []byte {
	return bytes.Join([][]byte{
		[]byte(s.Format), []byte(s.LanguageVersion), []byte(s.ABIHash), []byte(s.ProgramHash), []byte(s.BytecodeHash),
		[]byte(strings.Join(s.Capabilities, ",")), []byte(s.CreatedAt), []byte(s.PublicKey), raw,
	}, []byte{0})
}
func sealBC(bc *BytecodeFile, priv ed25519.PrivateKey) (*Scroll, error) {
	raw, e := json.Marshal(bc)
	if e != nil {
		return nil, e
	}
	pub := priv.Public().(ed25519.PublicKey)
	s := &Scroll{Format: "moscroll-0.1", LanguageVersion: Version, ABIHash: abiHash(), ProgramHash: bc.ProgramHash, BytecodeHash: bc.BytecodeHash, Capabilities: bc.Capabilities, CreatedAt: time.Now().UTC().Format(time.RFC3339Nano), PublicKey: base64.StdEncoding.EncodeToString(pub), Bytecode: base64.StdEncoding.EncodeToString(raw)}
	s.Signature = base64.StdEncoding.EncodeToString(ed25519.Sign(priv, scrollPayload(s, raw)))
	return s, nil
}
func verifyScroll(s *Scroll, trusted ed25519.PublicKey) (*BytecodeFile, error) {
	if s.Format != "moscroll-0.1" || s.LanguageVersion != Version {
		return nil, moerr("MO019", "verify", "unsupported scroll or language version", nil)
	}
	if s.ABIHash != abiHash() {
		return nil, moerr("MO018", "verify", "ABI hash mismatch", nil)
	}
	pubRaw, e := base64.StdEncoding.DecodeString(s.PublicKey)
	if e != nil || len(pubRaw) != ed25519.PublicKeySize {
		return nil, moerr("MO014", "verify", "invalid public key", nil)
	}
	pub := ed25519.PublicKey(pubRaw)
	if trusted != nil && !bytes.Equal(pub, trusted) {
		return nil, moerr("MO017", "verify", "signer is not trusted key", nil)
	}
	raw, e := base64.StdEncoding.DecodeString(s.Bytecode)
	if e != nil {
		return nil, moerr("MO013", "verify", "invalid bytecode encoding", nil)
	}
	sig, e := base64.StdEncoding.DecodeString(s.Signature)
	if e != nil || !ed25519.Verify(pub, scrollPayload(s, raw), sig) {
		return nil, moerr("MO014", "verify", "signature validation failed", nil)
	}
	var bc BytecodeFile
	if e = json.Unmarshal(raw, &bc); e != nil {
		return nil, moerr("MO013", "verify", "invalid bytecode", nil)
	}
	if bc.BytecodeHash != bytecodeDigest(&bc) || bc.BytecodeHash != s.BytecodeHash {
		return nil, moerr("MO018", "verify", "bytecode hash mismatch", nil)
	}
	if bc.ProgramHash != s.ProgramHash {
		return nil, moerr("MO018", "verify", "program hash mismatch", nil)
	}
	if !reflect.DeepEqual(bc.Capabilities, s.Capabilities) {
		return nil, moerr("MO018", "verify", "capability manifest mismatch", nil)
	}
	return &bc, nil
}

// ---------------- IO helpers ----------------

func loadSource(path string) ([]byte, error) { return os.ReadFile(path) }
func sourcePipeline(path string) ([]Token, *Program, []string, *BytecodeFile, error) {
	b, e := loadSource(path)
	if e != nil {
		return nil, nil, nil, nil, e
	}
	t, e := lex(b)
	if e != nil {
		return nil, nil, nil, nil, e
	}
	p, e := parse(t)
	if e != nil {
		return nil, nil, nil, nil, e
	}
	caps, e := checkProgram(p)
	if e != nil {
		return nil, nil, nil, nil, e
	}
	bc, e := compileProgram(p, caps)
	return t, p, caps, bc, e
}
func loadBC(path string) (*BytecodeFile, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	var bc BytecodeFile
	if e = json.Unmarshal(b, &bc); e != nil {
		return nil, moerr("MO013", "load", "invalid bytecode JSON", nil)
	}
	if bc.BytecodeHash != bytecodeDigest(&bc) {
		return nil, moerr("MO018", "load", "bytecode hash mismatch", nil)
	}
	return &bc, nil
}
func loadPrivate(path string) (ed25519.PrivateKey, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	raw, e := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b)))
	if e != nil || len(raw) != ed25519.PrivateKeySize {
		return nil, errors.New("invalid Ed25519 private key")
	}
	return ed25519.PrivateKey(raw), nil
}
func loadPublic(path string) (ed25519.PublicKey, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	raw, e := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b)))
	if e != nil || len(raw) != ed25519.PublicKeySize {
		return nil, errors.New("invalid Ed25519 public key")
	}
	return ed25519.PublicKey(raw), nil
}
func writeJSON(path string, x any) error {
	b, e := json.MarshalIndent(x, "", "  ")
	if e != nil {
		return e
	}
	b = append(b, '\n')
	return os.WriteFile(path, b, 0644)
}
func printJSON(x any) { b, _ := json.MarshalIndent(x, "", "  "); fmt.Println(string(b)) }
func die(err error)   { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
func splitCaps(s string) []string {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	a := strings.Split(s, ",")
	for i := range a {
		a[i] = strings.TrimSpace(a[i])
	}
	return a
}

// ---------------- CLI ----------------

func usage() {
	fmt.Fprintf(os.Stderr, `MoScript %s (build %s) — executable glyph language runtime
Product of %s · %s

Usage:
  moscript version
  moscript abi
  moscript check <program.ms>
  moscript tokens <program.ms>
  moscript ast <program.ms>
  moscript canonical <program.ms>
  moscript hash <program.ms>
  moscript compile [-o program.mobc] <program.ms>
  moscript run [--allow cap1,cap2] [--max-steps N] [--workspace DIR] <program.ms|program.mobc>
  moscript keygen [--private private.key] [--public public.key]
  moscript seal --key private.key [-o program.moscroll] <program.ms>
  moscript verify [--pub trusted_public.key] <program.moscroll>
  moscript run-scroll --pub trusted_public.key [--allow cap1,cap2] [--max-steps N] [--workspace DIR] <program.moscroll>

Capabilities are deny-by-default. Implemented external capabilities:
  gate.execute, clock.read, filesystem.read, filesystem.write
`, Version, BuildVersion, Producer, Registration)
}

func logoPath(name string) string {
	if _, err := os.Stat(name); err == nil {
		return name
	}
	if ex, err := os.Executable(); err == nil {
		p := filepath.Join(filepath.Dir(ex), name)
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return ""
}

func printLogo(name string, width int) {
	if width < 1 {
		width = 40
	}
	path := logoPath(name)
	if path == "" {
		return
	}
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()

	img, err := png.Decode(f)
	if err != nil {
		return
	}
	bounds := img.Bounds()
	w, h := bounds.Dx(), bounds.Dy()
	if w == 0 || h == 0 {
		return
	}

	// Flatten onto white so transparent pixels become light.
	flat := image.NewRGBA(bounds)
	draw.Draw(flat, bounds, image.NewUniform(color.White), image.Point{}, draw.Src)
	draw.Draw(flat, bounds, img, bounds.Min, draw.Over)

	ratio := float64(h) / float64(w)
	height := int(float64(width) * ratio * 0.5)
	if height < 1 {
		height = 1
	}

	ramp := []byte(" .:-=+*#%@")
	for y := 0; y < height; y++ {
		sy0 := y * h / height
		sy1 := (y + 1) * h / height
		for x := 0; x < width; x++ {
			sx0 := x * w / width
			sx1 := (x + 1) * w / width
			var sum float64
			n := 0
			for sy := sy0; sy < sy1; sy++ {
				for sx := sx0; sx < sx1; sx++ {
					r, g, b, _ := flat.At(bounds.Min.X+sx, bounds.Min.Y+sy).RGBA()
					// Rec. 601 luma, values are in 0..65535
					luma := 0.299*float64(r) + 0.587*float64(g) + 0.114*float64(b)
					sum += luma
					n++
				}
			}
			avg := sum / float64(n) / 65535.0
			idx := int(avg * float64(len(ramp)-1))
			if idx < 0 {
				idx = 0
			}
			if idx >= len(ramp) {
				idx = len(ramp) - 1
			}
			fmt.Fprint(os.Stderr, string(ramp[len(ramp)-1-idx]))
		}
		fmt.Fprintln(os.Stderr)
	}
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cmd := os.Args[1]
	switch cmd {
	case "version":
		printJSON(map[string]any{
			"name":             ProductName,
			"language_version": Version,
			"build_version":    BuildVersion,
			"producer":         Producer,
			"registration":     Registration,
			"abi":              LanguageABI,
			"abi_hash":         abiHash(),
			"core":             "U+1F700-U+1F73F",
		})
	case "abi":
		printJSON(map[string]any{"name": LanguageABI, "abi_hash": abiHash(), "entries": abiEntries()})
	case "check", "tokens", "ast", "canonical", "hash":
		if len(os.Args) != 3 {
			usage()
			os.Exit(2)
		}
		t, p, caps, _, e := sourcePipeline(os.Args[2])
		if e != nil {
			die(e)
		}
		switch cmd {
		case "check":
			printJSON(map[string]any{"status": "ok", "program_hash": programHash(p), "abi_hash": abiHash(), "required_capabilities": caps})
		case "tokens":
			printJSON(t)
		case "ast":
			printJSON(p)
		case "canonical":
			fmt.Print(canonical(p))
		case "hash":
			fmt.Println(programHash(p))
		}
	case "compile":
		fs := flag.NewFlagSet("compile", flag.ExitOnError)
		out := fs.String("o", "", "output .mobc")
		fs.Parse(os.Args[2:])
		if fs.NArg() != 1 {
			usage()
			os.Exit(2)
		}
		_, _, _, bc, e := sourcePipeline(fs.Arg(0))
		if e != nil {
			die(e)
		}
		if *out == "" {
			*out = strings.TrimSuffix(fs.Arg(0), filepath.Ext(fs.Arg(0))) + ".mobc"
		}
		if e = writeJSON(*out, bc); e != nil {
			die(e)
		}
		fmt.Println(*out)
	case "run":
		fs := flag.NewFlagSet("run", flag.ExitOnError)
		allow := fs.String("allow", "", "comma-separated capabilities")
		steps := fs.Int("max-steps", DefaultSteps, "step budget")
		depth := fs.Int("max-depth", DefaultDepth, "call depth")
		ws := fs.String("workspace", ".", "filesystem capability root")
		fs.Parse(os.Args[2:])
		if fs.NArg() != 1 {
			usage()
			os.Exit(2)
		}
		path := fs.Arg(0)
		var bc *BytecodeFile
		var e error
		if strings.HasSuffix(path, ".mobc") {
			bc, e = loadBC(path)
		} else {
			_, _, _, bc, e = sourcePipeline(path)
		}
		if e != nil {
			die(e)
		}
		printLogo("ms2.png", 40)
		vm, e := newVM(bc, splitCaps(*allow), *steps, *depth, *ws, os.Stdout)
		if e != nil {
			die(e)
		}
		res, e := vm.run()
		if e != nil {
			die(e)
		}
		if res != nil {
			printJSON(map[string]any{"result": res, "steps": vm.steps})
		}
	case "keygen":
		fs := flag.NewFlagSet("keygen", flag.ExitOnError)
		privPath := fs.String("private", "moscript_private.key", "private key")
		pubPath := fs.String("public", "moscript_public.key", "public key")
		fs.Parse(os.Args[2:])
		if fs.NArg() != 0 {
			usage()
			os.Exit(2)
		}
		pub, priv, e := ed25519.GenerateKey(rand.Reader)
		if e != nil {
			die(e)
		}
		if e = os.WriteFile(*privPath, []byte(base64.StdEncoding.EncodeToString(priv)+"\n"), 0600); e != nil {
			die(e)
		}
		if e = os.WriteFile(*pubPath, []byte(base64.StdEncoding.EncodeToString(pub)+"\n"), 0644); e != nil {
			die(e)
		}
		printJSON(map[string]any{"private": *privPath, "public": *pubPath})
	case "seal":
		fs := flag.NewFlagSet("seal", flag.ExitOnError)
		key := fs.String("key", "", "Ed25519 private key")
		out := fs.String("o", "", "output .moscroll")
		fs.Parse(os.Args[2:])
		if *key == "" || fs.NArg() != 1 {
			usage()
			os.Exit(2)
		}
		printLogo("ms.png", 32)
		_, _, _, bc, e := sourcePipeline(fs.Arg(0))
		if e != nil {
			die(e)
		}
		priv, e := loadPrivate(*key)
		if e != nil {
			die(e)
		}
		scroll, e := sealBC(bc, priv)
		if e != nil {
			die(e)
		}
		if *out == "" {
			*out = strings.TrimSuffix(fs.Arg(0), filepath.Ext(fs.Arg(0))) + ".moscroll"
		}
		if e = writeJSON(*out, scroll); e != nil {
			die(e)
		}
		fmt.Println(*out)
	case "verify":
		fs := flag.NewFlagSet("verify", flag.ExitOnError)
		pubPath := fs.String("pub", "", "optional trusted public key")
		fs.Parse(os.Args[2:])
		if fs.NArg() != 1 {
			usage()
			os.Exit(2)
		}
		b, e := os.ReadFile(fs.Arg(0))
		if e != nil {
			die(e)
		}
		var s Scroll
		if e = json.Unmarshal(b, &s); e != nil {
			die(e)
		}
		var pub ed25519.PublicKey
		if *pubPath != "" {
			pub, e = loadPublic(*pubPath)
			if e != nil {
				die(e)
			}
		}
		bc, e := verifyScroll(&s, pub)
		if e != nil {
			die(e)
		}
		printLogo("ms.png", 32)
		printJSON(map[string]any{"status": "verified", "program_hash": bc.ProgramHash, "bytecode_hash": bc.BytecodeHash, "capabilities": bc.Capabilities})
	case "run-scroll":
		fs := flag.NewFlagSet("run-scroll", flag.ExitOnError)
		pubPath := fs.String("pub", "", "trusted public key (required)")
		allow := fs.String("allow", "", "comma-separated capabilities")
		steps := fs.Int("max-steps", DefaultSteps, "step budget")
		depth := fs.Int("max-depth", DefaultDepth, "call depth")
		ws := fs.String("workspace", ".", "filesystem capability root")
		fs.Parse(os.Args[2:])
		if *pubPath == "" || fs.NArg() != 1 {
			usage()
			os.Exit(2)
		}
		pub, e := loadPublic(*pubPath)
		if e != nil {
			die(e)
		}
		b, e := os.ReadFile(fs.Arg(0))
		if e != nil {
			die(e)
		}
		var s Scroll
		if e = json.Unmarshal(b, &s); e != nil {
			die(e)
		}
		bc, e := verifyScroll(&s, pub)
		if e != nil {
			die(e)
		}
		printLogo("ms2.png", 40)
		vm, e := newVM(bc, splitCaps(*allow), *steps, *depth, *ws, os.Stdout)
		if e != nil {
			die(e)
		}
		res, e := vm.run()
		if e != nil {
			die(e)
		}
		if res != nil {
			printJSON(map[string]any{"result": res, "steps": vm.steps})
		}
	default:
		usage()
		os.Exit(2)
	}
}
