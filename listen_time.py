from funcs import ms2hr
from settings import *

# '''
# Step 4:
#     Compute the total listen time. Several transformations or filterings are done before computing the total listen time.
# '''
def total_listen_time(cf, region_map, subregions, month67 = False):
    counts = [0 for i in range(5)]
    # '''
    # Subruotine 1:
    #     Remove all the regions that are completely nested within the skip regions.
    #     If a region is partially overlap with a skip region, remove only the overlapping portion by adjusting the boundary of the region.
    # '''
    def remove_regions_nested_in_skip():
        skip_start_times = region_map['skip']['starts']
        skip_end_times = region_map['skip']['ends']
        assert(len(skip_start_times)==len(skip_end_times))
        for region_type in ['makeup', 'silence', 'subregion', 'extra']:
            region_start_times = region_map[region_type]['starts']
            region_end_times = region_map[region_type]['ends']
            assert(len(region_start_times)==len(region_end_times))
            for i in range(len(skip_start_times)):
                for j in range(len(region_start_times)-1, -1, -1):
                    if skip_start_times[i]<=region_start_times[j] and skip_end_times[i]>=region_end_times[j]:
                        print('Remove!')
                        print("Nested in skip!")
                        print("removed {} {} {}".format(region_type, region_start_times[j], region_end_times[j]))
                        del region_end_times[j]
                        del region_start_times[j]
                        if region_type == 'subregion':
                            #del subregions[j]
                            print('')
                    elif skip_start_times[i]<=region_start_times[j] and skip_end_times[i]<=region_end_times[j] and skip_end_times[i] >= region_start_times[j]:
                        skip_start_times[i] = region_start_times[j]
                    elif skip_start_times[i]>=region_start_times[j] and skip_end_times[i]>=region_end_times[j] and skip_start_times[i] <= region_end_times[j]:
                        skip_end_times[i] = region_end_times[j]
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
    def remove_subregions_with_nested_makeup():
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
        #print(subregion_start_times)

    # '''
    # Subroutine 3:
    #     Remove all subregions that does not have any annotations. Those regions should be ignored since they do not consists
    #     of any listened content.
    # '''
    def remove_subregions_without_annotations():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = True
            lines = cf.get_within_time(begin=subregion_start_times[i], end=subregion_end_times[i]).line_map
            # Hacky way to count the number of annotations in the subregion.
            count = 0
            for line in lines:
                annot = code_regx.findall(line.line)
                if annot:
                    remove = False
                    count += 1
            print(count)
            counts[i] = count
            if remove:
                print('Remove!')
                print("no annot", subregion_start_times[i])
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
                del subregion[i]
        #print(subregion_start_times)

    # '''
    # Subroutine 5:
    #     If a silent region partially overlaps with a subregion, remove the NON-OVERLAPPING portion of that silent region (since we don't subtract that part in our calculation.
    #     Otherwise, if the silent region does not overlap with the subregion at all, completely remove it! 
    # '''
    def remove_silence_regions_outside_subregions():
        silence_start_times = region_map['silence']['starts']
        silence_end_times = region_map['silence']['ends']
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        i = len(silence_start_times) - 1
        while i>=0:
            remove = True
            for j in range(len(subregion_start_times)):
                # If the silent region i start time is between start and end of subregion j
                if silence_start_times[i]>=subregion_start_times[j] and silence_start_times[i]<=subregion_end_times[j]:
                    # If there is not a complete nesting of the silent region within the subregion! 
                    if silence_end_times[i]>subregion_end_times[j]:
                        silence_end_times.append(silence_end_times[i])
                        silence_start_times.append(subregion_end_times[j]+1)
                        silence_end_times[i] = subregion_end_times[j]
                        i += 2
                        silence_start_times.sort()
                        silence_end_times.sort()
                    remove = False
                    break
                if silence_end_times[i]>=subregion_start_times[j] and silence_end_times[i]<=subregion_end_times[j]:
                    silence_start_times[i] = max(subregion_start_times[j], silence_start_times[i])
                    remove = False
                    break
            if remove:
                del silence_start_times[i]
                del silence_end_times[i]
            i -= 1

    def remove_subregions_with_surplus():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        surplus_start_times = region_map['surplus']['starts']
        surplus_end_times = region_map['surplus']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            remove = False
            for j in range(len(surplus_start_times)):
                # If surplus start or end is inside the subregion (e.g. there is any kind of overlap)
                if (subregion_start_times[i]<=surplus_start_times[j] and subregion_end_times[i]>=surplus_start_times[j]) \
                or (subregion_start_times[i]<=surplus_end_times[j] and subregion_end_times[i]>=surplus_end_times[j]):
                    remove = True
                    break
            if remove:
                print('Remove')
                print("overlap surplus ",subregion_start_times[i], subregion_end_times[i])
                del subregion_start_times[i]
                del subregion_end_times[i]
                #del subregions[i]

    def skip_silence_overlap_time():
        ''' This is only used for month 6 and 7.
            The total time where skip and silence regions overlap are computed so as to be subtracted from silence time computed later.
        '''
    # Only used for month 6 and 7

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

    def annotated_subregion_time():
        start_times = region_map['subregion']['starts']
        end_times = region_map['subregion']['ends']
        total_time = 0
        num_subregion_with_annot = 0
        for i in range(len(start_times)):
            num_subregion_with_annot += 1
            total_time += end_times[i] - start_times[i] # +1?
        return total_time, num_subregion_with_annot

    # I have those functions all separated in case we need to make modifications to the way we compute listen time for each region
    def skip_region_time():
        start_times = region_map['skip']['starts']
        end_times = region_map['skip']['ends']
        total_time = 0
        for i in range(len(start_times)):
            total_time += end_times[i] - start_times[i]
        return total_time

    def silence_region_time():
        start_times = region_map['silence']['starts']
        end_times = region_map['silence']['ends']
        total_time = 0
        for i in range(len(start_times)):
            total_time += end_times[i] - start_times[i]
        return total_time

    def extra_region_time():
        start_times = region_map['extra']['starts']
        end_times = region_map['extra']['ends']
        total_time = 0
        for i in range(len(start_times)):
            total_time += end_times[i] - start_times[i]
        return total_time, len(start_times)

    def makeup_region_time():
        start_times = region_map['makeup']['starts']
        end_times = region_map['makeup']['ends']
        total_time = 0
        for i in range(len(start_times)):
            total_time += end_times[i] - start_times[i]
        return total_time, len(start_times)

    def surplus_region_time():
        start_times = region_map['surplus']['starts']
        end_times = region_map['surplus']['ends']
        total_time = 0
        for i in range(len(start_times)):
            total_time += end_times[i] - start_times[i]
        return total_time, len(start_times)

    def count_sr_annotations():
        subregion_start_times = region_map['subregion']['starts']
        subregion_end_times = region_map['subregion']['ends']
        for i in range(len(subregion_start_times)-1, -1, -1):
            lines = cf.get_within_time(begin=subregion_start_times[i], end=subregion_end_times[i]).line_map
            # Hacky way to count the number of annotations in the subregion.
            count = 0
            for line in lines:
                annot = code_regx.findall(line.line)
                if annot:
                    count += 1
            counts[i] = count
            
    result = {}


    # Here we add the raw totals for skip and subregion to the result dictionary. By raw, we mean that the preprocessing steps below are not done. These items are for diagnostic purposes. 

    result['silence_raw_hour'] = ms2hr(silence_region_time())
    shour, snum = annotated_subregion_time()
    result['num_raw_subregion'], result['subregion_raw_hour'] = snum, ms2hr(shour)

    if not month67:
        # Preprocessing
        remove_subregions_with_surplus()
        remove_regions_nested_in_skip()
        remove_subregions_with_nested_makeup()
        remove_subregions_without_annotations()
        remove_subregions_nested_in_silence_regions()
        remove_silence_regions_outside_subregions()
        result['skip_silence_overlap_hour'] = 0
                      
    else:
        # Preprocessing
        skip_silence_time = skip_silence_overlap_time()
        skip_time = skip_region_time()
        silence_time = silence_region_time()
        result['skip_silence_overlap_hour'] = ms2hr(skip_silence_time)
        
    subregion_time, num_subregion_with_annot = annotated_subregion_time()
    result['subregion_time'] = subregion_time
    result['num_subregion_with_annot'] = num_subregion_with_annot
    result['subregion_time_hour'] = ms2hr(subregion_time)

    skip_time = skip_region_time()
    result['skip_time'] = skip_time
    result['skip_time_hour'] = ms2hr(skip_time)

    silence_time = silence_region_time()
    result['silence_time'] = silence_time
    result['silence_time_hour'] = ms2hr(silence_time)

    extra_time, num_extra_region = extra_region_time()
    result['extra_time'] = extra_time
    result['num_extra_region'] = num_extra_region     
    result['extra_time_hour'] = ms2hr(extra_time)

    makeup_time, num_makeup_region = makeup_region_time()
    result['makeup_time'] = makeup_time
    result['num_makeup_region'] = num_makeup_region          
    result['makeup_time_hour'] = ms2hr(makeup_time)

    surplus_time, num_surplus_region = surplus_region_time()
    result['surplus_time'] = surplus_time
    result['num_surplus_region'] = num_surplus_region
    result['surplus_time_hour'] = ms2hr(surplus_time)

    result['counts'] = counts

    print(subregion_time, skip_time, silence_time)


    # If the file is not a 6 or 7 month file, we add/subtract regions to get total time.
    if not month67:
        total_time = subregion_time + extra_time + makeup_time + surplus_time - silence_time - skip_time

    # Otherwise, we assume that the entire file was listened to, so we do not touch anything. 
    else:
        total_time = cf.line_map[-1].offset - (skip_time + silence_time - skip_silence_time)
        print('{} - ({} + {} - {}) == {}'.format(cf.line_map[-1].offset, skip_time, silence_time, skip_silence_time, total_time))
        print(cf.line_map[-1].offset - (skip_time + silence_time - skip_silence_time) == total_time)
        
    result['total_listen_time'] = total_time

    result['end_time_hour'] = ms2hr(cf.line_map[-1].offset)

    result['total_listen_time_hour'] = ms2hr(total_time)
    return result


