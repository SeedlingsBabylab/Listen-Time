import pandas as pd


df = pd.read_csv("all_cha_top5.csv")



df['onset'] = df.orig_index *5*60*1000
df['offset'] = df.onset+3600000

df.to_csv("all_cha_top5_ms.csv", index=False)

# df = pd.read_csv("annotations_outside_subregions_NEW.csv")





# df =
print()


