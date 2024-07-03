from pandas import DataFrame


web_stats = {'Day': [1, 2, 3, 4, 2, 6],
             'Visitors': [43, 43, 34, 23, 43, 23],
             'Bounce_Rate': [3, 2, 4, 3, 5, 5]}
df = DataFrame(web_stats)
print(f"before drop, df is {df}")

df.drop(df.index, inplace=True)

print(f"after drop, df is {df}")


