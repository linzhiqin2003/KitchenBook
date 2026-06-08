# Chapter 20 — Software testing

## Overview

This is the final lecture of the unit, given by Jo Hallett. It tackles the question students kept asking all year: *"how do I know if I got it right?"* The honest answer is that proving code is correct is genuinely hard — even an obvious `mean()` function over an `int` array silently breaks on rounding (`int` division), float precision (`IEEE 754`), and overflow (`INT_MAX`). And once you've fixed those, you still get to choose between summing-then-dividing and dividing-as-you-go, which trade speed against numerical stability.

The lecture's stance: *we cannot guarantee absolute truth, so engineer for known limitations.* The whole chapter is a tour of techniques in roughly increasing order of rigour and cost:

1. `assert` (cheap, debug-only sanity checks)
2. **Unit testing** — Python with `pytest`
3. **Behavioural / Acceptance testing** — Cucumber, with `.feature` files in plain English
4. **Property testing** — QuickCheck (Haskell) / `pytest-quickcheck`
5. **Fuzz testing** — AFL++
6. **Formal methods** — Lean 4, seL4 (the "nuclear option")

The takeaway from the slides: most engineers stop at unit + behavioural + property tests. Formal proof is a "PhD's worth of effort for a medium problem" — reserved for aircraft, AWS networking, kernels (seL4), and crypto. The framework actually taught for hands-on use is **`pytest`**.

## Core knowledge

### Why test; cost of bugs

Even "correct-looking" code is wrong in ways that depend on language, type system, hardware, and input. The slides walk through five iterations of `mean()` where each version compiles and runs but is subtly broken (integer division, format-specifier mismatch, float rounding, overflow). Without tests you'd never notice.

Quality Assurance is a whole branch of software engineering. It exists because passing tests *now* and not regressing *later* is the minimum bar for production code.

### The test pyramid (industry context, not in slides)

The slides do not draw the classical pyramid (many unit tests at the bottom, a few end-to-end tests at the top), but they implicitly follow it: unit tests are the workhorse, behavioural / acceptance tests sit above them, and fuzz / formal methods are rare and expensive.

### Test categories

| Category | What it checks | In the slides |
|---|---|---|
| **Unit** | A single function/class against known inputs | Yes — pytest section |
| **Integration** | Several units wired together | Implicit (cribbage lab tests modules together) |
| **System / End-to-end** | The whole program from outside | Not covered explicitly |
| **Regression** | Old bugs don't come back ("Passing tests now fail") | Yes — listed as production minimum |
| **Acceptance / Behavioural (BDD)** | Spec written by client, checked by code | Yes — Cucumber section |
| **Property** | Universal claims hold for *any* input | Yes — QuickCheck section |
| **Fuzz** | Random / corrupt input doesn't crash | Yes — AFL++ |
| **Performance** | Speed/memory bounds | Mentioned only via formal proof of bounds |

### Black-box vs white-box

Not stated as a heading, but both styles appear:
- *Black-box*: feature-file scenarios ("a base of 4, power 7, answer 16384") — only inputs/outputs.
- *White-box*: fuzzers "instrument the code… try and find inputs that trigger every path through every conditional." Property tests sit between the two.

### TDD red/green/refactor

Not named in the slides. The implicit cycle is "write test → run → fix code → rerun" — see the `power2.py` failure that triggers an investigation.

### The Python framework actually taught

**`pytest`**, run as `python -m pytest`. The slides explicitly contrast it with writing your own ad-hoc `if`-statement test mode. Plugins shown in the captured output: `pytest-asyncio`, `pytest-mock`. The lab additionally recommends `pytest-quickcheck` for property tests and `behave` for BDD.

`unittest` is *not* taught.

### Assertion style

Plain Python `assert` inside test methods. Pytest rewrites the assertion so the failure prints both sides:

```
>       assert power(1,100) == 5
E       assert None == 5
E        +  where None = power(1, 100)
```

For expected exceptions, use the context manager `pytest.raises`:

```python
def test_knownerror(self):
    with pytest.raises(AssertionError):
        power(2, -3)
```

Tests can live in a `class TestPower` or as bare `def test_*` functions; pytest discovers both. The example puts them in the same file as the production code, which is fine for a lecture but not normal practice.

### Fixtures

Not shown in the slides. Standard pytest knowledge: a fixture is a function decorated with `@pytest.fixture` whose return value is injected into any test that names it as an argument. Useful for setting up a fresh `Deck()` or `Game([Martin(), Martin()])` for each cribbage test.

### Parametrise

Not shown in the slides. Standard pytest knowledge: `@pytest.mark.parametrize("base,exp,expected", [(4,7,16384), (2,10,1024), (3,0,1)])` runs the same test body once per tuple.

### Mocking & dependency injection

Not covered in the slides. The `pytest-mock` plugin appears in the captured output but is not demonstrated. The cribbage lab forces you to confront this anyway: `agents.Martin.choose_play` calls `random.shuffle`, so to test a deterministic outcome you must either seed `random`, monkey-patch `random.shuffle`, or inject a fake agent — which is the point of the lab hint *"sometimes you need to change the code to make it easier to test."*

### Coverage

`coverage.py` is *not* mentioned by name. The closest the slides come is the AFL++ description: "instrumenting the code… find inputs that trigger every path through every conditional." That is branch coverage in spirit but driven by a fuzzer, not a coverage tool.

### Test design techniques

The slides do not name **equivalence partitioning**, **boundary-value analysis**, or **decision tables**. They do show the underlying instinct: the QuickCheck examples deliberately probe boundaries — `0` as a base, `1` as an exponent, negative bases with odd exponents, `INT_MAX` overflow. The `power(2,-3)` test is a one-element equivalence class for "negative exponents must error".

### Property-based testing (hypothesis)

Property testing is a major section, but the slides use **QuickCheck** (Haskell) for the demo, not Python's `hypothesis`. The lab points at **`pytest-quickcheck`**. The conceptual moves are the same:

1. State a universal property: *"for any base and exponent > 0, `b ** e >= b`"*.
2. Let the framework generate random inputs.
3. On failure, the framework **shrinks** to a minimal counterexample (`*** Failed! Falsified (after 18 tests and 5 shrinks): 0 1`).

Edge cases the slides surface this way: `base = 0`, negative base with odd exponent, fixed-width-integer overflow (`8^21 = -9223372036854775808`).

### Testing in CI

CI is not directly covered. The lab's "Bonus stuff" pushes adjacent practice: install a Git pre-commit hook that runs the test suite and rejects commits if anything fails. That is essentially CI on the developer's machine.

### Fuzz testing

Run random/corrupt inputs to find crashes; instrumented fuzzers aim for full-path coverage. Tool named: **AFL++** (`apfplus.plus`).

### Formal methods

`Lean 4` proof assistant; `seL4` "OS that you cannot hack" cited as the headline success story. Bath connection: Rod Chapman at AWS proves networking properties. The slides are blunt: monumental cost, only justified when failure is catastrophic (aviation, hyperscaler infra, roots of trust, crypto).

## pytest cheat sheet

```bash
# Run every test under the current directory
python -m pytest

# Run a specific file or test
python -m pytest path/to/file.py
python -m pytest path/to/file.py::TestPower::test_knowngood

# More verbose output, stop at first failure
python -m pytest -v -x
```

```python
# 1. Bare-function tests (pytest's preferred style)
def test_knowngood():
    assert power(4, 7) == 16384

# 2. Class-based grouping (used in the slides)
class TestPower:
    def test_knowngood(self):
        assert power(4, 7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2, -3)

# 3. Expected-exception assertion
with pytest.raises(ValueError, match="negative"):
    power(2, -3)

# 4. Fixtures (not in slides, standard practice)
import pytest

@pytest.fixture
def fresh_deck():
    from cribbage.deck import Deck
    return Deck()

def test_deck_has_52(fresh_deck):
    assert len(fresh_deck._cards) == 52

# 5. Parametrisation (not in slides, standard practice)
@pytest.mark.parametrize("b,e,expected", [
    (4, 7, 16384),
    (2, 10, 1024),
    (3, 0, 1),
])
def test_power_table(b, e, expected):
    assert power(b, e) == expected

# 6. Property test with pytest-quickcheck (lab recommendation)
import pytest_quickcheck   # registers the marker

@pytest.mark.randomize(b=int, e=int, min_num=1, max_num=20)
def test_power_grows(b, e):
    assert power(b, e) >= b
```

The pytest output format from the slides:

```
============================= test session starts ==============================
platform linux -- Python 3.13.2, pytest-8.3.4, pluggy-1.5.0
plugins: asyncio-0.24.0, mock-3.14.0
collected 3 items
power2.py ..F                                                           [100%]

=================================== FAILURES ===================================
____________________________ TestPower.test_failing ____________________________
>       assert power(1,100) == 5
E       assert None == 5
E        +  where None = power(1, 100)
========================= 1 failed, 2 passed in 0.01s ==========================
```

A single dot is a passing test, `F` is failing, `E` is errored, `s` is skipped.

## power.py vs power2.py

The two files are 99% identical:

```python
# power.py
class TestPower:
    def test_knowngood(self):
        assert power(4,7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2,-3)
```

```python
# power2.py — ONE extra method appended
class TestPower:
    def test_knowngood(self):
        assert power(4,7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2,-3)

    def test_failing(self):           # <-- added
        assert power(1,100) == 5
```

So `power2.py` is **not** a redesigned-for-testability version of `power.py`. It is the same code with one *new* test deliberately added that exposes a real bug. This is a teaching trick, not a refactor.

What the new test reveals is more interesting than the test itself. Reread the implementation:

```python
def power(base, exponent):
    assert(exponent >= 0)
    if exponent == 0:
        return 1
    if exponent == 1:
        return base
    if exponent & 1 == 1:
        return base * power(base*base, (exponent-1)//2)
    # NOTE: no return statement for the even-exponent branch!
```

The recursive `power(base*base, exponent//2)` line that should handle the even-exponent case is **missing**. So whenever `power` is called with an even exponent ≥ 2, Python falls off the end of the function and implicitly returns `None`. `power(1, 100)` is exactly that path — `100` is even — so the function returns `None`, the new test fails with `assert None == 5`, and the failure points the developer at the missing branch. The C version on the prior slide *does* have the equivalent fourth branch, so this is a Python-only bug introduced when the algorithm was ported.

The pedagogical point: the test suite for `power.py` (`test_knowngood` only checks `power(4,7)`, an *odd* exponent path) gives a false sense of safety. Adding *one* more case touches a previously-untested branch and the bug falls out immediately. That is regression testing and branch coverage in miniature.

## Lab walkthrough

Source: `lab/README.org`, the `lab/cribbage/` package, the `lab/cribbage.py` entry point.

**Goal:** practice writing tests against a real, deliberately buggy codebase. The learning outcome the lecturer cares about (and that is examinable) is "you tried writing tests" — not mastery of any specific framework.

### The simulator

`cribbage.py` is a five-line entry point:

```python
ai = Martin()
human = Martin()
game = Game([human, ai])
game.play()
```

Running `python3 cribbage.py` simulates a two-player game between two `Martin` agents (`agents.py`), where `Martin.choose_play` picks a card by `random.shuffle` and `choose_discards` discards two cards at random. The package layout is:

```
lab/cribbage/
  __init__.py
  card.py        # Card class: rank, suit, value, is_black_jack, str/repr
  deck.py        # Deck: builds and deals 52 cards
  round.py       # Round: hands, turn, box, discarding
  game.py        # Game: top-level loop, scoring, the play, the hand
  agents.py      # Agent / Martin (random AI) / Human (stdin)
  util.py        # all_equal, subset, str_cards
  scoring/
    __init__.py
    hand.py      # fifteens, pairs, runs, flushes
    play.py      # Play, check_*; Trick/Nob/Fifteen/Pair/Run classes
```

### Recommended toolchain

- `pytest` for unit tests.
- `pytest-quickcheck` for property tests.
- Optionally `behave` (Cucumber port) for behavioural tests — not required.

The README is explicit: *"the learning outcome we want is that you've tried writing tests; not that you know any particular framework."*

### Suggested unit / behavioural tests

From `README.org` section *Unit or behavioural tests*:

1. The Jack of Clubs has `value() == 10`.
2. The Jack of Hearts and the 3 of Spades return `False` from `is_black_jack()`.
3. A hand worth 4 points always prints *"and the rest don't score"*.
4. The maximum cribbage hand — four 5s plus a black-jack turn card — scores 27.
5. Hearts and Diamonds always print red.
6. Going round the cribbage board: up the outside lane, back down the inside.

What that maps to in code:

```python
# 1
def test_jack_of_clubs_value_is_10():
    assert Card("JC").value() == 10

# 2
def test_jack_of_hearts_is_not_black_jack():
    assert Card("JH").is_black_jack() is False

def test_three_of_spades_is_not_black_jack():
    assert Card("3S").is_black_jack() is False

# 3 — needs capsys to capture print output
def test_score_4_says_rest_dont_score(capsys):
    ...
    out = capsys.readouterr().out
    assert "and the rest don't score" in out

# 4 — the famous "29 hand" is JH 5S 5C 5D + 5H turn worth 29 in real
#     cribbage, but the README explicitly states 27 for "4 fives + black jack
#     turn". Either way: build that hand and assert score.
```

### Suggested property tests

From `README.org` section *Property tests*:

1. It is impossible to score 19 in the play (`game.py: _play_hand`).
2. When the game ends, **exactly one** player has score > 120.
3. No run in the play is ever longer than 7 cards (`scoring/play.py`).
4. You cannot score a pair from 5 matching cards (impossible — only 4 of each rank exist).

These directly stress the QuickCheck-style mindset: "for any randomly generated game state, this invariant must hold."

### Bugs the testing exercise will surface

Reading the supplied code with a tester's eye reveals real defects:

- `cribbage/scoring/play.py` line 39: `[PairRoyale(played[-3:])]` references an undefined name `played` (should be `self._played`). The pair-royale path crashes at runtime.
- `cribbage/scoring/play.py` line 91: `class PairImperiale` passes the name `"Pair Royale"` to its `super().__init__`, mis-labelling 12-point pair imperiales as pair royales.
- `cribbage/game.py` line 168: `printf(f"--- Pair imperiale!...")` — `printf` doesn't exist in Python; should be `print`. Crashes whenever a quad lands.
- `cribbage/game.py` line 119: `if play == 31` compares a `Play` object to an int; should be `play.count == 31`.
- `cribbage/scoring/hand.py` line 52: `card.suit` (the method object) is compared instead of `card.suit()` — flush detection is broken.
- `cribbage/scoring/hand.py`: `flushes()` returns an `int` (4, 5, or 0) but `game._play_hand` then iterates `str_cards(flushes)` over it, which will crash.
- `cribbage/round.py`: `get_box` is defined twice (harmless, second wins).
- `cribbage/card.py`: passing a 3-character `value` like `"10H"` sets `self._rank = 10` (an int) and never sets `self._suit` — `Card("10H")` is broken.

These are exactly what the README warns about: *"if you make a test that cannot pass… you might need to fix the code."*

### Expected coverage

Not stated as a numeric target. The reachable goal is to cover `card.py`, `scoring/hand.py`, and `scoring/play.py` thoroughly (these are pure, deterministic, and easy to test), and to test `game.py` only after injecting a deterministic agent so `random.shuffle` doesn't make every run different. That is the unstated lesson behind the "sometimes you need to change the code to make it easier to test" hint.

### Bonus stretch goals

- Wire the test suite into a Git **pre-commit hook** (`.git/hooks/pre-commit` runs `python -m pytest`; non-zero exit blocks the commit). The README links to the official Git docs for hooks.
- Try the **Lean Natural Numbers Game** for a taste of formal proof: <https://adam.math.hhu.de/#/g/leanprover-community/nng4>

## Pitfalls & emphasis

- **Even "correct" code is wrong.** The five `mean()` examples are the spine of the lecture: you have to know *how* your code is wrong, not whether it is.
- **`assert` is not a test.** It is debug scaffolding. With `-DNDEBUG=1` (C) or `python -O` it disappears, and your "checks" are gone. Use a real test framework for things that must hold in production.
- **Run tests with `python -m pytest`, not `pytest`.** The `-m` form ensures the local package is on `sys.path`. This is the form shown on every slide.
- **Pytest's output is the docs.** Read the failure block carefully — it shows the assertion, both sides, and where the value came from (`+ where None = power(1,100)`). That is enough to localise most bugs without a debugger.
- **Adding *one* test can expose a whole class of bugs.** `power2.py` is the canonical lesson: the original suite only hit odd-exponent paths, so an entire branch of the algorithm was untested.
- **Property tests are powerful but need the right property.** The slides walk through the iteration `b ** e > b` → fails on `0` → restrict to positive bases → fails on overflow with fixed-width ints → switch to `Integer`. Each failure refines either the property or the type.
- **Shrinking is the key feature.** A randomly generated counterexample of length 200 is useless; a minimal one (`0, 1`) tells you what to fix.
- **Behavioural tests put the spec in the customer's language.** The Cucumber `.feature` file is plain English; the `step_definitions` translate it. The win is that managers can read and (in principle) write the spec.
- **Fuzzers and formal methods are real tools, not academic curiosities** — but the cost curve is steep. Use them where a crash equals millions of dollars or human lives. Otherwise stop at unit + property tests.
- **Specific to the cribbage lab: the code is buggy on purpose.** A failing test that "looks right" probably *is* right and you've just found a defect. Open an issue, or fix it.
- **Some tests force a redesign.** Random AIs and stdin-bound humans can't be unit-tested as written. Inject a deterministic agent, seed `random`, or monkey-patch — this is the testability-driven-design lesson hidden in the lab.
- **Exam format reminder** (relevant context, not testing per se): 32 four-way multiple-choice questions, open notes, this term's lectures and labs are examinable.
