import os
import sys
import pandas as pd
import re

interval_regx = re.compile("\\x15(\d+_\d+)\\x15")


def onset(index):
    return index*5*60*1000

def offset(index):
    return onset(index) + 3600000

def onset_in_bounds(x, y, reg):
    reg_onset = onset(reg.orig_index)
    reg_offset = offset(reg.orig_index)
    if x[0] <= reg_onset <= y[1]:
        return "onset"
    if x[0] <= reg_offset <= y[1]:
        return "offset"
    return False


def find_last_timestamp(lines):
    for line in reversed(lines):
        m = interval_regx.findall(line)
        if m and len(m) == 1:
            ts = m[0].split("_")
            return (int(ts[0]), int(ts[1]))
    return (0, 0)

start_template = "REWRITTEN REGION   ** START ** -- %xcom:\tsubregion {} of {} (ranked {} of {}) starts at {} -- previous timestamp adjusted:\n"
end_template =   "REWRITTEN REGION   ** END **   -- %xcom:\tsubregion {} of {} (ranked {} of {}) ends at {} -- previous timestamp adjusted:\n"

def process(file, top5):
    fname = os.path.basename(file)
    top5 = top5.sort_values(by="orig_index")

    top5['chron_rank'] = [x for x in range(1, top5.shape[0]+1)]
    lines = []
    with open(file, "rU") as input:
        with open(os.path.join(output_dir, fname), "wb") as out:
            lines = []

            written_begin_comms = []
            written_end_comms = []

            for line in input:
                out.write(line)
                m = interval_regx.findall(line)
                if m and len(m) == 1:
                    ts = m[0].split("_")
                    ts = (int(ts[0]), int(ts[1]))

                    num_found = 0

                    for i, r in top5.iterrows():
                        lookup = onset_in_bounds(find_last_timestamp(lines), ts, r)
                        if lookup:
                            # if r.region_num == 2 or r.region_num == 3:
                            #     print
                            if lookup == "onset":
                                if r.region_num not in written_begin_comms:
                                    out.write(start_template.format(r.chron_rank,
                                                                    top5.shape[0],
                                                                    r.region_num,
                                                                    top5.shape[0],
                                                                    onset(r.orig_index)))
                                written_begin_comms.append(r.region_num)
                                lines.append(line)
                                num_found += 1
                            elif lookup == "offset":
                                if r.region_num not in written_end_comms:
                                    out.write(end_template.format(r.chron_rank,
                                                                  top5.shape[0],
                                                                  r.region_num,
                                                                  top5.shape[0],
                                                                  offset(r.orig_index)))
                                written_end_comms.append(r.region_num)
                                lines.append(line)
                                num_found += 1



                    if num_found == 0:
                        # out.write(line)
                        lines.append(line)
                    if num_found > 1:
                        print("PROBLEM - {}".format(ts[0]))

                else:
                    # out.write(line)
                    lines.append(line)





if __name__ == "__main__":

    input_dir = sys.argv[1] # folder with .cha's
    output_dir = sys.argv[2] # where to dump new cha's with new subregion comms
    top5 = pd.read_csv(sys.argv[3]) # csv with all_cha_top5
    subr_v_algo = pd.read_csv(sys.argv[4]).file.unique() # output from subregs_com_vs_algo.py (with window=0)

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".cha"):
                pfx = file[:5]
                file5 = top5.query("file == \"{}\"".format(pfx))

                # we only process those files that have at least 1
                # instance of a subregion not being where it should
                # be exactly (i.e. window of 0 milliseconds) according
                # to the original subregion picking algorithm
                if pfx in subr_v_algo:
                    process(os.path.join(root, file), file5)
                    print(pfx)
