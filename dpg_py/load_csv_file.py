import os
import pandas as pd

def load_file(file_name, engine = None, dtype_backend = 'numpy_nullable'):
    hs_df = pd.read_csv(file_name, sep=";", decimal=',', engine=engine, dtype_backend=dtype_backend)
    hs_df["TimeString"] = pd.to_datetime(hs_df.TimeString, dayfirst=True)
    hs_df["TimeString"] = hs_df.TimeString.astype('int64')/1000000000
    return hs_df

def load_folder(path, engine = None, dtype_backend = 'numpy_nullable', drop_id = False):
    df_all = pd.DataFrame()

    for f in os.listdir(path):
        tmp = pd.read_csv(path + f, sep=";", decimal=',',  engine=engine, dtype_backend =dtype_backend) #335.6

        if drop_id:
            tmp = tmp.reset_index(drop=True)
            df_all = df_all.reset_index(drop=True)

        df_all = pd.concat([df_all, tmp], ignore_index=True)
    df_all["TimeString"] = pd.to_datetime(df_all.TimeString, dayfirst=True)
    return df_all