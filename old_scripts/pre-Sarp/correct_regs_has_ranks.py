import csv
import pandas as pd
import sys



if __name__ == "__main__":


    algo5 = pd.read_csv(sys.argv[1])
    subr = pd.read_csv(sys.argv[2])
    wrong_regs = pd.read_csv(sys.argv[3])
    unranked = pd.read_csv(sys.argv[4])

    results = []

    wrong_reg_files = wrong_regs.file.unique()
    unranked_files = unranked.file.unique()

    for x in algo5.file.unique():
        if x not in wrong_reg_files and x not in unranked_files:
            results.append(x)

    df = pd.DataFrame(results, columns = ["file"])
    df.to_csv("correct_subregions_has_ranks.csv", index=False)


    results = []
    for x in algo5.file.unique():
        if x not in wrong_reg_files and x in unranked_files:
            results.append(x)

    df = pd.DataFrame(results, columns=["file"])
    df.to_csv("correct_subregions_missing_ranks.csv", index=False)