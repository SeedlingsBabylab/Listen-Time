import os
import sys
import csv

var_list = [
        'filename',
        'region_type',
        'start_time',
        'stop_time'
        ]

region_types = [
        'subregion',
        'silence',
        'skip',
        'extra',
        'surplus',
        'makeup'
        ]

        
def process_line(line, f_dict):
    if 'starts' in line or 'ends' in line:
        llist = line.split()
        rtype = llist[0]
        start_stop = llist[1]
        tstamp = llist[2]
        f_dict[rtype][start_stop].append(tstamp)

def flatten(f_dict, filename):
    out_list = []
    for l in f_dict:
        for i, v in enumerate(f_dict[l]['starts']):
            temp_dict = {}
            temp_dict['filename'] = filename[:-4]
            temp_dict['region_type'] = l
            temp_dict['start_time'] = v
            temp_dict['stop_time'] = f_dict[l]['ends'][i]
            out_list.append(temp_dict)
    return out_list




if __name__ == '__main__':
    # The first command line argument is the directory that contains cha structure files.
    with open(os.path.join('output', 'timeline_data.csv'), 'w') as csvfile:
        
        # create a Dictwriter object that will write rows by taking dictionaries and mapping
        # them to variables, according to the fieldnames argument.
        writer = csv.DictWriter(csvfile, fieldnames=var_list)
        writer.writeheader()

        for f in os.listdir(sys.argv[1]):

            #process each cha structure file
            with open(os.path.join(sys.argv[1], f)) as cha_struct:
                f_dict = {r: {'starts': [], 'ends': []} for r in region_types}
                # traverse the cha structure file line by line
                print(f)
                #print f_dict
                for line in cha_struct:
                    process_line(line, f_dict)

                writer.writerows(flatten(f_dict, f))
                
                #print f_dict
                print('\n\n\n')

                




