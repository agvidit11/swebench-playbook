#!/usr/bin/env python3
"""instruction-lint.py <task-dir> <upstream-clone> — is the contract/grader pair legal under D1?

D1 (playbook decision, 2026-09-22) — the naming rule is a SOURCING FILTER, not a gag:

  * The observable symptom is always stated.
  * A new name the GRADED TESTS PIN **must** be named in the instruction.
  * A name the graded tests do NOT touch is never stated.
  * Algorithm, file paths and call order are never stated.

The illegal configuration is *silent contract + pinning test*. That is what produced
BAD_GRADING_WRONG on 4 of 4 tasks in the peer pipeline: the spec withheld the accessor
name and the hidden tests asserted on it.

So this lint is THREE-WAY, and checks both directions:

  absent at base + pinned by graded tests + named in contract  -> OK, D1 requires it
  absent at base + NOT pinned by tests     + named in contract  -> FAIL, gratuitous leak
  absent at base + pinned by graded tests + NOT in contract     -> FAIL, the illegal config

Read-only. Exit 1 on a blocking finding.

History: before 2026-09-22 this script enforced an absolute never-name rule and would
FAIL on a symbol D1 now requires. If you are reading an older run log, that is why.
"""
import json, glob, os, re, subprocess, sys

IDENT = r"[A-Za-z_][A-Za-z0-9_]{3,}"


def configs(task):
    return sorted(glob.glob(os.path.join(task, "steps", "*", "tests", "config.json"))) + \
           [os.path.join(task, "tests", "config.json")]


def base_commit(task):
    for c in configs(task):
        if os.path.exists(c):
            bc = json.load(open(c)).get("base_commit", "")
            if re.fullmatch(r"[0-9a-f]{40}", str(bc)):
                return bc
    return None


def repo_symbols(clone, bc):
    """Every identifier present in the repo at base_commit."""
    try:
        out = subprocess.run(["git", "-C", clone, "grep", "-hoE", IDENT, bc],
                             capture_output=True, text=True, timeout=180)
        return set(out.stdout.split())
    except Exception:
        return set()


# `\\.` cannot match a backslash-NEWLINE continuation, because `.` excludes \n.
# Rust wraps long literals that way:
#     "Sec-WebSocket-Protocol: {}\r\n\
#      Other: {}\r\n"
# so the literal never closed, the strip failed, and `Protocol` was reported as a
# coined API symbol on dropshot. `[\s\S]` lets the escape consume the newline.
# (The negated classes already match \n, so only the escape branch needed fixing.)
STRLIT = re.compile(r'"(?:[^"\\]|\\[\s\S])*"' + r"|'(?:[^'\\]|\\[\s\S])*'" + r"|`[^`]*`")
RUBY_PERCENT = re.compile(
    r'%[wWiIqQxrs]?\[[^\]]*\]'
    r'|%[wWiIqQxrs]?\([^)]*\)'
    r'|%[wWiIqQxrs]?\{[^}]*\}'
)
COMMENT = re.compile(r'//.*$|#.*$', re.M)
PKGSEL = re.compile(r'\b[a-z][A-Za-z0-9_]*\.([A-Z][A-Za-z0-9_]*)')
RUBY_EXTERNAL_NAMESPACE = re.compile(
    r'\b(?:RSpec|Minitest|JSONAPI)(?:::[A-Z][A-Za-z0-9_]*)+'
)


def code_only(text):
    """Strip string literals and comments before tokenising.

    Measured 2026-09-23: the header literal "X-Ordered-Trailer" tokenised to
    Ordered and Trailer and was reported as a coined API symbol the contract
    failed to name. Every finding on that task was a false positive of this kind.
    """
    return COMMENT.sub(" ", RUBY_PERCENT.sub(" ", STRLIT.sub(" ", text)))


OWN_GO_MODULES = set()   # filled from <clone>/go.mod in main()
MENTIONED = set()        # every identifier on any added test-patch line (direction-1 proxy)


def graded_symbols(task, only=None):
    """Identifiers appearing on ADDED lines of every step's test_patch.

    These are the symbols the graded suite can actually pin. Returns None if no
    test_patch is readable yet, which means the pairing cannot be judged.
    """
    syms, locally_defined, saw_patch = set(), set(), False
    test_defined = set()
    pinned_extra = set()   # reflection / interface-assertion pins; survive selector + local stripping
    for c in (only or configs(task)):
        if not os.path.exists(c):
            continue
        try:
            cfg = json.load(open(c))
        except Exception:
            continue
        # ONLY the test patch. The oracle `patch` is the SOLUTION -- its private
        # helpers are not pinned by anything and must never be read as contract.
        # Including it reported `isRepresentableTrailerValue` (an oracle-internal
        # func with ZERO call sites in the graded test) as an unnamed pinned symbol.
        for key in ("test_patch",):
            body = cfg.get(key) or ""
            if body.strip():
                saw_patch = True
            if not body:
                continue
            added = "\n".join(l[1:] for l in body.splitlines()
                              if l.startswith("+") and not l.startswith("+++"))
            code = code_only(added)
            # Collect unambiguously test-local Go declarations up front. Keep
            # this independent from the language-specific filtering below so
            # broad pinning fallbacks cannot reclassify a helper function or a
            # short-declared channel variable as production API.
            test_defined |= set(re.findall(
                r'(?m)^\s*func\s+(?:\([^)]*\)\s*)?(\w+)', added
            ))
            for lhs in re.findall(
                r'(?:^\s*|\b(?:for|if|switch)\s+)([\w,\s]+?)\s*:=',
                added,
                re.M,
            ):
                test_defined |= {t.strip() for t in lhs.split(",") if t.strip()}
            # A method or field pinned BY REFLECTION -- reflect MethodByName("X") / FieldByName("X") --
            # is graded even though its name lives in a string literal code_only() strips. Tests do
            # this so the package compiles at a step's starting tree where X does not exist yet.
            # Missing it reported CheckBackwardCompatibility as ungraded on go-zero-goctl 2026-10-02.
            pinned_extra |= set(re.findall(r'(?:MethodByName|FieldByName)\(\s*"(\w+)"', added))
            # Same purpose, other idiom: the test declares an anonymous interface naming the method,
            # type-asserts the value to it, and calls through that variable -- the call then looks like
            # a package selector and is dropped. Methods declared in a test interface ARE pinned.
            for blk in re.findall(r'interface\s*\{([^{}]*)\}', added):
                pinned_extra |= set(re.findall(r'\b([A-Z]\w*)\s*\(', blk))
            syms |= set(re.findall(IDENT, code))
            # Members reached through a package selector (maps.EqualFunc,
            # slices.Equal) belong to stdlib or a dependency, not to this repo,
            # so they are absent from the base grep and read as coined.
            syms -= set(PKGSEL.findall(code))
            # ...EXCEPT a selector through an import of THIS repo's own module. An external
            # test package calls the API as `tablepkg.DivergentPaths(...)`; dropping it reported
            # a correctly-named, graded DivergentPaths as "named but ungraded" on gobgp 2026-10-02.
            # Searched in `added`, not `code`: a test that compiles a generated program keeps the
            # import and the call inside a raw string (gobgp step 1, table.DivergentRoute).
            for alias, path in re.findall(r'(?m)^\s*(?:import\s+)?(\w+)?\s*"([^"]+)"\s*$', added):
                if not any(path == m or path.startswith(m + "/") for m in OWN_GO_MODULES):
                    continue
                segs = [p for p in path.split("/") if not re.fullmatch(r"v\d+", p)]
                alias = alias or segs[-1]
                pinned_extra |= set(re.findall(r'\b' + re.escape(alias) + r'\.([A-Z]\w*)', added))
            # reflect's own methods, reached through a call result (reflect.ValueOf(x).MethodByName)
            # rather than a package name, so PKGSEL never sees them.
            syms -= {"MethodByName", "FieldByName", "Interface", "IsNil", "IsValid", "Call", "Elem"}
            # Methods chained off a stdlib constructor -- new(big.Int).SetBytes(..), big.NewInt(1).Lsh(..) --
            # belong to that stdlib type. Reported SetBytes as coined API on gobgp 2026-10-02.
            for chain in re.findall(r'(?:new\(\s*(?:big|strings|bytes|sync|time)\.\w+\s*\)|\b(?:big|strings|bytes|time|netip|reflect)\.\w+\([^()]*\))((?:\.\w+\([^()]*\))+)', code):
                syms -= set(re.findall(r'\.(\w+)\(', chain))
            # Go func PARAMETER names, variadic included: `specs ...prefixSpec` reported `specs`.
            for params in re.findall(r'\bfunc\s*(?:\([^)]*\)\s*)?\w*\s*\(([^)]*)\)', code):
                found = set(re.findall(r'(\w+)\s+(?:\.\.\.)?[\*\[\]\w.]+\s*(?:,|$)', params))
                syms -= found
                locally_defined |= found
            # Constants below known external test/dependency namespaces are
            # framework APIs, never API the solver must add.  For example,
            # RSpec::Expectations::ExpectationNotMetError and
            # JSONAPI::IncludeDirective::InvalidKey were reported as coined
            # production symbols by the Graphiti task.
            for chain in RUBY_EXTERNAL_NAMESPACE.findall(code):
                syms -= set(re.findall(IDENT, chain))
            # Identifiers the test patch DEFINES are test-local by construction;
            # the contract has no business naming them.
            for pat in (r'\bfunc\s+(?:\([^)]*\)\s*)?(\w+)', r'\btype\s+(\w+)',
                        # Go package clause. An external test package is named
                        # `<pkg>_test`, which is a file-layout fact, not a symbol
                        # any contract could state. Reported `lifecycle_guard_test`
                        # and `lifecycle_regression_test` as coined API on circl.
                        r'^package\s+(\w+)',
                        r'\b(?:var|const)\s+(\w+)',
                        # Ruby test-local declarations. Without these, helper
                        # classes and fixtures are misreported as production
                        # APIs that the instruction must name.
                        r'^\s*class\s+(\w+)',
                        r'^\s*module\s+(\w+)',
                        # struct FIELD declaration: "sendFirst    bool"
                        r'^\s*([a-zA-Z_]\w*)\s+[\w\[\]\*\.<>,\s]+$',
                        # composite-literal KEY: "{sendFirst: true}" -- a reference
                        # to a field the same patch declares
                        r'[{,]\s*(\w+)\s*:',
                        r'^\s*(\w+)\s+=\s',
                        # Ruby resource/fixture DSL declarations create names
                        # local to the test patch. Calls later made through
                        # those relationships do not make their names part of
                        # the solver-facing API contract.
                        r'\b(?:has_many|has_one|belongs_to|sideload)\s+:([A-Za-z_]\w*)',
                        # Ruby keyword arguments used to construct test-local
                        # context objects (OpenStruct.new(flag: true), etc.).
                        r'[({,]\s*([a-z_][A-Za-z0-9_]*)\s*:',
                        # --- Rust declaration forms. The list above is Go-only,
                        # so a trait/struct the TEST FILE declares read as a symbol
                        # the solver must implement. On dropshot that reported 8
                        # false positives (Dispatch, Outcome, ViaStr, ViaString,
                        # WebsocketUpgradeTestExt, ApiEndpointSubprotocolsTestExt),
                        # all defined inside the test patch itself.
                        r'\b(?:trait|struct|enum|union|mod)\s+(\w+)',
                        # `fn NAME` may only be stripped at COLUMN 0. A top-level
                        # fn in a test file is a local helper; an INDENTED one is a
                        # trait or impl member, and in the parent-revision-fallback
                        # idiom those method names ARE the contract surface the
                        # solver must implement. Stripping `fn` wholesale made the
                        # lint report the inverse error, "contract names NEW symbols
                        # no graded test pins", on dropshot's three real names.
                        r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)',
                        r'\blet\s+(?:mut\s+)?(\w+)',
                        r'\bimpl(?:<[^>]*>)?\s+(?:\w+(?:<[^>]*>)?\s+for\s+)?(\w+)'):
                found = set(re.findall(pat, code, re.M))
                syms -= found
                locally_defined |= found
            # Ruby block parameters and special globals are local/language
            # names, not solver-implemented symbols. This removes block-local
            # `_buffer`/`_auth_server` and `$VERBOSE` false positives.
            for params in re.findall(r'\|([^|]+)\|', code):
                found = set(re.findall(IDENT, params))
                syms -= found
                locally_defined |= found
            # Ruby method names and parameters declared by the test patch.
            for method, params in re.findall(
                r'^\s*def\s+(?:self\.)?([A-Za-z_]\w*[!?=]?)\s*(?:\(([^)]*)\))?',
                code,
                re.M,
            ):
                found = {method.rstrip('!?=')} | set(re.findall(IDENT, params))
                syms -= found
                locally_defined |= found
            found = set(re.findall(r'\$([A-Za-z_]\w*)', code))
            syms -= found
            locally_defined |= found
            # Identifiers pulled in by a `use` statement belong to std or a
            # dependency, not to this repo, so they are absent from the base grep
            # and read as coined. This is how tokio's AsyncReadExt was reported.
            for imp in re.findall(r'\buse\s+[^;]+;', code):
                syms -= set(re.findall(IDENT, imp))
        # A graded test's OWN NAME is not a symbol the contract must state. The
        # declared ids enumerate them exactly, so subtract their components rather
        # than guessing from syntax -- `fn NAME` cannot be stripped wholesale,
        # because in the parent-revision-fallback idiom a trait's method names ARE
        # the contract surface. Reported 8 Rust test fns on dropshot.
        for tid in (cfg.get("fail_to_pass") or []) + (cfg.get("pass_to_pass") or []):
            syms -= set(re.findall(IDENT, str(tid)))
            # short assignment, including multi-value: "message, receiveErr := ..."
            # The `^\s*` anchor misses Go's commonest forms, where the assignment
            # is the init clause of a statement: `for recipient := range newIDs`,
            # `if got := f(); got != want`, `switch v := x.(type)`. Those reported
            # `recipient` as a coined contract symbol on circl. Allow the keyword.
            for lhs in re.findall(r'(?:^\s*|\b(?:for|if|switch)\s+)([\w,\s]+?)\s*:=',
                                  code, re.M):
                syms -= {t.strip() for t in lhs.split(",") if t.strip()}
    # Test-local declarations win even when the same identifier was collected
    # by one of the broad pinning fallbacks.  Unioning pinned_extra after the
    # subtraction reintroduced helpers and local channel variables (for
    # example awaitCoalescingProbeResult, fetchReturned, and releaseOld) as
    # purported production APIs, yielding a blocking silent-contract false
    # positive.  Real interface/reflection pins are unaffected unless the test
    # patch also defines that exact identifier locally.
    return ((syms | pinned_extra) - locally_defined - test_defined) if saw_patch else None


def contract_symbols(text):
    c = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_:.#]{3,})`", text))
    # A call-shaped span -- `Normalize(*ApiSpec)`, `(*NormalizedSpec).MarshalText` -- names its identifiers too.
    # The pattern above rejects any span containing parentheses; that reported a stated Normalize as unstated.
    for span in re.findall(r"`([^`]*\([^`]*)`", text):
        c |= {m for m in re.findall(r"([A-Za-z_]\w{3,})\s*\(", span)}
        c |= {m for m in re.findall(r"\)\.([A-Za-z_]\w{3,})", span)}
    # A Go signature the contract states in a fenced block -- `func (s *PrefixSet) Reduced() []Prefix`
    # -- names Reduced even though it is neither backticked nor camelCase. Missed on gobgp 2026-10-02.
    # Prose signatures, not fenced or backticked: "func (next *NormalizedSpec) BreakingRequestWitness(",
    # "Normalize(*ApiSpec)", "(*NormalizedSpec).MarshalText". Reported a stated Normalize as unstated, go-zero 2026-10-03.
    c |= set(re.findall(r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w{3,})\s*\(", text))
    c |= set(re.findall(r"\b([A-Z]\w{3,})\(\*\w+\)", text))
    c |= set(re.findall(r"\(\*\w+\)\.([A-Z]\w{3,})", text))
    for blk in re.findall(r"```[\w]*\n(.*?)```", text, re.S):
        c |= set(re.findall(r"\bfunc\s*(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", blk))
    c |= set(re.findall(r"\b([A-Z][a-z]+[A-Z][A-Za-z0-9]{2,})\b", text))
    c |= set(re.findall(r"\b([a-z]+_[a-z_]{3,})\b", text))
    return c


def leaf(sym):
    return re.split(r"[:.#]", sym)[-1]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    task, clone = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/")

    bc = base_commit(task)
    if not bc:
        print("  SKIP  instruction-lint: no resolvable base_commit")
        return 0
    present = repo_symbols(clone, bc)
    if not present:
        print("  SKIP  instruction-lint: could not read repo at base")
        return 0

    gomod = os.path.join(clone, "go.mod")
    if os.path.exists(gomod):
        m = re.search(r"(?m)^module\s+(\S+)", open(gomod).read())
        if m:
            OWN_GO_MODULES.add(m.group(1))
    graded = graded_symbols(task)
    for _c in configs(task):
        try:
            _b = json.load(open(_c)).get("test_patch") or ""
        except Exception:
            continue
        MENTIONED.update(re.findall(r"[A-Za-z_]\w*", "\n".join(l for l in _b.splitlines() if l.startswith("+"))))
    if graded is None:
        print("  WARN  instruction-lint: no test_patch yet — running NAME-LEAK half only.")
        print("        Re-run after B3 to check the silent-contract/pinning-test direction.")

    bad = False
    instrs = sorted(glob.glob(os.path.join(task, "steps", "*", "instruction.md"))) or \
             [os.path.join(task, "instruction.md")]

    cum_named = set()   # names stated by THIS or an EARLIER step's contract (multi-turn is cumulative)
    for i in instrs:
        if not os.path.exists(i):
            continue
        text = open(i).read()
        step = os.path.basename(os.path.dirname(i))
        # NOT code_only() here: the contract is markdown, where backticks mark the
        # symbol names we are looking for. Stripping them as raw strings erased
        # every name the contract states and failed a correctly-named task.
        named = {c for c in contract_symbols(text) if len(leaf(c)) >= 4}

        # Byte-pattern / magic-number notation is DATA, not a coined symbol. A contract
        # describing what WAV bytes look like -- `RIFF....WAVE` -- names nothing the solver
        # must implement and cannot narrow the fork, which is the whole reason D1 exists.
        # Reported as a FAIL on gzhttp-declared-length-sniff-window, 2026-09-30, where it was
        # the only blocker on an otherwise clean task. Shapes excluded: runs of dots used as
        # byte wildcards, and all-caps tokens that are purely a magic string.
        named = {c for c in named
                 if '....' not in c and not re.fullmatch(r'[A-Z0-9]{3,}\.{2,}[A-Z0-9]{3,}', c)}

        cum_named |= {leaf(c) for c in named} | named
        new_named = {c for c in named if leaf(c) not in present and c not in present}

        # A name the contract qualifies with a Go STANDARD-LIBRARY package (encoding.TextMarshaler,
        # io.Reader, context.Context) is not a symbol the solver coins, and neither is its bare
        # leaf. Reported as a D1 FAIL on go-zero-goctl 2026-10-02, whose test pins the interface
        # with a compile-time assertion the lint cannot see as a pin.
        _STD = ("encoding", "io", "fmt", "errors", "context", "net", "time", "strings", "bytes",
                "sort", "sync", "json", "http", "os", "reflect", "strconv", "unicode", "math")
        _std_leaves = {c.split(".")[-1] for c in named if "." in c and c.split(".")[0] in _STD}
        new_named = {c for c in new_named
                     if not ("." in c and c.split(".")[0] in _STD) and leaf(c) not in _std_leaves}

        # --- direction 1: the contract names something new that nothing grades ---
        if graded is not None:
            # A name that appears ANYWHERE on the test patch's added lines is graded for this direction's
            # purpose: receiver-variable calls (next.BreakingRequestWitness) and compile-time assertions
            # (var _ encoding.TextMarshaler) are dropped as package selectors by graded_symbols().
            gratuitous = sorted(c for c in new_named
                                if leaf(c) not in graded and c not in graded
                                and leaf(c) not in MENTIONED)
            required = sorted(c for c in new_named if c not in gratuitous)
            if gratuitous:
                print(f"  \033[31mFAIL\033[0m  ({step}) contract names NEW symbols no graded test pins: "
                      f"{gratuitous[:6]}")
                print("        D1: a name the grader ignores is never stated. Remove it, or")
                print("        grade it. Naming it for free only narrows the fork.")
                bad = True
            if required:
                ov = os.path.join(task, "audit", "gate0-override.md")
                if os.path.exists(ov):
                    print(f"  \033[32mOK\033[0m    ({step}) contract names {len(required)} new symbol(s) the "
                          f"graded tests pin — D1 requires this, and A3 GATE 0 was "
                          f"overridden on record: {required[:6]}")
                else:
                    print(f"  \033[33mWARN\033[0m  ({step}) contract names {len(required)} COINED symbol(s) the "
                          f"graded tests pin: {required[:6]}")
                    print( "        This pairing is LEGAL — naming a pinned symbol is what D1 requires,")
                    print( "        and the alternative (silent contract + pinning test) is the thing that")
                    print( "        produced BAD_GRADING_WRONG on 4 of 4 peer tasks.")
                    print(f"        But A3 GATE 0 rejects candidates that need a coined name at all")
                    print( "        (corpus rate: 1 passed / 13 failed), and no override is on record at")
                    print(f"        {ov}. Either write that override with its justification, or this")
                    print( "        candidate should not have left A3. Legality is not a licence to coin.")
        else:
            if new_named:
                print(f"  \033[33mWARN\033[0m  ({step}) contract names symbols absent at base: "
                      f"{sorted(new_named)[:6]}")
                print("        Legal ONLY if the graded tests pin each one. Verify after B3.")

        # --- direction 2: THE ILLEGAL CONFIG — tests pin a new name, contract is silent ---
        if graded is not None:
            named_leaves = {leaf(c) for c in named} | named
            # PER-STEP: judge each step against ITS OWN graded set, allowing names an earlier step's
            # contract already stated. Using the union blamed step 1 for not stating step 3's API
            # (go-zero-goctl, 2026-10-02).
            step_cfg = os.path.join(os.path.dirname(i), "tests", "config.json")
            sg = graded_symbols(task, [step_cfg]) if os.path.exists(step_cfg) else graded
            sg = graded if sg is None else sg
            known = named_leaves | cum_named
            silent = sorted(g for g in sg
                            if g not in present and g not in known
                            and len(g) >= 5
                            and not g.startswith(("_", "test_", "assert", "Test")))
            if silent:
                print(f"  \033[31mFAIL\033[0m  ({step}) graded tests pin NEW symbols the contract never "
                      f"states: {silent[:8]}")
                print("        This is the illegal configuration: silent contract + pinning test.")
                print("        It produced BAD_GRADING_WRONG on 4 of 4 tasks in the peer pipeline.")
                print("        Fix by naming them in the contract (Avocado only), or by making the")
                print("        assertion name-agnostic (Codex, B3).")
                bad = True

    if not bad:
        print("  \033[32mPASS\033[0m  contract/grader naming is legal under D1")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
