import csv
import json
import sys

REGISTERS = 48
MAX_INSTRUCTIONS = 4096


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
    for op, i, j, d in program:
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
        elif op == "/":
            if a % b != 0:
                raise ValueError("inexact division")
            r = a // b
        else:
            raise ValueError("bad operator")
        if r <= 0 or r > value_limit:
            raise ValueError("value out of range")
        regs[d] = r
        produced.add(r)
    missing = [t for t in targets if t not in produced]
    return len(program), missing


def demo():
    starting_values = [3]
    targets = [1, 2, 5, 8]
    value_limit = 9
    program = build_program(starting_values, targets, value_limit)
    score, missing = simulate(starting_values, program, targets, value_limit)
    print(json.dumps(program))
    print(f"instructions: {score}, missing targets: {missing}")


def solve_file(in_path, out_path):
    with open(in_path, newline="") as f:
        rows = list(csv.DictReader(f))
    total = 0
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "program"])
        for row in rows:
            sv = json.loads(row["starting_values"])
            tg = json.loads(row["targets"])
            vl = int(row["value_limit"])
            program = build_program(sv, tg, vl)
            score, missing = simulate(sv, program, tg, vl)
            if missing or score > MAX_INSTRUCTIONS:
                raise ValueError(f"{row['id']}: invalid program (missing={missing})")
            total += score
            w.writerow([row["id"], json.dumps(program)])
    print(f"wrote {len(rows)} programs to {out_path}, total score {total}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        demo()
    elif len(sys.argv) == 3:
        solve_file(sys.argv[1], sys.argv[2])
    else:
        sys.exit("usage: python3 starter.py puzzles.csv submission.csv | --demo")
