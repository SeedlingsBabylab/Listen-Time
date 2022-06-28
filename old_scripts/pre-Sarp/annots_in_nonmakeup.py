import sys

import pandas as pd


def check_region_bounds(regions, all_annots):
    """
    :param regions: bounds for non makeup subregions
    :param all_annots: all the annotations in that file
    :return: bool, whether all annotations fall within
                    non-makeup subregions
    """
    query_regs = []
    for reg in regions:
        query_regs.append("({} < onset < {})".format(reg[0], reg[1]))

    query_str = " | ".join(query_regs)

    non_makeup_annots = all_annots.query(query_str)

    if non_makeup_annots.shape[0] == all_annots.shape[0]:
        return True
    return False


if __name__ == "__main__":
    all_bl = pd.read_csv(sys.argv[1])
    subregs = pd.read_csv(sys.argv[2])
    columns = ["region"] + list(all_bl.columns.values)


    query_str = "(SubjectNumber == \"{}\") & (audio_video == \"audio\")"

    results = []
    for i, x in subregs.groupby("file"):
        print(i)
        regions = []
        # ignore file/Subject Number (?) less than 8
        if int(i[3:]) < 8:
            continue
        for j, y in x.iterrows():
            # for Subject Number 8-13, ignore region number 5
            if 8 <= int(y.file[3:]) <= 13:
                if y.region_num  != 5:
                    start = y.orig_index*5*60*1000
                    end = start + 60*60*1000
                    regions.append((start, end))

            # for Subject Number 14+, ignore region number 4, 5
            if int(y.file[3:]) >= 14 and y.region_num not in [4, 5]:
                start = y.orig_index * 5 * 60 * 1000
                end = start + 60 * 60 * 1000
                regions.append((start, end))

        # query all annots belong to the file/subjectNumber, print to csv whether the annots are within the subregion 1 hr(?) timeframe
        all_annots = all_bl.query(query_str.format(y.file))
        only_in_nonmakeup = check_region_bounds(regions, all_annots)
        results.append((i, only_in_nonmakeup))

    df = pd.DataFrame(results, columns=["file", "all_annots_in_non_makeup_regions"])

    df.to_csv("all_annots_in_non_makeup_regions.csv", index=False)
