import os
import sys
import re
import pandas as pd
import csv


interval_regx = re.compile("\\x15(\d+_\d+)\\x15")


def pull_regions(path, month):
    if month < 8:
        raise Exception("No subregions in this file")
    begin_extras = []
    end_extras = []
    begin_makeup = []
    end_makeup = []
    begin_skip = []
    end_skip = []
    begin_subreg = []
    end_subreg = []
    begin_sil = []
    end_sil = []

    with open(path, "rU") as input:
        lines = []
        print("here")
        summary = []
        count_annot = 0
        for line in input:
            if "_y_" in line or "_n_" in line or "_u_" in line:
                count_annot += 1
            if "begin extra time" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                begin_extras.append(ts)
                summary.append("begin extra "+str(ts)+"\n")
            elif "end extra time" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                end_extras.append(ts)
                summary.append("end extra "+str(ts)+"\n")
            elif "begin makeup region" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                begin_makeup.append(ts)
                summary.append("begin makeup "+str(ts)+"\n")
            elif "end makeup region" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                end_makeup.append(ts)
                summary.append("end makeup "+str(ts)+"\n")
            elif "begin skip" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                begin_skip.append(ts)
                summary.append("begin skip "+str(ts)+"\n")
            elif "end skip" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_last_timestamp(lines)
                end_skip.append(ts)
                summary.append("end skip "+str(ts)+"\n")

            elif "subregion" in line and "starts" in line:
                if ("ranked 1" in line or "ranked 2" in line or "ranked 3" in line):
                    summary.append(str(count_annot)+" annotations\n")
                    count_annot = 0
                    ts = get_line_timestamp(line)
                    begin_subreg.append(ts)
                    summary.append("begin subreg "+str(ts)+"\n")
                elif ("ranked 4" in line and month<14):
                    summary.append(str(count_annot)+" annotations\n")
                    count_annot = 0
                    ts = get_line_timestamp(line)
                    begin_subreg.append(ts)
                    summary.append("begin subreg "+str(ts)+"\n")
            elif "subregion" in line and "ends" in line:
                if ("ranked 1" in line or "ranked 2" in line or "ranked 3" in line):
                    summary.append(str(count_annot)+" annotations\n")
                    count_annot = 0
                    ts = get_line_timestamp(line, start = False)
                    end_subreg.append(ts)
                    summary.append("end subreg "+str(ts)+"\n")
                elif ("ranked 4" in line and month<14):
                    summary.append(str(count_annot)+" annotations\n")
                    count_annot = 0
                    ts = get_line_timestamp(line, start = False)
                    end_subreg.append(ts)
                    summary.append("end subreg "+str(ts)+"\n")

            elif "silence" in line and "starts" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_line_timestamp(line)
                begin_sil.append(ts)
                summary.append("begin silence "+str(ts)+"\n")
            elif "silence" in line and "ends" in line:
                summary.append(str(count_annot)+" annotations\n")
                count_annot = 0
                ts = get_line_timestamp(line, start = False)
                end_sil.append(ts)
                summary.append("end silence "+str(ts)+"\n")
            else:
                lines.append(line)
        summary.append(str(count_annot)+" annotations\n")
    end_sil = list(set(end_sil))
    if len(begin_extras) != len(end_extras):
        print(begin_extras, end_extras)
        raise Exception("EXTRA: begin count does not match end count")
    elif len(begin_makeup) != len(end_makeup):
        print(begin_makeup, end_makeup)
        raise Exception("MAKEUP: begin count does not match end count")
    elif len(begin_skip) != len(end_skip):
        raise Exception("SKIP: begin count does not match end count")
    elif len(begin_sil) != len(end_sil):
        print(begin_sil, end_sil)
        raise Exception("SILENCE: begin count does not match end count")
    else:
        return begin_extras, end_extras, begin_makeup, \
               end_makeup, begin_skip, end_skip,\
               begin_subreg, end_subreg, begin_sil,\
               end_sil, summary


def get_line_timestamp(line, start = True):
    words = line.split()
    print("issue here")
    if start:
        print("start", len(words), words.index("starts"))
        return int(float(words[words.index("starts")+2]))
    else:
        print("end",len(words), words.index("ends"))
        return int(float(words[words.index("ends")+2]))


def get_last_timestamp(lines):
    for line in reversed(lines):
        m = interval_regx.findall(line)
        if m and len(m) == 1:
            return int(m[0].split("_")[1])
    return 0

def sum_regions(begins, ends):
    joined = zip(begins, ends)
    total = 0
    for x in joined:
        if x[1] < x[0]:
            raise Exception("begin is after end: begin: {}  end: {}".format(x[0], x[1]))
        total += x[1] - x[0]
    return total

def sil_subr_overlap_sum(month,
                         b_sil, e_sil,
                         b_sub, e_sub,
                         b_mak, e_mak,
                         b_ext, e_ext):

    """
    sum of all silence +subregion overlap time
    :param month:
    :param b_sil: silence onsets
    :param e_sil: silence offsets
    :param b_sub: subregion onsets
    :param e_sub: subregion offsets
    :param b_mak: makeup onsets
    :param e_mak: makeup offsets
    :return: total silence overlap time
    """
    subregs = zip(b_sub, e_sub)
    sils = zip(b_sil, e_sil)
    makeups = zip(b_mak, e_mak)

    overlap = 0
    for silreg in sils:
        overlap += region_overlap(silreg, subregs)
        overlap += region_overlap(silreg, makeups)
        overlap += region_overlap(silreg, extra)

    return overlap

def region_overlap(sil, subregs):
    sum = 0
    for reg in subregs:
        if reg[0] < sil[0] < reg[1] < sil[1]:
            return(reg[1] - sil[0])
        elif reg[0] < sil[0] < sil[1] < reg[1]:
            return(sil[1] - sil[0])
        elif sil[0] < reg[0] < sil[1] < reg[1]:
            return(sil[1] - reg[0])




if __name__ == "__main__":

    file = sys.argv[1]
    # subregs = sys.argv[2]

    results = []

    fname = os.path.basename(file)
    month = int(fname[3:5])

    extra_sum = 0
    makeup_sum = 0
    skip_sum = 0
    overlap_sum = 0
    subr_sum = 0
    try:
        print("HERE")
        b_extra, e_extra, b_makup, e_makup, \
        b_skip, e_skip, b_subr, e_subr, b_sil, \
        e_sil, summary  = pull_regions(file, month)
        if b_extra:
            try:
                extra_sum = sum_regions(b_extra, e_extra)
                print("1")
            except Exception as e:
                print(fname)
                print(e)
                print()
        if b_makup:
            try:
                makeup_sum = sum_regions(b_makup, e_makup)
                print("2")
            except Exception as e:
                print(fname)
                print(e)
                print()
        if b_skip:
            try:
                skip_sum = sum_regions(b_skip, e_skip)
                print("3")
            except Exception as e:
                print(fname)
                print(e)
                print()
        if b_sil:
            try:
                overlap_sum = sil_subr_overlap_sum(int(fname[3:5]),
                                                   b_sil, e_sil,
                                                   b_subr, e_subr,
                                                   b_makup, e_makup)

                print("4")
            except:
                print()
        if b_subr:
            try:
                subr_sum = sum_regions(b_subr, e_subr)
                print("5")
            except Exception as e:
                print(fname)
                print(e)
                print()

        results.append((os.path.basename(file)[:5], extra_sum, makeup_sum, skip_sum, overlap_sum, subr_sum))

    except Exception as e:
        print(fname)
        print(e)
        print()

    # with open(r"total_listened_time.csv", 'a') as f:
    #     writer = csv.writer(f)
    #     for row in results:
    #         writer.writerow(row)

    sumpath = "/".join(file.split("/")[:-1])
    print(sumpath)
    with open(sumpath+"/summary.txt", 'w') as f:
        for l in summary:
            f.write(l)
    # df = pd.DataFrame(results, columns=["file", "extra", "makeup", "skip", "overlap", "subregions"])
    # print(df)
    # df.to_csv("total_listened_time.csv", index=False)
