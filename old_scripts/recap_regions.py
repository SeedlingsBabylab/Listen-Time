import pyclan as pc
import csv
import re
import sys
import os.path
import pandas as pd


subr_regx = re.compile('subregion (\d*) ?of (\d*)') # There are some cases where the numbering is missing
keyword_list = ["subregion", "silence", "skip", "makeup", "make-up", "make up"]


def pull_regions(path):
    skip_count = None
    skip_time = None
    extra_count = None
    extra_time = None
    makeup_count = None
    makeup_time = None
    silence_time = None
    sub_start = None
    silence_start = None
    skip_start = None
    makeup_start = None
    extra_start = None
    results = {}
    issues = []


    cf = pc.ClanFile(path)
    pfx = cf.filename[:5]

    comments = cf.get_user_comments()
    comments.sort(key = lambda x: x.offset)
    #print comments

    for cline in comments:
        line = cline.line
        if "subregion" in line:
            m = subr_regx.findall(line)
            if len(m) > 1:
                issues.append([cline.index, line, "subregion comment repeated"])
            if "starts" in line:
                if sub_start is not None:
                    issues.append([sub_start.index, sub_start.line, "subregion without end"])
                    continue
                if len(m[0])<2:
                    issues.append([cline.index, line, "subregion without incorrect numbering"])
                sub_start = cline
                skip_count = 0
                skip_time = 0
                extra_count = 0
                extra_time = 0
                makeup_count = 0
                makeup_time = 0
                silence_time = 0
                results[m[0]] = []
                continue
            if "ends" in line:
                if m[0] not in results:
                    issues.append([cline.index, line, "subregion without begin"])
                    continue
                results[m[0]] = [skip_count, skip_time, extra_count, extra_time, makeup_count, makeup_time, silence_time]
                sub_start = None
                skip_count = None
                skip_time = None
                extra_count = None
                extra_time = None
                makeup_count = None
                makeup_time = None
                silence_time = None
        if "extra" in line:
            if extra_count is None:
                if "begin" in line:
                    issues.append([cline.index, line, "extra region begins outside subregion"])
                    continue
                if "end" in line:
                    issues.append([cline.index, line, "extra region ends outside subregion"])
                    continue
                issues.append([cline.index, line, "extra region outside subregion"])
                continue
            if "begin" in line:
                if extra_start is not None:
                    issues.append([extra_start.index, extra_start.line, "extra region without end"])
                extra_start = cline
                continue
            if "end" in line:
                if extra_start is None:
                    issues.append([cline.index, cline.line, "extra region without begin"])
                    continue
                extra_count += 1
                extra_time += cline.offset - extra_start.offset
                extra_start = None
                continue
        if "make up" in line or "make-up" in line or "makeup" in line:
            if makeup_count is None:
                if "begin" in line:
                    issues.append([cline.index, line, "makeup region begins outside subregion"])
                    continue
                if "end" in line:
                    issues.append([cline.index, line, "makeup region ends outside subregion"])
                    continue
                issues.append([cline.index, line, "makeup region outside subregion"])
                continue
            if "begin" in line:
                if makeup_start is not None:
                    issues.append([makeup_start.index, makeup_start.line, "makeup region without end"])
                makeup_start = cline
                continue
            if "end" in line:
                if makeup_start is None:
                    issues.append([cline.index, cline.line, "makeup region without begin"])
                    continue
                makeup_count += 1
                makeup_time += cline.offset - makeup_start.offset
                makeup_start = None
                continue
        if "skip" in line:
            if skip_count is None:
                if "begin" in line:
                    issues.append([cline.index, line, "skip region begins outside subregion"])
                    continue
                if "end" in line:
                    issues.append([cline.index, line, "skip region ends outside subregion"])
                    continue
                issues.append([cline.index, line, "skip region outside subregion"])
                continue
            if "begin" in line:
                if skip_start is not None:
                    issues.append([skip_start.index, skip_start.line, "skip region without end"])
                skip_start = cline
                continue
            if "end" in line:
                if skip_start is None:
                    issues.append([cline.index, cline.line, "skip region without begin"])
                    continue
                skip_count += 1
                skip_time += cline.offset - skip_start.offset
                skip_start = None
                continue
        if "silence" in line:
            if silence_time is None:
                if "start" in line:
                    issues.append([cline.index, line, "silence region starts outside subregion"])
                    continue
                if "end" in line:
                    issues.append([cline.index, line, "silence region ends outside subregion"])
                    continue
                issues.append([cline.index, line, "silence region outside subregion"])
                continue
            if "start" in line:
                if silence_start is not None:
                    issues.append([silence_start.index, silence_start.line, "silence region without end"])
                silence_start = cline
                continue
            if "end" in line:
                if silence_start is None:
                    issues.append([cline.index, cline.line, "silence region without begin"])
                    continue
                silence_time += cline.offset - silence_start.offset
                silence_start = None
                continue

    return issues, results


# def process_file(path):
#     results = {}
#     sub_count = 0
#     skip_count = 0
#     skip_time = 0
#     extra_count = 0
#     extra_time = 0
#     makeup_count = 0
#     makeup_time = 0
#     silence_time = 0
#     silence_start = None
#     skip_start = None
#     makeup_start = None
#
#     cf = pc.ClanFile(path)
#     pfx = cf.filename[:5]
#     # get all comments that contain subregion and sort by offset
#     subrs = filter(lambda x: any(keyword in x.line for keyword in keyword_list]), cf.get_user_comments())
#     subrs.sort(key=lambda x: x.offset)
#     # subregion lines should be in pairs
#     if len(subrs) % 2 != 0:
#         raise Exception
#
#     for x in subrs:
#         if "subregion" in x:
#             m = subr_regx.findall(x.line)
#             # each subregion line should only have one regex match
#             if len(m) > 1:
#                 raise Exception
#             m=m[0]
#             # each subregion index should have two subregion lines,
#             # and the smaller offset of the lines should be the onset of subregion,
#             # larger offset of the lines be the offset
#             if m[0] not in results:
#                 results[m[0]] = []
#                 continue
#             else:
#                 results[m[0]].extend([skip_count, skip_time, extra_count, extra_time, makeup_count, makeup_time, silence_time])
#                 sub_count += 1
#                 continue
#         if "silence" in x:
#             if silence_start = None:
#                 silence_start = x.offset
#                 continue
#             silence_time += x.offset - silence_start
#             silence_start = None
#             continue
#         if "skip" in x:
#             if skip_start = None:
#                 skip_start = x.offset
#                 continue
#             skip_time += x.offset - skip_start
#             skip_start = None
#             skip_count += 1
#             continue
#         if "make-up region" in x:
#             if makeup_start = None:
#                 makeup_start = x.offset
#                 continue
#             makeup_time += x.offset - makeup_start
#             makeup_start = None
#             makeup_count += 1
#             continue
#
#     # filename, subregion index, onset, offset
#     results = [[pfx, sub_count, int(key), val[0], val[1]] for key, val in results.items()]
#     return results


if __name__ == "__main__":
    cha_dir = sys.argv[1]
    files = sorted([os.path.join(cha_dir, x) for x in os.listdir(cha_dir) if x.endswith(".cha")])
    #files = ['../all_cha/03_12_sparse_code.cha']
    regions = []
    issues = []
    for file in files:
        print("Checking {}".format(os.path.basename(file)))
        issues_file, results = pull_regions(file)
        file_regions = [[os.path.basename(file), len(results), "subregion {} of {}".format(sub[0], sub[1])]+results[sub] for sub in results.keys()]
        issues_file = [[os.path.basename(file)]+iss for iss in issues_file]
        regions.extend(file_regions)
        issues.extend(issues_file)
        print("Finished {}".format(os.path.basename(file)))

    df = pd.DataFrame(regions, columns=['file', 'subregion_count', 'current_subregion', 'skip_count', 'skip_time', 'extra_count', 'extra_time', 'makeup_count', 'makeup_time', 'silence_time'])
    df_issue = pd.DataFrame(issues, columns=['file', 'line_index', 'line', 'issue'])
    df.to_csv("recap_regions.csv", index=False)
    df_issue.to_csv("regions_issue.csv", index=False)
