import io

import pyclan
import os.path
from settings import *
import csv


def _extract_subregion_info(clan_line: pyclan.ClanLine, clan_file_path: str):
    """
    Extracts subregion position, rank, offset from a comment line from a clan (cha) file. Returns "N/A" for attributes
    it couldn't extract.
    :param clan_line:
    :return: position, rank, offset
    """
    line = clan_line.line
    position = "N/A"
    rank = "N/A"
    try:
        position = subregion_regex.search(line).group(1)
        rank = subregion_rank_regex.search(line).group(1)
    except AttributeError:
        print(bcolors.FAIL + 'Subregion time does not exist/is not correct' + bcolors.ENDC)
        print(bcolors.FAIL + clan_file_path + bcolors.ENDC)

    offset = subregion_time_regex.findall(line)
    try:
        offset = int(offset[0])
    except:
        print(bcolors.FAIL + 'Unable to grab time' + bcolors.ENDC)

    return position, rank, offset


def pull_regions(clan_file: pyclan.ClanFile):
    """
    Step 1:
        Parse file by pyclan and extract comments from the file.
        Go through each comment, if it marks the beginning or ending of the regions,
        mark it down to a list of tuples that looks like:
        [(subregion starts, timestamp),  (silence starts, timestamp), (silence ends, timestamp)....]
    :param clan_file_path: path to the clan (cha) file as a string
    :return: (region_boundaries, clan_file, subregions)
        region_boundaries - list of tuples described above
        clan_file - pc.ClanFile object that parsed the input clan file
        subregions - list of strings of the format
    """

    # List of strings of the format 'Position: {}, Rank: {}'
    subregions = []

    comments = clan_file.get_user_comments()
    comments.sort(key=lambda x: x.offset)

    region_boundaries = []
    clan_line: pyclan.ClanLine
    for clan_line in comments:
        line = clan_line.line

        # Pulling subregion information from the line. 

        if 'subregion' in line:
            sub_pos, sub_rank, offset = _extract_subregion_info(clan_line=clan_line, clan_file_path=clan_file.clan_path)
            if 'starts' in line:
                region_boundaries.append(('subregion starts', offset))
            # Only adding after ends in order to not add the position and rank info twice to the subregions list. 
            elif 'ends' in line:
                region_boundaries.append(('subregion ends', offset))
                subregions.append('Position: {}, Rank: {}'.format(sub_pos, sub_rank))
        elif 'extra' in line:
            if 'begin' in line:
                region_boundaries.append(('extra starts', clan_line.offset))
            elif 'end' in line:
                region_boundaries.append(('extra ends', clan_line.offset))
        elif 'silence' in line:
            if 'start' in line:
                region_boundaries.append(('silence starts', clan_line.offset))
            elif 'end' in line:
                region_boundaries.append(('silence ends', clan_line.offset))
        elif 'skip' in line:
            if 'begin' in line:
                region_boundaries.append(('skip starts', clan_line.offset))
            elif 'end' in line:
                region_boundaries.append(('skip ends', clan_line.offset))
        elif 'makeup' in line or 'make-up' in line or 'make up' in line:
            if 'begin' in line:
                region_boundaries.append(('makeup starts', clan_line.offset))
            elif 'end' in line:
                region_boundaries.append(('makeup ends', clan_line.offset))
        elif 'surplus' in line:
            if 'begin' in line:
                region_boundaries.append(('surplus starts', clan_line.offset))
            elif 'end' in line:
                region_boundaries.append(('surplus ends', clan_line.offset))
        # if len(region_boundaries)>1 and region_boundaries[-2][1]==clan_line.offset:
        #     print(bcolors.WARNING + "Special case" + bcolors.ENDC)

    print(subregions)
    return region_boundaries, clan_file, subregions


def ms2hr(ms):
    return round(ms / 3600000.0, PRECISION)


def sort_list_of_region_boundaries(region_boundaries):
    """
    Step 2:
        Sort the output, a list of tuples, from the pull_regions function.
        The sorting has two keys, primary key is the timestamp, ascending
        secondary sorting key is rank specified in keyword rank.
        The purpose of the secondary key is to ensure that when two entries
        have the same timestamp, certain sorting order is still maintained.
    :param region_boundaries: list of ('<kind_of_region> <starts|ends>', <timestamp>) tuples
    :return:
    """
    region_boundaries = sorted(region_boundaries, key=lambda k: (k[1], starts_ends[k[0].split()[1]], region_sorting_rank[k[0]]))
    return region_boundaries


