import os
import sys
import pandas as pd
import re

interval_regx = re.compile("\\x15(\d+_\d+)\\x15")


def find_last_timestamp(lines):
    for line in reversed(lines):
        m = interval_regx.findall(line)
        if m and len(m) == 1:
            return int(m[0].split("_")[1])
    return 0


if __name__ == "__main__":

    start = sys.argv[1]

    problem_regions = []

    not_actually_a_problem = []

    for root, dirs, files in os.walk(start):
        for file in files:
            if file.endswith(".cha"):
                print(file)

                # full = ""
                lines = []
                with open(os.path.join(root, file), "rU") as input:
                    for line in input:
                        if "subregion" in line and "rank" not in line:
                            last_ts = find_last_timestamp(lines)
                            problem_regions.append((file[:5], last_ts))
                        # full += line
                        lines.append(line)
                if 8 <= int(file[3:5]) <= 13:
                    if any("lowest ranked" in x for x in lines):
                        not_actually_a_problem.append(file[:5])



    # uncomment this to filter out instances where
    # there is at least the "lowest ranked" comment
    # problem_regions = [x for x in problem_regions if x not in not_actually_a_problem]


    df = pd.DataFrame(problem_regions, columns=["file", "region_onset"])

    df.to_csv("files_with_unranked_subregions.csv", index=False)