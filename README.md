# Santa 2026 - The Elf Calculator: starter solution

`starter.py` generates a valid submission (`id,program` CSV) for the 1,000 scored puzzles.

## Usage

```bash
python3 starter.py --demo                                  # worked example from the Data page
python3 starter.py solve puzzles.csv submission.csv        # generate submission
python3 starter.py check puzzles.csv submission.csv        # validate against all rules
```

Unzip the competition data first: `unzip santa-2026.zip` (contains `puzzles.csv`,
`practice_puzzles.csv`, `sample_submission.csv`).

## How it works

Per puzzle, greedily emit one instruction per target when two existing register
values combine to it (`-`, `/`, `*`, `+`), otherwise build the target by binary
expansion from 1 (double per bit, add 1 for set bits) using 2 scratch registers.
`simulate()` replays a program and enforces every rule: 48 registers, positive
integers only, exact division, `value_limit` on intermediates, defined sources,
<= 4096 instructions, <= 128 KiB per cell, all targets produced.

## Baseline result on the real scored puzzles (puzzles.csv)

- 1,000 programs, all valid under the simulator (no missing targets, all limits respected)
- **Total score: 1,489,337 instructions** (lower is better)
- Max instructions in any single puzzle: 2,873 (same as the official sample submission's max)
- Max program cell: 34,477 bytes (limit 131,072)
- submission.csv size: 20,867,730 bytes; sha256 e5011a781e73faff5357c5b6f1d4793754cf8ea11a1b735fa84e351253fff16e
- Practice set (200 puzzles): total score 302,734

Reproduce: `python3 starter.py solve puzzles.csv submission.csv && python3 starter.py check puzzles.csv submission.csv`
