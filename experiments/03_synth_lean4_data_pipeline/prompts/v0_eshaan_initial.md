---
parent: null
date: 2026-04-21
author: Eshaan B. (Stanford AI for Lean Club)
agentic_cli: claude-code
model_tested: (unspecified — recommended on `claude-sonnet-4-6` and `gpt-5.5-xhigh`)
problem: "Initial spec — there was no canonical autoformalization prompt for translating C/Py to Lean 4 with theorems + proofs + compiler-checked tests."
rationale: "Comprehensive scaffolding covers input source (the-stack), per-function record schema, filtration rules (skip OS/state/varargs/fnptrs), call-graph topo-sort + axiomatize, validation pipeline, and theorem-quality discipline. Captures Eshaan's working notes from the lean-ebm group."
diff_summary: "Initial version — verbatim copy of ~/lean-ebm/experiments/claude_prompt.md (commit at lean-ebm/main as of 2026-05-10)."
source_url: "https://github.com/Stanford-AI-for-LEAN-Club/lean-ebm/blob/main/experiments/claude_prompt.md"
local_source: "~/lean-ebm/experiments/claude_prompt.md"
---

> **Provenance.** This file is a verbatim snapshot of Eshaan's prompt as of 2026-05-10. The body below has not been edited. Future revisions live in sibling files `vN_<short_name>.md` with their own frontmatter linking back to this v0 via `parent: v0_eshaan_initial`. See [`README.md`](./README.md) for the discipline.

---

# Synthetic C-to-Lean4 Dataset Generation

We are creating a dataset containing C and Python functions, their translations into Lean4, test cases that verify their faithful representation in Lean, theorems about the Lean algorithm that prove its correctness, and proofs of those theorems.

## Input

C code and Python code. Scrape from the internet. For example, use https://huggingface.co/datasets/bigcode/the-stack for a huge list of C and Python files and functions.

## Output

For each function in C and Python, generate:

1. **Lean translation** of the C and Python code
2. **Test cases** of the same function in C and Python and the same test cases in Lean
3. **Theorem statements** in Lean that prove major properties of the behavior of the C and Python code
4. **Theorem proofs** in Lean about those above statements

The schema will be, for each function, output a JSON record with these exact keys:
- "language": "Python" or "C" (string)
- "source": original source function (string)
- "lean_translation": Lean4 translation (string)
- "tests": C or Python test harness as a complete compilable .c/.py file (string) 
- "lean_tests": Lean4 #eval / #check test cases (string)
- "theorems": list of { "name": string, "statement": string, "proof": string }
- "deps_fully_translated": list of callee names that were axiomatized
- "axiomatized_deps": list of { "name": string, "lean_axiom": string }. 
- "skip_reason": null | string (if skipped, why)

After you are done, write the huggingface repo: https://huggingface.co/datasets/StanfordAILean/c-py-dataset. Use your HF_TOKEN!

## Filtration of C Files

Figure out what to prove and what not to prove:
- Don't prove functions that rely on "states" or OS-level functions (e.g., network calls, system calls)
- Not possible to read files or call network calls in Lean
- You can prove stuff about pointers and memory by defining an explicit map
- Etc. (not an exhaustive list; think from the perspective of proving something in Lean)

Specifically, SKIP a function if it:
- calls malloc/free/realloc without a bounded, analyzable pattern
- uses FILE*, sockets, pipes, or any fd-based I/O
- contains inline assembly or compiler intrinsics
- relies on global mutable state that isn't passed as an argument
- uses function pointers in a way that requires dynamic dispatch
- is variadic (va_list, ...)
- Think of other conditions!

## Preprocessing of C/Py files

For each C/Py function, if it calls subfunctions, axiomatize those and assume that those subfunctions are correct. 

1. Parse all C/Py files and build a call graph
2. Topologically sort functions (leaves first)
3. Process leaves first — they have no dependencies, translate fully
4. For each non-leaf function:
   a. Check if all callees have been fully translated → use the Lean translation
   b. If a callee was skipped (OS call, etc.) → generate an axiom for it
   c. If a callee is outside the dataset → generate an axiom for it
5. Tag each record with:
   - "deps_fully_translated": bool
   - "axiomatized_deps": list of callee names that were axiomatized

## Tips for conversion from C --> Lean
PROVE with a memory model if it:
- takes a pointer + length pair (model as Array or Fin-indexed function)
- does in-place mutation on a struct (model as a pure function returning a new struct)

Memory model convention:
- C arrays of length n → Lean `Array α` or `Fin n → α`
- Structs → Lean `structure` with identical field names
- Pointer mutation → pure functions returning (new_state, return_value)
- NULL pointer → `Option α`
- Integer overflow → use `UInt32`/`UInt64` (wrapping semantics) not `Nat`

Integer, the conversion process must be:
- int, long, short → use UInt32/UInt64/UInt16 (wrapping semantics) for bit-exact behavior
- unsigned variants → same UInt types (already unsigned in Lean)
- signed overflow is UB in C → document assumption that inputs avoid it, OR
  model as Int32/Int64 and add a precondition `h : x ∈ Set.Icc Int32.min Int32.max`
- size_t → USize (platform-width, wrapping)
- char used as integer → UInt8
- Bitwise ops (&, |, ^, ~, <<, >>) → use Lean's corresponding UInt ops, NOT Nat/Int
- Right shift of signed integers is UB in C → axiomatize or restrict to unsigned

**Floats** the conversion process must be:
- float  → Float32  (if available in your Lean version) or axiomatize as opaque
- double → Float    (Lean's built-in IEEE 754 double)
- Do NOT model floats as ℝ or ℚ — this breaks test case consistency
- NaN, ±Inf → Lean Float handles these; explicitly test Float.isNaN, Float.isInf
- Floating-point equality in theorems → avoid (=); use |a - b| ≤ ε with an explicit ε
- Functions that are only correct up to rounding → state theorems as:
    |lean_result - exact_result| ≤ n * Float.epsilon
- fma, sqrt, ceil, floor, round → use Lean's Float.sqrt etc. or axiomatize
- Do NOT attempt to prove termination/correctness of iterative float algorithms
  (e.g., Newton-Raphson) without a convergence bound as a precondition

**Characters and Strings**: the conversion process must be:
- char        → UInt8 (treat as byte, not Unicode)
- char*       → Array UInt8 (for byte buffers) or String (for null-terminated text)
- char* with explicit length n → Array UInt8 with a side condition h : arr.size = n
- Null-terminated strings → model as Array UInt8 with a terminator proof:
    ∃ i, i < arr.size ∧ arr[i] = 0 ∧ ∀ j < i, arr[j] ≠ 0
- String mutation (strcpy, strcat) → pure function returning new Array UInt8
- wchar_t / wide strings → SKIP (too platform-dependent)

**Booleans**: The conversion process must be:
- bool / _Bool → Bool
- C enums with contiguous values → Lean inductive with a toNat / ofNat roundtrip lemma
- C enums used as bitmasks → UInt32, not inductive
- -1 used as sentinel / error code → Option (return None for error cases)

**Structs and Unions**: the conversion process must be:
- Structs → Lean `structure` with identical field names and translated field types
- Nested structs → nested Lean structures (inline, not by pointer)
- Pointer-to-struct (pass by reference) → function takes and returns the struct value
- Unions → SKIP by default; or model the active variant as an `inductive` with one
  constructor per member, adding a note that this loses aliasing semantics
- Bitfields → model as UInt with explicit mask/shift accessors + roundtrip lemmas
- Packed structs / __attribute__((packed)) → SKIP (layout is implementation-defined)

**Pointers**: 
- T*  (non-null, single element) → just T (pass by value, return new value)
- T*  (nullable)                 → Option T
- T** (out-parameter)            → function returns (T, rest_of_state) as a product
- void* (generic pointer)        → SKIP or axiomatize the specific cast being used
- Function pointers              → SKIP (requires higher-order axiomatization; flag for manual review)
- Pointer arithmetic / arrays    → Array T with explicit index bounds proofs
- restrict keyword               → safe to ignore (it's an optimizer hint, not semantic)

**Arrays and Buffers**:
- Fixed-size array T[N]          → Fin N → T  (enables index-exhaustion proofs)
- Variable-length array T[n]     → Array T with side condition h : arr.size = n
- Multi-dimensional T[M][N]      → Fin M → Fin N → T
- Out-of-bounds access is UB     → add precondition h : i < n to every theorem
- Stack buffer vs heap buffer    → treat identically (irrelevant to functional behavior)

**Numerical Edge Cases to always test**:
Generate test cases covering:
- 0, 1, -1 for every integer argument
- INT_MAX (2147483647), INT_MIN (-2147483648), UINT_MAX (4294967295)
- Powers of 2 and powers of 2 minus 1 (boundary of bitwise ops)
- NaN, +Inf, -Inf, -0.0, Float.epsilon, largest finite float for every float argument
- Empty array (size = 0), single-element array, two-element array
- Arrays where all elements are equal
- Null / None for every optional pointer argument

## Validation

Ensure that the generated proofs:

1. **Translation correctness**: Ensure that the translations are correct by calling the Lean compiler
2. **Test case consistency**: Ensure that the translation matches test cases for the C/Py function and the Lean translation of the C/Py function. If there are discrepancies between the test cases in Lean and C, rewrite the Lean function to resolve them.
3. **Proof correctness**: Ensure that the proofs are correct by calling the Lean compiler
4. **Theorem coverage**: Ensure that the generated theorems about the Lean function cover all of the major properties that the algorithm would need to have to be considered correct.

Validation pipeline (run in order, abort step on failure):
1. lean --check <lean_translation>          → fix syntax errors (max 3 retries)
2. gcc -o test && ./test                    → fix C test harness (run python for python test cases)
3. lean --check <lean_tests>               → fix Lean test cases
4. If C/Py and Lean tests disagree on any input → rewrite Lean translation, restart from 1.
5. lean --check <theorems + proofs>        → fix proofs (max 5 retries with error feedback)
6. If proof still fails → downgrade to `sorry`, flag record as "proof_incomplete"

## Theorem Generation

Theorems must be **substantive** and **universally quantified**. Collectively they should constitute a correctness specification: a reviewer should be able to reconstruct the function's behavior from the theorem statements alone, and an incorrect implementation should fail at least one.

**Reject a theorem if** its proof is `native_decide` or `rfl` on concrete literals, or if it's trivially true for any implementation.

**Each function's theorems should cover as many of the following as apply:**
- Algebraic laws: commutativity, idempotency, monotonicity, roundtrip laws
- Agreement with Lean stdlib where an equivalent exists
- Output invariants: range, length, sortedness, etc.
- Full case characterization across all input regions

**Examples:**
```lean
-- BAD: point evaluation disguised as a theorem
theorem abs_val_neg_one : abs_val (-1) = (1 : Int32) := by native_decide

-- GOOD: universally quantified properties that characterize the function
theorem abs_val_nonneg (x : Int) : abs_val x ≥ 0 := by
  simp [abs_val]; split_ifs <;> omega
theorem abs_val_agrees_with_stdlib (x : Int) : abs_val x = x.natAbs.cast := by
  simp [abs_val, Int.natAbs]; split_ifs <;> omega

-- BAD: unproven stub
theorem gcd_comm (a b : Nat) : gcd a b = gcd b a := by sorry

-- GOOD: proven agreement with verified stdlib
theorem gcd_agrees_with_stdlib (a b : Nat) : gcd a b = Nat.gcd a b := by
  induction a, b using Nat.gcd.induction with
  | H1 n => simp [gcd, Nat.gcd]
  | H2 m n hm ih => simp [gcd, Nat.gcd, Nat.mod_def, ih]
```

**When a proof is out of reach:** state the theorem correctly, prove what you can, and mark the rest `sorry` with `"proof_incomplete": true`. Never downgrade a correct statement to something trivial just to avoid `sorry`.


