import pandas as pd
import sys
import os
import pyclan as pc


if __name__ == "__main__":
    problems = pd.read_csv(sys.argv[1])
    cha_dir = sys.argv[2]
    out_dir = sys.argv[3]
    cha_files = filter(lambda x: x.endswith(".cha"), os.listdir(cha_dir))
    files = {}
    for file in cha_files:
        files[file[:5]] = os.path.join(cha_dir, file)


    for pfx, annots in problems.groupby('SubjectNumber'):
        cf = pc.ClanFile(files[pfx])
        coms = [x for x in cf.get_user_comments() if "subregion" not in x.line and "silence" not in x.line]
        with open(os.path.join(out_dir, pfx), 'wb') as out:
            for com in coms:
                out.write("{}  ---  {}\n".format(com.line.replace("\n", ""), com.onset))

