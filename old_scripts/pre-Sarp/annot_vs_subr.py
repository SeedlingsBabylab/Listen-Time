import pandas as pd
import sys


def process(regions, annots):
    annots['in_subregion'] = inside_regions(regions, annots)
    probs = annots.query('in_subregion == False')
    return probs

def inside_regions(regions, annots):
    results = []
    for i, ann in annots.iterrows():
        results.append(any(inside(ann, reg)
                           for i, reg in regions.iterrows()))
    return results


def inside(x, reg):
    if reg.onset <= x.onset <= reg.offset:
        return True


if __name__ == "__main__":

    subregions = pd.read_csv(sys.argv[1])
    all_bl = pd.read_csv(sys.argv[2]).query('audio_video == \"audio\"')

    problems = pd.DataFrame(columns = all_bl.columns)
    for subjnum, regions in subregions.groupby('file'):
        annots = all_bl.query('SubjectNumber == \"{}\"'.format(subjnum))
        prob_annots = process(regions, annots)
        problems = problems.append(prob_annots)

    problems.to_csv('annotations_outside_subregions.csv', index=False)

