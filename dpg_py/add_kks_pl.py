from load_csv_file import load_file

def add_kks(file, x, y,path=''):

    df = load_file(path + file, 'pyarrow', 'pyarrow') 
    x = df.loc[1:, x]
    y = df.loc[1:, y]
    return x,y