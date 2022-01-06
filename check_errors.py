from settings import region_types


def sequence_missing_repetition_entry_alert(region_starts_and_ends):
    """
    Step 3:
        Basic error checking. It first builds the following map:
        region_map = {
            'subregion': {'starts': [list 1], 'ends': [list 2]},
            'silence': {'starts': [list 1], 'ends': [list 2]},
            ....
        }
        where list 1 and list 2 are the starting and ending timestamps for that particular type of region.
        The checking makes sure that both the beginning and end remarks are present for each region identified.
    """

    region_map = {x:{'starts':[], 'ends': []} for x in region_types}
    error_list = []
    for entry in region_starts_and_ends:
        region_map[entry[0].split()[0]][entry[0].split()[1]].append(entry[1])
    for item in region_types:
        if len(region_map[item]['starts']) == 0 and len(region_map[item]['ends']) == 0:
            continue
        # Checking for duplicate starts and ends. Length of set will be shorter if there are duplicates.
        if len(set(region_map[item]['ends'])) < len(region_map[item]['ends']):
            error_list.append(item + ' ends repetition')
        if len(set(region_map[item]['starts'])) < len(region_map[item]['starts']):
            error_list.append(item + ' starts repetition')
        start_list = sorted(set(region_map[item]['starts']))
        end_list = sorted(set(region_map[item]['ends']))
        i, j = 0, 0
        pe = 0

        # Added code to check for nesting of same type (skips within skips, fully or partially, which is not handled by default!)
        while i<len(start_list) and j<len(end_list):
            if start_list[i] < pe:
                print('Found a nesting! {0} end at {1} is nested between {0} start at {2} and {0} end at {3}'.format(item, pe, start_list[i], end_list[j]))
                print(item, pe)
                error_list.append('Found a nesting! {0} end at {1} is nested between {0} start at {2} and {0} end at {3}'.format(item, pe, start_list[i], end_list[j]))
            pe = end_list[j]
            if start_list[i]<=end_list[j]:
                i += 1
                j += 1
            else: # rstart_list[i]>end_list[j]: eversal, indicating that there is a missing start
                error_list.append(item + ' starts missing for end at ' + str(end_list[j]))
                j += 1
        if i<len(start_list):
            error_list.extend([item + ' ends missing for start at ' + str(start_list[s]) for s in range(i, len(start_list))])
        if j<len(end_list):
            error_list.extend([item + 'starts missing for end at ' + str(end_list[s]) for s in range(i, len(start_list))])
    return error_list, region_map


