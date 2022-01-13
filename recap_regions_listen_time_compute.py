import argparse
import csv
import io
import os.path
import signal
import sys
from multiprocessing import Pool, Manager

import pyclan

from check_errors import sequence_missing_repetition_entry_alert
from funcs import pull_regions, bcolors, sort_list_of_region_boundaries
from listen_time import total_listen_time
from settings import FIELD_NAMES, default_cha_structures_folder


def get_args():
    parser = argparse.ArgumentParser(description='Compute listened time for the corpus.')
    parser.add_argument('input_file',
                        help='Either a path file containing a path for each cha file, one path per line, OR, a single cha file.')
    parser.add_argument('--output_path', help='Optional output directory to output the reports/csvs/etc.',
                        default='output')
    parser.add_argument("--fast", action="store_true", help='Parallelize processing using up to 6 corse')
    return parser.parse_args()


def process_single_file(clan_file_path, output_folder=default_cha_structures_folder):

    print("Checking {}".format(os.path.basename(clan_file_path)))

    # Parse the clan file
    try:
        clan_file = pyclan.ClanFile(clan_file_path)
    except Exception as e:
        print(bcolors.FAIL + "Error opening file: {}".format(clan_file_path) + bcolors.ENDC)
        print(sys.exc_info())
        return

    # Extract sequence of all starts/ends of all regions and subregion positions and ranks
    region_boundaries, subregions = pull_regions(clan_file=clan_file)

    # Sort that sequence by timestamp and - in case of collisions - by region rank
    region_boundaries = sort_list_of_region_boundaries(region_boundaries)

    # Check for errors
    error_list, region_map = sequence_missing_repetition_entry_alert(region_boundaries)
    if error_list:
        print(
            bcolors.WARNING + "Finished {0} with errors! Listen time cannot be calculated due to missing starts or ends!\nCheck the {0}.txt file for errors!".format(
                os.path.basename(clan_file_path)) + bcolors.ENDC)
        file_with_error.append((os.path.basename(clan_file_path), error_list))

    # Write results to a text file
    with open(os.path.join(output_folder, os.path.basename(clan_file_path) + '.txt'), 'w') as f:
        # Write the region boundaries
        f.write('\n'.join([region_type_and_side + '   ' + str(timestamp)
                           for region_type_and_side, timestamp in region_boundaries]))
        f.write('\n' * 3)

        # Write the list of errors
        f.write('\n'.join(error_list))

        # Write subregion information
        f.write('\n')
        f.write('\n'.join(subregions))

    # Calculate listen time

    # If the file with error has a missing start or end error, we cannot correctly process it! So return!
    for subregion in error_list:
        if 'missing' in subregion:
            return

    try:
        # Checking if the file is a 6 or 7 month old to set the month67 parameter of the function
        month67 = os.path.basename(clan_file_path)[3:5] in ['06', '07']
        listen_time = total_listen_time(clan_file, region_map, subregions, month67=month67)
    except:
        return

    # listen_time is dict returned by total_listen_time function in listen_time.py
    listen_time['filename'] = os.path.basename(clan_file_path)

    # Setting the subregions of the listen_time dictionary.
    positions = []
    ranks = []
    for subregion in subregions:
        # subregion is a string like 'Position: 4, Rank: 4'
        position_string, rank_string = subregion.split(',')
        position = position_string.split()[1]
        rank = rank_string.split()[1]
        positions.append(position)
        ranks.append(rank)

    listen_time['subregions'] = subregions
    listen_time['ranks'] = ranks
    listen_time['positions'] = positions
    listen_time_summary.append(listen_time)
    print("Finished {}".format(os.path.basename(clan_file_path)) + '\nTotal Listen Time: ' + bcolors.OKGREEN + str(
        listen_time['total_listen_time_hour']) + bcolors.ENDC)
    print(subregions)


def output_aggregated_results(file_with_error, listen_time_summary, output_path):
    with open(os.path.join(output_path, 'Error_Summary.txt'), 'w') as f:
        for entry in file_with_error:
            f.write(entry[0]+'\n')
            for error in entry[1]:
                f.write('\t\t\t\t'+error+'\n')
            f.write('\n')

    # Writing to the total listen time summary file
    with open(os.path.join(output_path, 'Total_Listen_Time_Summary.csv'), 'wb') as binary_file:
        # I am not sure why binary mode was used above but it won't work with Python 3 csv module which wants to write
        # strings, not bytes. Just in case it was necessary to write to a binary file, we'll just wrap the binary file
        # an a virtual text file object.
        with io.TextIOWrapper(binary_file, encoding='utf-8', newline='') as virtual_text_file:
            writer = csv.DictWriter(virtual_text_file, fieldnames=FIELD_NAMES)
            writer.writeheader()
            listen_time_summary = list(listen_time_summary)
            listen_time_summary.sort(key=lambda k: k['filename'])
            writer.writerows(listen_time_summary)


if __name__ == "__main__":
    args = get_args()

    if os.path.splitext(args.input_file)[-1] == '.cha':
        listen_time_summary = []
        file_with_error = []
        process_single_file(args.input_file)

    else:

        path_file = args.input_file
        clan_file_paths = []
        with open(path_file) as f:
            for path in f.readlines():
                path = path.strip()
                clan_file_paths.append(path)
        print("Expected to process {} cha files".format(len(clan_file_paths)))
        # Create output folder if it does not exist
        try:
            output_path = sys.argv[2]
            if output_path.startswith('--'):
                output_path = 'output'
        except IndexError:
            output_path = 'output'

        if not os.path.isdir(output_path):
            os.mkdir(output_path)

        if not os.path.isdir(os.path.join(output_path, 'cha_structures')):
            os.mkdir(os.path.join(output_path, 'cha_structures'))

        cha_structure_path = os.path.join(output_path, 'cha_structures')

        if '--fast' in sys.argv:
            global manager
            manager = Manager()
            file_with_error = manager.list()
            listen_time_summary = manager.list()
            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            p = Pool(6)
            signal.signal(signal.SIGINT, original_sigint_handler)
            try:
                res = p.map(process_single_file, clan_file_paths)
            except KeyboardInterrupt:
                print("Caught KeyboardInterrupt, terminating workers")
                p.terminate()
            else:
                print("Normal termination")
                p.close()
            p.join()

        else:
            file_with_error = []
            listen_time_summary = []

            for clan_file_path in clan_file_paths:
                try:
                    process_single_file(clan_file_path, cha_structure_path)
                except Exception as e:
                    print(e)
                    continue

    # We output the findings.
    output_aggregated_results(file_with_error, listen_time_summary, args.output_path)
