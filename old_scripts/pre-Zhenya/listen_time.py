import re
from functools import partial
from copy import deepcopy

import pyclan

from funcs import ms2hr
from settings import REGION_TYPES

ANNOTATION_REGEX = re.compile(
    r'([a-zA-Z][a-z+]*)( +)(&=)([A-Za-z]{1})(_)([A-Za-z]{1})(_)([A-Z]{1}[A-Z0-9]{2})(_)?(0x[a-z0-9]{6})?',
    re.IGNORECASE | re.DOTALL)


def find_nested_skip(skip_regions, subregion_start, subregion_end):
    """

    :param skip_regions: a list of d
    :param subregion_start:
    :param subregion_end:
    :return: index of the first skip that is fully nested in the subregion
    """
    for i, item in enumerate(skip_regions):
        if item['starts'] >= subregion_start and item['ends'] <= subregion_end:
            return i


def get_overlap(a, b):
    """
    Returns the length of the overlap between intervals a and b
    :param a: pair of numbers, order not tested
    :param b: pair of numbers, order not tested
    :return: single number - length of the overlap
    """
    x1, x2 = a
    y1, y2 = b
    return max(0, min(x2, y2) - max(x1, y1))


def process_region_map(region_map, clan_file: pyclan.ClanFile):
    """
    Removes/modifies regions based on their overlap with other regions
    :param region_map: a dict of dicts with 'starts' and 'ends' lists
    :param clan_file: pased clan/cha file
    :return: modified region map, list of removal reasons for each subregion
    """
    region_map = deepcopy(region_map)
    # Sub positions is an array to keep track of which subregion is which after deletions.
    # It's my hacky way of figuring out the positions of subregions after removals, so I can correctly assign reasons
    # for removal.
    sub_positions = list(range(1, 6))
    removals = ['' for i in range(5)]

    # '''
    # Subroutine 1:
    #     Remove all the regions that are completely nested within the skip regions.
    # '''
    def remove_regions_except_surplus_nested_in_skip():
        skip_start_times = region_map['skip']['starts']
        skip_end_times = region_map['skip']['ends']
        assert len(skip_start_times) == len(skip_end_times)
        for region_type in ['makeup', 'silence', 'subregion', 'extra']:
            region_start_times = region_map[region_type]['starts']
            region_end_times = region_map[region_type]['ends']
            assert len(region_start_times) == len(region_end_times)
            for i in range(len(skip_start_times)):
                for j in range(len(region_start_times)-1, -1, -1):
                    if skip_start_times[i]<=region_start_times[j] and skip_end_times[i]>=region_end_times[j]:
                        print('Remove!')
                        print("Nested in skip!")
                        print("removed {} {} {}".format(region_type, region_start_times[j], region_end_times[j]))
                        del region_end_times[j]
                        del region_start_times[j]
                        if region_type == 'subregion':
                            update_sub_pos('Subregion removed for being nested in skip!', i)
                            print('')
    '''
        TODO:
        Assumption: if a subregion has nested makeup region, that means there should not be any other annotations outside the nested makeup region
                    but inside the subregion (i.e. the subregion could be discounted)

        This assumption needs to be verified
    '''
    # '''
    # Subroutine 2:
    #     Remove all the subregions that has a makeup region or surplus region inside. This is because only the makeup/surplus region listen time
    #     needs to be summed.
    # '''
    def remove_subregions_with_nested_makeup_or_surplus():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        makeup_start_times = region_map['makeup']['starts']
        makeup_end_times = region_map['makeup']['ends']
        surplus_start_times = region_map['surplus']['starts']
        surplus_end_times = region_map['surplus']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = False
            for j in range(len(makeup_start_times)):
                if subregion_start_times[i]<=makeup_start_times[j] and subregion_end_times[i]>=makeup_end_times[j]:
                    remove = True
                    break
            for j in range(len(surplus_start_times)):
                if subregion_start_times[i]<=surplus_start_times[j] and subregion_end_times[i]>=surplus_end_times[j]:
                    remove = True
                    break
            if remove:
                print('Remove!')
                print("nested makeup or surplus ",subregion_start_times[i], subregion_end_times[i])
                del subregion_start_times[i]
                del subregion_end_times[i]
                #del subregions[i]
                update_sub_pos('Subregion removed for having a nested makeup or surplus region', i)
        #print(subregion_start_times)

    # '''
    # Subroutine 3:
    #     Remove all subregions that does not have any annotations. Those regions should be ignored since they do not consists
    #     of any listened content.
    # '''
    def remove_subregions_without_annotations():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']

        skip_start_times = region_map['skip']['starts']
        skip_end_times = region_map['skip']['ends']

        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = True
            lines = clan_file.get_within_time(begin=subregion_start_times[i], end=subregion_end_times[i]).line_map
            for line in lines:
                annot = ANNOTATION_REGEX.findall(line.line)
                if annot:
                    remove = False
                    break
            if remove:
                skip_regions = [{'starts':_i, 'ends':_j} for _i, _j in zip(region_map['skip']['starts'], region_map['skip']['ends'])]
                subregion_start = subregion_start_times[i]
                subregion_end = subregion_end_times[i]
                find_nested_skip(skip_regions, subregion_start, subregion_end)
                print('Remove!')
                print("no annot in subregion # {}, starting at {}".format(sub_positions[i], subregion_start_times[i]))
                update_sub_pos('Subregion removed for not having any annotations', i)
                del subregion_start_times[i]
                del subregion_end_times[i]
                #del subregions[i]
        #print(subregion_start_times)

    # '''
    # Subroutine 4:
    #     Remove subregions that are completely nested in silent or surplus regions. Partial nesting does not count.
    # '''
    def remove_subregions_nested_in_silence_regions():
        silence_start_times = region_map['silence']['starts']
        silence_end_times = region_map['silence']['ends']
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        surplus_start_times = region_map['surplus']['starts']
        surplus_end_times = region_map['surplus']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = False
            for j in range(len(silence_start_times)):
                if subregion_start_times[i]>=silence_start_times[j] and subregion_end_times[i]<=silence_end_times[j]:
                    remove = True
                    break
            for j in range(len(surplus_start_times)):
                if subregion_start_times[i]>=surplus_start_times[j] and subregion_end_times[i]<=surplus_end_times[j]:
                    remove = True
                    break
            if remove:
                print('Remove')
                print("in silence or in surplus", subregion_start_times[i])
                del subregion_start_times[i]
                del subregion_end_times[i]
                update_sub_pos('Subregion removed for being nested inside a silent or surplus region.', i)
        #print(subregion_start_times)

    # '''
    # Subroutine 5:
    #     If a silent region partially overlaps with a subregion, remove the NON-OVERLAPPING portion of that silent region (since we don't subtract that part in our calculation.
    #     Otherwise, if the silent region does not overlap with the subregion at all, completely remove it!
    # '''
    def remove_parts_outside_good_regions(region_type):
        region_start_times = region_map[region_type]['starts']
        region_end_times = region_map[region_type]['ends']
        # Surplus is not one of the good region types in this context because we won't count it toward the total time in
        # the end, so we don't need to keep the silence that overlap with the surpluses.
        good_region_types = ['subregion', 'makeup', 'extra']
        # The good regions will not be modified so we can just copy their boundaries
        good_region_start_times = [start
                                   for good_region_type in good_region_types
                                   for start in region_map[good_region_type]['starts']]
        good_region_end_times = [end
                                 for good_region_type in good_region_types
                                 for end in region_map[good_region_type]['ends']]
        i = len(region_start_times) - 1
        while i >= 0:
            remove = True
            for j in range(len(good_region_start_times)):
                # If the silent region i start time is between start and end of subregion j
                if good_region_start_times[j] <= region_start_times[i] <= good_region_end_times[j]:
                    # If there is not a complete nesting of the silent region within the subregion!
                    if region_end_times[i] > good_region_end_times[j]:
                        region_end_times.append(region_end_times[i])
                        region_start_times.append(good_region_end_times[j]+1)
                        region_end_times[i] = good_region_end_times[j]
                        i += 2
                        region_start_times.sort()
                        region_end_times.sort()
                    remove = False
                    break
                if good_region_start_times[j] <= region_end_times[i] <= good_region_end_times[j]:
                    region_start_times[i] = max(good_region_start_times[j], region_start_times[i])
                    remove = False
                    break
            if remove:
                del region_start_times[i]
                del region_end_times[i]
            i -= 1

    def remove_subregions_overlapping_with_surplus():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        surplus_start_times = region_map['surplus']['starts']
        surplus_end_times = region_map['surplus']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = False
            for j in range(len(surplus_start_times)):
                # If surplus start or end is inside the subregion (e.g. there is any kind of overlap)
                sub = subregion_start_times[i], subregion_end_times[i]
                surp = surplus_start_times[j], surplus_end_times[j]
                if get_overlap(sub, surp):
                    remove = True
                    break
            if remove:
                print('Remove')
                print("overlap surplus ",subregion_start_times[i], subregion_end_times[i])
                del subregion_start_times[i]
                del subregion_end_times[i]
                update_sub_pos('Subregion removed for overlapping with surplus', i)
                #del subregions[i]

    def update_sub_pos(message, i):
        ind = sub_positions[i]
        removals[ind-1] = message
        print(removals)
        del sub_positions[i]

    remove_subregions_overlapping_with_surplus()
    remove_regions_except_surplus_nested_in_skip()
    remove_subregions_with_nested_makeup_or_surplus()
    remove_subregions_without_annotations()
    remove_subregions_nested_in_silence_regions()
    remove_parts_outside_good_regions('silence')
    remove_parts_outside_good_regions('skip')


    return region_map, removals


def count_annotations_within_subregion(region_map, clan_file):

    counts = [0 for i in range(5)]
    subregion_start_times = region_map['subregion']['starts']
    subregion_end_times = region_map['subregion']['ends']
    for i in range(len(subregion_start_times) - 1, -1, -1):
        lines = clan_file.get_within_time(begin=subregion_start_times[i], end=subregion_end_times[i]).line_map
        # Hacky way to count the number of annotations in the subregion.
        count = 0
        for line in lines:
            annot = ANNOTATION_REGEX.findall(line.line)
            if annot:
                count += 1
        counts[i] = count

    return counts


def get_total_time_and_count(region_map, region_type):
    assert region_type in REGION_TYPES
    start_times = region_map[region_type]['starts']
    end_times = region_map[region_type]['ends']
    total_time = 0
    for i in range(len(start_times)):
        total_time += end_times[i] - start_times[i]
    return total_time, len(start_times)


def skip_silence_overlap_time(region_map):
    """ This is only used for month 6 and 7.
        The total time where skip and silence regions overlap are computed so as to be subtracted from silence time
        computed later.
    """
    skip_start_times = region_map['skip']['starts']
    skip_end_times = region_map['skip']['ends']
    silence_start_times = region_map['silence']['starts']
    silence_end_times = region_map['silence']['ends']
    overlap_time = 0
    for i in range(len(skip_start_times)):
        for j in range(len(silence_start_times)):
            if skip_start_times[i]>=silence_start_times[j] and skip_start_times[i]<=silence_end_times[j]:
                overlap_time += min(silence_end_times[j], skip_end_times[i]) - skip_start_times[i]
            elif skip_end_times[i]>=silence_start_times[j] and skip_end_times[i]<=silence_end_times[j]:
                overlap_time += skip_end_times[i] - max(silence_start_times[j], skip_start_times[i])
    return overlap_time


def total_listen_time(clan_file: pyclan.ClanFile, region_map, month67=False):
    """
    Step 4:
        Compute the total listen time. Several transformations or filterings are done before computing the total listen
        time.
    """
    result = {}

    # Here we add the raw totals for skip and subregion to the result dictionary. By raw, we mean that the preprocessing
    # steps below are not done. These items are for diagnostic purposes.

    result['silence_raw_hour'] = ms2hr(get_total_time_and_count(region_map, 'silence')[0])
    shour, snum = get_total_time_and_count(region_map, 'subregion')
    result['num_raw_subregion'], result['subregion_raw_hour'] = snum, ms2hr(shour)

    result['annotation_counts_raw'] = count_annotations_within_subregion(region_map=region_map, clan_file=clan_file)

    if not month67:
        region_map, removals = process_region_map(region_map=region_map, clan_file=clan_file)
    else:
        removals = [''] * 5

    skip_silence_time = skip_silence_overlap_time(region_map)
    result['skip_silence_overlap_hour'] = ms2hr(skip_silence_time)
        
    subregion_time, num_subregion_with_annot = get_total_time_and_count(region_map, 'subregion')
    result['subregion_time'] = subregion_time
    result['num_subregion_with_annot'] = num_subregion_with_annot

    skip_time, _ = get_total_time_and_count(region_map, 'skip')
    result['skip_time'] = skip_time

    silence_time, _ = get_total_time_and_count(region_map, 'silence')
    result['silence_time'] = silence_time

    extra_time, num_extra_region = get_total_time_and_count(region_map, 'extra')
    result['extra_time'] = extra_time
    result['num_extra_region'] = num_extra_region

    makeup_time, num_makeup_region = get_total_time_and_count(region_map, 'makeup')
    result['makeup_time'] = makeup_time
    result['num_makeup_region'] = num_makeup_region

    surplus_time, num_surplus_region = get_total_time_and_count(region_map, 'surplus')
    result['surplus_time'] = surplus_time
    result['num_surplus_region'] = num_surplus_region

    result['removals'] = removals

    print(['{}: {}'.format(k, v) for k, v in result.items() if k.endswith('hour')])

    # If the file is not a 6 or 7 month file, we add/subtract regions to get total time.
    if not month67:
        total_time = (subregion_time + extra_time + makeup_time + surplus_time
                      - (skip_time + silence_time - skip_silence_time))

    # Otherwise, we assume that the entire file was listened to, so we do not touch anything. 
    else:
        total_time = clan_file.line_map[-1].offset - (skip_time + silence_time - skip_silence_time)
        print('{} - ({} + {} - {}) == {}'.format(clan_file.line_map[-1].offset, skip_time, silence_time,
                                                 skip_silence_time, total_time))
        print(clan_file.line_map[-1].offset - (skip_time + silence_time - skip_silence_time) == total_time)
        
    result['total_listen_time'] = total_time

    result['end_time'] = clan_file.line_map[-1].offset

    return result, region_map


