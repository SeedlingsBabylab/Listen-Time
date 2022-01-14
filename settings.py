# Precision for rounding the millisecond values.
PRECISION = 2

# These are the header fields for the summary csv output. 
FIELD_NAMES = [
    'filename',
    'subregion_time',
    'skip_time',
    'num_makeup_region',
    'num_subregion_with_annot',
    'total_listen_time',
    'num_extra_region',
    'silence_time',
    'num_surplus_region',
    'surplus_time',
    'makeup_time',
    'extra_time',
    'extra_time_hour',
    'makeup_time_hour',
    'surplus_time_hour',
    'silence_time_hour',
    'subregion_time_hour',
    'skip_time_hour',
    'skip_silence_overlap_hour',
    'end_time_hour',
    'total_listen_time_hour',
    'silence_raw_hour',
    'subregion_raw_hour',
    'num_raw_subregion',
    'subregions',
    'positions',
    'ranks',
    'counts',
    'removals'
     ]


class BColors:
    """
    Container for holding ANSI colors for colored console output
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


REGION_TYPES = ("subregion", "silence", "skip", "makeup", "extra", "surplus")
