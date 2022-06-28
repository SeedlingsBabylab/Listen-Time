import csv
import sys
import os
import pandas as pd

class group:
    def __init__(self, algo, curr):
        self.algo = algo
        self.curr = curr


def diff(r, r2, lowest):
    if abs(r.onset - r2.onset) < abs(r.onset - lowest.onset):
        # print "hello"
        return r2
    return lowest


def compare(algo, subr):
    groups = []
    for i, r in subr.iterrows():
        lowest = algo.iloc[0]
        for j, r2 in algo.iterrows():
            lowest = diff(r, r2, lowest)
        groups.append(group(lowest, r))
    return groups



if __name__ == "__main__":

    algo5 = pd.read_csv(sys.argv[1])
    subrg = pd.read_csv(sys.argv[2])


    all_files = set([x[:5] for x in os.listdir("all_cha") if x[3:5] not in ["06", "07"]])

    all_files2 = set([x for x in algo5.file.unique() if x[3:5] not in ["06", "07"]])

    results = []
    for f, r in algo5.groupby("file"):
        print(f)
        sub = subrg.query("file == \"{}\"".format(f))
        if sub.shape[0] > 0:
            results.extend(compare(r, sub))

    output = []
    for x in results:
        output.append(
            (x.algo.file, x.algo.onset, x.curr.onset, x.algo.onset - x.curr.onset,
             x.algo.offset, x.curr.offset, x.algo.offset - x.curr.offset, x.algo.region_num)
        )

    df = pd.DataFrame(output, columns = ["file", "onset_correctSR", "onset_currentSR",
                                 "onset_timediff", "offset_correctSR", "offset_currentSR",
                                 "offset_timediff", "rank_correct"])

    df.to_csv("algo_vs_current_subregion_overlap.csv", index=False)

    # all = set([x for x in algo5.file.unique() if x[3:5] not in ["06", "07"]])
    #
    # files = pd.DataFrame(df.file.unique(), columns=['file'])
    # files['subj'] = files.file.str[:2]

    # for i, g in files.groupby("subj"):
    #     if g.shape[0] != 10:
    #         print i
    #
    for i, g in df.groupby("file"):
        if g.shape[0] != 5:
            print("i: {}   g: {}".format(i, g.shape[0]))


    print("missing 1-5 in rank correct: ")
    for i, g in df.groupby("file"):
        if any(x not in g.rank_correct.values for x in [1, 2, 3, 4, 5]):
            print(i)

    new_df = pd.DataFrame(columns=list(df.columns) + ['file_contains_diff', 'region_onset_diff', "region_offset_diff", "onset_diff_minutes", "offset_diff_minutes"])

    df['file_contains_diff'] = "F"
    df['region_onset_diff'] = "F"
    df['region_offset_diff'] = "F"
    df['onset_diff_minutes'] = 0
    df['offset_diff_minutes'] = 0



    for i, g in df.groupby('file'):
        if any(abs(x) > 1000 for x in g.onset_timediff) or any(abs(y) >  1000 for y in g.offset_timediff):
            g.file_contains_diff = "T"
        new_df = new_df.append(g)

    final_df = pd.DataFrame(columns=new_df.columns)

    for i, r in new_df.iterrows():
        if abs(r.onset_timediff) > 1000:
            r.region_onset_diff = "T"
            r.onset_diff_minutes = float(r.onset_timediff) / 1000 / 60
        if abs(r.offset_timediff) > 1000:
            r.region_offset_diff = "T"
            r.offset_diff_minutes = float(r.offset_timediff) / 1000 / 60
        final_df = final_df.append(r)

    final_df.to_csv("algo_vs_current_subregion_overlap.csv", index=False)


    print()

