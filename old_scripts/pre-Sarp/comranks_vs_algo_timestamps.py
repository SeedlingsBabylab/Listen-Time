import os
import pandas as pd
import sys



def process(subreg, unranked, probs):
    # probs = pd.DataFrame(columns = ["file", "region_onset"])
    for i, x in unranked.iterrows():
        for j, y in subreg.iterrows():
            if x.region_onset == y.onset:
                probs = probs.append({"file": x.file, "region_onset": x.region_onset},
                                     ignore_index=True)
    return probs



if __name__ == "__main__":

    subregs = pd.read_csv(sys.argv[1])
    unranked = pd.read_csv(sys.argv[2])

    probs = pd.DataFrame(columns=["file", "region_onset"])

    for f, entries in subregs.groupby("file"):
        norank = unranked.query("file == \"{}\"".format(f))
        if norank.shape[0] > 0:
            probs = process(entries, norank, probs)

    probs.to_csv("subregion_norank_andalso_not_algo.csv", index=False)