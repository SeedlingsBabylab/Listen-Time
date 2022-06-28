import pyclan as pc
import csv
import re
import sys
import os.path
import pandas as pd

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


subr_regx = re.compile(r'subregion (\d*) ?of (\d*)') # There are some cases where the numbering is missing
code_regx = re.compile(r'([a-zA-Z][a-z+]*)( +)(&=)([A-Za-z]{1})(_)([A-Za-z]{1})(_)([A-Z]{1}[A-Z0-9]{2})(_)?(0x[a-z0-9]{6})?', re.IGNORECASE | re.DOTALL) # Annotation regex
keyword_list = ["subregion", "silence", "skip", "makeup", "extra"]
keyword_rank = {"subregion": 1, "skip": 2, "silence": 3, "makeup": 4, "extra": 5}

FIELD_NAMES = [
        'filename',
        1,
        2,
        3,
        4,
        5,
        'total',
        'outside'
        ]
        

def pull_regions(path):
    cf = pc.ClanFile(path)

    comments = cf.get_user_comments()
    comments.sort(key = lambda x: x.offset)
    #print comments

    sequence = []
    for cline in comments:
        line = cline.line
        if 'subregion' in line:
            if 'starts' in line:
                sequence.append(('subregion starts', cline.offset))
            if 'ends' in line:
                sequence.append(('subregion ends', cline.offset))
        elif 'extra' in line:
            if 'begin' in line:
                sequence.append(('extra starts', cline.offset))
            if 'end' in line:
                sequence.append(('extra ends', cline.offset))
        elif 'silence' in line:
            if 'start' in line:
                sequence.append(('silence starts', cline.offset))
            if 'end' in line:
                sequence.append(('silence ends', cline.offset))
        elif 'skip' in line:
            if 'begin' in line:
                sequence.append(('skip starts', cline.offset))
            if 'end' in line:
                sequence.append(('skip ends', cline.offset))
        elif 'makeup' in line or 'make-up' in line or 'make up' in line:
            if 'begin' in line:
                sequence.append(('makeup starts', cline.offset))
            if 'end' in line:
                sequence.append(('makeup ends', cline.offset))
        # if len(sequence)>1 and sequence[-2][1]==cline.offset:
        #     print(bcolors.WARNING + "Special case" + bcolors.ENDC)
    return sequence, cf

def sequence_minimal_error_sorting(sequence):
    def swap(i, j, seq):
        k = seq[i]
        seq[i] = seq[j]
        seq[j] = k
    for i in range(len(sequence)-1):
        x1 = sequence[i]
        x2 = sequence[i+1]
        if x1[1]==x2[1]:
            if x1[0].split()[1]=='starts' and x2[0].split()[1]=='ends':
                swap(i, i+1, sequence)
            elif x1[0].split()[1]=='starts' and x2[0].split()[1]=='starts':
                if keyword_rank[x1[0].split()[0]] > keyword_rank[x2[0].split()[0]]:
                    swap(i, i+1, sequence)
            elif x1[0].split()[1]=='ends' and x2[0].split()[1]=='ends':
                if keyword_rank[x1[0].split()[0]] < keyword_rank[x2[0].split()[0]]:
                    swap(i, i+1, sequence)

def sequence_missing_repetition_entry_alert(sequence):
    region_map = {x:{'starts':[], 'ends': []} for x in keyword_list}
    error_list = []
    for entry in sequence:
        region_map[entry[0].split()[0]][entry[0].split()[1]].append(entry[1])
    for item in keyword_list:
        if len(set(region_map[item]['starts'])) < len(set(region_map[item]['ends'])):
            error_list.append(item + ' starts missing')
        elif len(set(region_map[item]['starts'])) > len(set(region_map[item]['ends'])):
            error_list.append(item + ' ends missing')
        if len(set(region_map[item]['ends'])) < len(region_map[item]['ends']):
            error_list.append(item + ' ends repetition')
        if len(set(region_map[item]['starts'])) < len(region_map[item]['starts']):
            error_list.append(item + ' starts repetition')
    return error_list, region_map

'''
    Sieve out annotations that do not belong to one of the following cases:
    1. Inside extra region
    2. Inside subregion
    3. Inside makeup region but not inside subregion
'''
def outside_annotation_check(cf, region_map):
    '''
        TODO:
        Assumption: if a subregion has nested makeup region, that means there should not be any other annotations outside the nested makeup region
                    but inside the subregion (i.e. the subregion could be discounted)

        This assumption needs to be verified
    '''
    counts = {'extra', 'makeup', 'subregion', 'subregion_raw'}
    counts_by_region = {i: 0 for i in range(1, 6)}
    subregion_starts = list(region_map['subregion']['starts'])
    subregion_ends = list(region_map['subregion']['ends'])

    def remove_subregions_with_nested_makeup():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        makeup_start_times = region_map['makeup']['starts']
        makeup_end_times = region_map['makeup']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = False
            for j in range(len(makeup_start_times)):
                if subregion_start_times[i]<=makeup_start_times[j] and subregion_end_times[i]>=makeup_end_times[j]:
                    remove = True
                    break
            if remove:
                del subregion_start_times[i]
                del subregion_end_times[i]

    def is_inside_extra_region(offset):
        for i in range(len(region_map['extra']['starts'])):
            if offset>=region_map['extra']['starts'][i] and offset<=region_map['extra']['ends'][i]:
                return True
        return False
    
    def is_inside_makeup_region(offset):
        for i in range(len(region_map['makeup']['starts'])):
            if offset>=region_map['makeup']['starts'][i] and offset<=region_map['makeup']['ends'][i]:
                return True
        return False

    def is_inside_subregion(offset):
        for i in range(len(region_map['subregion']['starts'])):
            if offset>=region_map['subregion']['starts'][i] and offset<=region_map['subregion']['ends'][i]:
                return True
        return False

    def logical_or(offset, functions):
        for f in functions:
            if f(offset):
                return True
        return False

    def is_inside_unremoved_subregion(offset):
        for i in range(len(subregion_starts)):
            if offset>=subregion_starts[i] and offset<=subregion_ends[i]:
                return i + 1
        return 0

    remove_subregions_with_nested_makeup()
    annotations = cf.annotations()
    conditions = [is_inside_extra_region, is_inside_makeup_region, is_inside_subregion]
    outside_annots = []
    j = 0
    for annot in annotations:
        # cond is True (more precisely a positive subregion position) if an annotation is inside an unremoved subregion
        cond = is_inside_unremoved_subregion(annot.offset)
        if not logical_or(annot.offset, conditions):
            outside_annots.append(annot)
        elif cond:
            counts_by_region[cond] += 1
            
    
    return outside_annots
            

if __name__ == "__main__":
    path_file = sys.argv[1]
    with open(path_file) as pf:
        files = [l.strip() for l in pf.readlines()]
    #files = ['../all_cha/15_14_sparse_code.cha']
    file_with_error = []
    outside_annotations_f = open('../output/outside_annots.txt', 'w')
    counts_sum = []
    for file in files:
        print("Checking {}".format(os.path.basename(file)))
        sequence, cf = pull_regions(file)
        sequence_minimal_error_sorting(sequence)
        error_list, region_map = sequence_missing_repetition_entry_alert(sequence)
        with open('../output/structures/'+os.path.basename(file)+'.txt', 'w') as f:
            f.write('\n'.join([x[0] + '   ' + str(x[1]) for x in sequence]))
            f.write('\n')
            f.write('\n')
            f.write('\n')
            f.write('\n'.join(error_list))
        if error_list:
            print(bcolors.WARNING + "Finished {}".format(os.path.basename(file)) + bcolors.ENDC)
            file_with_error.append((os.path.basename(file), error_list))
        else:
            # Outside annots.txt file is outputted here.
            outside_annots, counts_by_region, total = outside_annotation_check(cf, region_map)
            counts_by_region['outside'] = len(outside_annots)
            counts_by_region['total'] = total
            counts_by_region['filename'] = os.path.basename(file)
            counts_sum.append(counts_by_region)
            # Check if file is month 8-17
            if outside_annots and int(os.path.basename(file)[3:5])>=8:
                outside_annotations_f.write(os.path.basename(file)+'\n')
                outside_annotations_f.write('Total: {}'.format(total))
                for annot in outside_annots:
                    outside_annotations_f.write('\t\t\t\t' + annot.__repr__() + '\t\t' + str(annot.offset)+'\n')
                outside_annotations_f.write('\n')
            print("Finished {}".format(os.path.basename(file)))
    outside_annotations_f.close()
    with open('../output/counts_by_region.csv', 'wb') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(counts_sum)
        
    with open('../output/summary.txt', 'w') as f:
        for entry in file_with_error:
            f.write(entry[0]+'\n')
            for error in entry[1]:
                f.write('\t\t\t\t'+error+'\n')
            f.write('\n')
