import csv
import json
import sys

REGISTERS = 48
MAX_INSTRUCTIONS = 4096
MAX_CELL_BYTES = 131072
OPERATORS = ("+", "-", "*", "/")


def build_program(starting_values, targets, value_limit):
    program = []
    reg_value = dict(enumerate(starting_values))
    covered = set(starting_values)
    free = list(range(len(starting_values), REGISTERS))
    scratch = free.pop(0)

    def emit(op, i, j, d=scratch):
        a, b = reg_value[i], reg_value[j]
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        else:
            r = a // b
        if r <= 0 or r > value_limit:
            raise ValueError(f"illegal result {r}")
        program.append([op, i, j, d])
        reg_value[d] = r
        covered.add(r)
        return d

    one = next((r for r, v in reg_value.items() if v == 1), None)
    if one is None:
        one = free.pop(0)
        emit("/", 0, 0, d=one)

    for t in targets:
        if t in covered:
            continue
        hit = None
        items = list(reg_value.items())
        for ri, a in items:
            for rj, b in items:
                if a > b and a - b == t:
                    hit = ("-", ri, rj)
                    break
                if a % b == 0 and a // b == t:
                    hit = ("/", ri, rj)
                    break
                if a * b == t:
                    hit = ("*", ri, rj)
                    break
                if a + b == t:
                    hit = ("+", ri, rj)
                    break
            if hit:
                break
        if hit:
            emit(*hit)
            continue
        emit("/", one, one, d=scratch)
        for bit in bin(t)[3:]:
            emit("+", scratch, scratch, d=scratch)
            if bit == "1":
                emit("+", scratch, one, d=scratch)
    return program


def simulate(starting_values, program, targets, value_limit):
    regs = [None] * REGISTERS
    for i, v in enumerate(starting_values):
        regs[i] = v
    produced = set(starting_values)
    for instr in program:
        if len(instr) != 4:
            raise ValueError("instruction must have 4 elements")
        op, i, j, d = instr
        if op not in OPERATORS:
            raise ValueError(f"bad operator {op!r}")
        for r in (i, j, d):
            if not isinstance(r, int) or not 0 <= r < REGISTERS:
                raise ValueError(f"register index out of range: {r!r}")
        if regs[i] is None or regs[j] is None:
            raise ValueError("undefined source register")
        a, b = regs[i], regs[j]
        if op == "+":
            r = a + b
        elif op == "-":
            if a <= b:
                raise ValueError("non-positive subtraction")
            r = a - b
        elif op == "*":
            r = a * b
        else:
            if a % b != 0:
                raise ValueError("inexact division")
            r = a // b
        if r <= 0 or r > value_limit:
            raise ValueError("value out of range")
        regs[d] = r
        produced.add(r)
    missing = [t for t in targets if t not in produced]
    return len(program), missing


def encode_cell(program):
    return json.dumps(program, separators=(",", ":"))


def validate_program(puzzle, program):
    cell = encode_cell(program)
    if len(cell.encode("utf-8")) > MAX_CELL_BYTES:
        raise ValueError("program cell exceeds 128 KiB")
    if len(program) > MAX_INSTRUCTIONS:
        raise ValueError(f"{len(program)} instructions > {MAX_INSTRUCTIONS}")
    sv = json.loads(puzzle["starting_values"])
    tg = json.loads(puzzle["targets"])
    vl = int(puzzle["value_limit"])
    score, missing = simulate(sv, program, tg, vl)
    if missing:
        raise ValueError(f"missing targets {missing}")
    return score


def demo():
    puzzle = {"starting_values": "[3]", "targets": "[1, 2, 5, 8]", "value_limit": "9"}
    program = build_program(json.loads(puzzle["starting_values"]),
                            json.loads(puzzle["targets"]),
                            int(puzzle["value_limit"]))
    score = validate_program(puzzle, program)
    print(f"instructions: {score}")
    w = csv.writer(sys.stdout)
    w.writerow(["id", "program"])
    w.writerow(["example_0001", encode_cell(program)])


def solve(puzzles_path, submission_path):
    with open(puzzles_path, newline="", encoding="utf-8") as f:
        puzzles = list(csv.DictReader(f))
    ids = [p["id"] for p in puzzles]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate puzzle ids")
    total = 0
    with open(submission_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "program"])
        for puzzle in puzzles:
            sv = json.loads(puzzle["starting_values"])
            tg = json.loads(puzzle["targets"])
            vl = int(puzzle["value_limit"])
            program = build_program(sv, tg, vl)
            total += validate_program(puzzle, program)
            w.writerow([puzzle["id"], encode_cell(program)])
    print(f"wrote {len(puzzles)} programs to {submission_path}, total score {total}")


def check(puzzles_path, submission_path):
    with open(puzzles_path, newline="", encoding="utf-8") as f:
        puzzles = {p["id"]: p for p in csv.DictReader(f)}
    with open(submission_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != ["id", "program"]:
            raise ValueError(f"bad header: {header}")
        rows = list(reader)
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate ids in submission")
    if sorted(ids) != sorted(puzzles):
        raise ValueError("submission ids do not match puzzle ids exactly")
    total = 0
    for pid, cell in rows:
        if len(cell.encode("utf-8")) > MAX_CELL_BYTES:
            raise ValueError(f"{pid}: program cell exceeds 128 KiB")
        program = json.loads(cell)
        try:
            total += validate_program(puzzles[pid], program)
        except ValueError as e:
            raise ValueError(f"{pid}: invalid program ({e})")
    print(f"submission valid, total score {total}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        demo()
    elif len(sys.argv) == 4 and sys.argv[1] == "solve":
        solve(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[1] == "check":
        check(sys.argv[2], sys.argv[3])
    else:
        sys.exit("usage: python3 starter.py --demo | solve puzzles.csv submission.csv | check puzzles.csv submission.csv")
