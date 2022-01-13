import os
import sys
import re

import pandas as pd
import pyclan as pc

subr_regx = re.compile('subregion (\d+) of (\d+)')


regions = []

def process_file(path):
    results = {}
    cf = pc.ClanFile(path)
    pfx = cf.filename[:5]
    # get all comments that contain subregion and sort by offset
    subrs = filter(lambda x: "subregion" in x.line, cf.get_user_comments())
    subrs.sort(key=lambda x: x.offset)
    # subregion lines should be in pairs
    if len(subrs) % 2 != 0:
        raise Exception

    for x in subrs:
        m = subr_regx.findall(x.line)
        # each subregion line should only have one regex match
        if len(m) > 1:
            raise Exception
        m=m[0]
        # each subregion index should have two subregion lines,
        # and the smaller offset of the lines should be the onset of subregion,
        # larger offset of the lines be the offset
        if m[0] not in results:
            results[m[0]] = [x.offset]
        else:
            results[m[0]].append(x.offset)

    # filename, subregion index, onset, offset
    results = [[pfx, int(key), val[0], val[1]] for key, val in results.items()]
    regions.extend(results)




if __name__ == "__main__":

    #get subregion from all cha file in the directory, print file name if exception
    cha_dir = sys.argv[1]
    files = [os.path.join(cha_dir, x) for x in os.listdir(cha_dir) if x.endswith(".cha")]
    for file in files:
        try:
            process_file(file)
        except:
            print(os.path.basename(file))

    df = pd.DataFrame(regions, columns=['file', 'reg_num', 'onset', 'offset'])
    df.to_csv("subregions.csv", index=False)
