import pyclan as pc
import os.path
from settings import *
import csv

# '''
# Step 1:
#     Parse file by pyclan and extract comments from the file.
#     Go through each comment, if it marks the beginning or ending of the regions,
#     mark it down to a list of tuples that looks like:
#     [(subregion starts, timestamp),  (silence starts, timestamp), (silence ends, timestamp)....]
# '''


def pull_regions(path):
    cf = pc.ClanFile(path)

    subregions = []

    comments = cf.get_user_comments()
    comments.sort(key = lambda x: x.offset)

    sequence = []
    for cline in comments:
        line = cline.line

        # Pulling subregion information from the line. 

        if 'subregion' in line:
            sub_pos = "N/A"
            sub_rank = "N/A"
            try:
                sub_pos = subr_regx.search(line).group(1)
                sub_rank = rank_regx.search(line).group(1)
            except AttributeError:
                print(bcolors.FAIL + 'Subregion time does not exist/is not correct' + bcolors.ENDC)
                print(bcolors.FAIL + path + bcolors.ENDC)

            offset = subr_time_regx.findall(line)
            try:
                offset = int(offset[0])
            except:
                print(bcolors.FAIL + 'Unable to grab time' + bcolors.ENDC)
            if 'starts' in line:
                sequence.append(('subregion starts', offset))
            # Only adding after ends in order to not add the position and rank info twice to the subregions list. 
            elif 'ends' in line:
                sequence.append(('subregion ends', offset))
                subregions.append('Position: {}, Rank: {}'.format(sub_pos, sub_rank))
        elif 'extra' in line:
            if 'begin' in line:
                sequence.append(('extra starts', cline.offset))
            elif 'end' in line:
                sequence.append(('extra ends', cline.offset))
        elif 'silence' in line:
            if 'start' in line:
                sequence.append(('silence starts', cline.offset))
            elif 'end' in line:
                sequence.append(('silence ends', cline.offset))
        elif 'skip' in line:
            if 'begin' in line:
                sequence.append(('skip starts', cline.offset))
            elif 'end' in line:
                sequence.append(('skip ends', cline.offset))
        elif 'makeup' in line or 'make-up' in line or 'make up' in line:
            if 'begin' in line:
                sequence.append(('makeup starts', cline.offset))
            elif 'end' in line:
                sequence.append(('makeup ends', cline.offset))
        elif 'surplus' in line:
            if 'begin' in line:
                sequence.append(('surplus starts', cline.offset))
            elif 'end' in line:
                sequence.append(('surplus ends', cline.offset))
        # if len(sequence)>1 and sequence[-2][1]==cline.offset:
        #     print(bcolors.WARNING + "Special case" + bcolors.ENDC)
    print(subregions)
    return sequence, cf, subregions

def ms2hr(ms):
    return round(ms / 3600000.0, PRECISION)

def output(file_with_error, listen_time_summary, output_path):
    with open(os.path.join(output_path, 'Error_Summary.txt'), 'w') as f:
        for entry in file_with_error:
            f.write(entry[0]+'\n')
            for error in entry[1]:
                f.write('\t\t\t\t'+error+'\n')
            f.write('\n')

    # Writing to the total listen time summary file
    with open(os.path.join(output_path, 'Total_Listen_Time_Summary.csv'), 'wb') as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        writer.writeheader()
        listen_time_summary = list(listen_time_summary)
        listen_time_summary.sort(key = lambda k: k['filename'])
        writer.writerows(listen_time_summary)

# '''
# Step 2:
#     Sort the output, a list of tuples, from the pull_regions function.
#     The sorting has two keys, primary key is the timestamp, ascending
#     secondary sorting key is rank specified in keyword rank.
#     The purpose of the secondary key is to ensure that when two entries
#     have the same timestamp, certain sorting order is still maintained.
# '''
def sequence_minimal_error_sorting(sequence):
    sequence = sorted(sequence, key=lambda k: (k[1], starts_ends[k[0].split()[1]], keyword_rank[k[0]]))
    return sequence


