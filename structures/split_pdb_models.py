#!/usr/bin/env python3

import sys
from pathlib import Path

def split_pdb_models(input_pdb):
    input_pdb = Path(input_pdb)
    outdir = input_pdb.with_suffix("")
    outdir.mkdir(exist_ok=True)

    model_lines = []
    model_num = None
    in_model = False

    with open(input_pdb, "r") as f:
        for line in f:
            record = line[:6].strip()

            if record == "MODEL":
                in_model = True
                model_lines = [line]
                parts = line.split()
                model_num = parts[1] if len(parts) > 1 else None

            elif record == "ENDMDL":
                model_lines.append(line)

                if model_num is None:
                    model_num = "unknown"

                output_file = outdir / f"{input_pdb.stem}_model_{model_num}.pdb"
                with open(output_file, "w") as out:
                    out.writelines(model_lines)

                in_model = False
                model_lines = []
                model_num = None

            elif in_model:
                model_lines.append(line)

    print(f"Wrote split models to: {outdir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} input.pdb")
        sys.exit(1)

    split_pdb_models(sys.argv[1])
