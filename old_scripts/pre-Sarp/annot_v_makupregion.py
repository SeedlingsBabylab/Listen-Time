import sys

import pandas as pd


if __name__ == "__main__":
    # creating data frame with column names from all_bl(all basic level file) column names plus one extra column of 'region'
    all_bl = pd.read_csv(sys.argv[1])
    subregs = pd.read_csv(sys.argv[2])
    columns = ["region"] + list(all_bl.columns.values)
    df = pd.DataFrame(columns=list(all_bl.columns.values)+['region'])

    query_str = "(SubjectNumber == \"{}\") & ({} <= onset <= {}) & (audio_video == \"audio\")"

    # group subregions by file name, query annots from all basic level that is within 1 hour(?) of the subregion origin index
    for i, x in subregs.groupby("file"):
        for j, y in x.iterrows():
            # if subjectNumber is 8-13, only use region number 5
            if 8 <= int(y.file[3:]) <= 13:
                if y.region_num  == 5:
                    start = y.orig_index*5*60*1000
                    end = start + 60*60*1000
                    annots = all_bl.query(query_str.format(y.file, start, end))
                    annots['region'] = y.region_num
                    df = df.append(annots)
            # if subject Number is 14+, use region number 4 or 5
            if int(y.file[3:]) >= 14 and y.region_num  in [4, 5]:
                start = y.orig_index * 5 * 60 * 1000
                end = start + 60 * 60 * 1000
                annots = all_bl.query(query_str.format(y.file, start, end))
                annots['region'] = y.region_num
                df = df.append(annots)

    df.to_csv("annots_in_makeup_regions.csv", index=False)
