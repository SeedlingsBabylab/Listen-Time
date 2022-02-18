from pathlib import Path

from blabpy.seedlings.pipeline import calculate_listen_time_stats_for_all_cha_files


output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

df = calculate_listen_time_stats_for_all_cha_files()
df.to_csv(output_dir / 'Total_Listen_Time_Summary.csv', index=False)
