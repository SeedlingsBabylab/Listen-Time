import pandas as pd

coms = pd.read_csv("orig_subreg_comments.csv")
algo = pd.read_csv("all_cha_top5.csv")


coms['fprefix'] = coms.file.str[:5]
algo['onset'] = algo.orig_index*5*60*1000

def region_exists(reg, algo_regs):
    for i, other in algo_regs.iterrows():
        if close(reg, other):
            return True
    return False


def close(ts, other, window=1000):
    # if ts.fprefix == "01_10" and ts.onset == 35399580 and other.onset == 35400000:
    #     print
    start_match = (other.onset - window) <= ts.onset <= (other.onset + window)
    w1 = other.onset + 3600000 - window
    w2 = other.onset + 3600000 + window
    end_match = (other.onset + 3600000 - window) <= ts.offset <= (other.onset + 3600000 + window)

    if start_match and end_match:
        return True
    return False




problems = []
for i, f in coms.groupby('fprefix'):
    if i == "03_08":
        print()
    for j, r in f.iterrows():
        algo_regs = algo.query("file == \"{}\"".format(i))
        if not region_exists(r, algo_regs):
            problems.append((r.fprefix, r.onset))

probs = pd.DataFrame(problems, columns=['file', 'onset'])

probs['subject'] = probs.file.str[0:2]
probs['month'] = probs.file.str[3:5]

probs.to_csv("subreg_comment_not_in_orig_algo_output_1_SECOND_WINDOW.csv", index=False)



