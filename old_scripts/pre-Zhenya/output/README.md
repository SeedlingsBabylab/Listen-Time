## Files in this folder:

### XX_XX_sparse_code.cha.txt:

These files provide a summary of all different types of subregions for each sparse_code.cha file. All the start and end times of each type of region is outputted in the order
that they are encountered. It is useful for sanity checks and getting a general sense about the layout of the cha file. It also provides error summary for that file, which is
also available in the Error_Summary.txt file.

### Error_Summary.txt:

This file is a summary of all the errors encountered while processing the cha files, such as nested regions, missing starts/ends, etc.

### Total_Listen_Time_Summary.csv

This file contains the combined statistics for each cha file. The columns are:

Filename | Subregion Total/ms | Makeup Total/ms | Extra Total/ms | Surplus Total/ms | Silence Total/ms | Skip Total/ms | Num Subregion with Annots | Num Extra Region | Num Makeup Region | Num Surplus Region | Total Listen Time/ms | Total Listen Time/hour
|---|---|---|---|---|---|---|---|---|---|---|---|---|
01_06_sparse_code.cha | 0 | 0 | 0 | 0 | 21101110 | 35811840 | 0 | 0 | 0 | 0 | 36498880 | 10.1385777778
01_07_sparse_code.cha | 0 | 0 | 0 | 0 | 22274360 | 737060 | 0 | 0 | 0 | 0 | 35325630 | 9.812675
01_08_sparse_code.cha | 7200000 | 0 | 300240 | 6092080 | 0 | 0 | 2 | 1 | 0 | 3 | 13592320 | 3.77564444444

For months 6 and 7, the Total Listen Time is calculated by subtracting Silence Total and Skip Total from the last offset in the cha file. 
