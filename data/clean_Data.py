#%%
import pandas as pd
from src.utils.constants import RAW_DATA

#%%
df_coffee = pd.read_csv(RAW_DATA)

region_columns = [
    "region_africa_arabia", "region_caribbean", "region_central_america", 
    "region_hawaii", "region_asia_pacific", "region_south_america"
]

df_coffee['region'] = df_coffee[region_columns].idxmax(axis=1).str.replace("region_", "")

# Drop the original one-hot encoded columns
df = df_coffee.drop(columns=region_columns)

# Save the transformed DataFrame if needed
df_coffee.to_csv(r"C:\Users\Jeff\OneDrive\Documents\projects\COFFEE_RAG\data\coffee_cleaned.csv", index=True)
# %%
