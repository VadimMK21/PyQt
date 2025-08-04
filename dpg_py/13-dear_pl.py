import dearpygui.dearpygui as dpg
import pandas as pd
import os

path = 'C:/Projects/block3/123/'

def load_file():
    pass

def load_date(file_name):
    hs_df = pd.read_csv(f"./123/{file_name}", sep=";", decimal=',', engine='pyarrow', dtype_backend='pyarrow')
    hs_df["TimeString"] = pd.to_datetime(hs_df.TimeString, dayfirst=True)

    x = hs_df.loc[1:,"TimeString"]
    x = x.astype('int64')/1000000000
    y = hs_df.loc[1:,"VarValue"]

    dpg.add_line_series(x=x.tolist(), y=y.tolist(), parent="y_axis")

dpg.create_context()

def callback(sender, app_data, user_data):
    print("Sender: ", sender)
    print("App Data: ", app_data)

with dpg.file_dialog(directory_selector=False, show=False, callback=callback, id="file_dialog_id", width=700 ,height=400):
    dpg.add_file_extension(".*")
    dpg.add_file_extension("", color=(150, 255, 150, 255))
    dpg.add_file_extension(".csv", color=(0, 255, 0, 255), custom_text="[CSV]")

with dpg.window(tag="Primary Window", autosize=True):
    dpg.add_slider_int(label='Start time',width=-1,min_value=0, max_value=100,)
    dpg.add_slider_int(label='End time',width=-1,min_value=0, max_value=100,)
    dpg.add_button(label='add',width=120, height=40,indent=10,  callback=lambda: dpg.show_item("file_dialog_id"))
    dpg.add_button(label='clear',width=120, height=40,indent=10)

    dpg.add_listbox(os.listdir(path),width=140, num_items=15)

    with dpg.plot(width=-1,height=-1,pos=(155,50),use_24hour_clock=True,use_ISO8601=True):
        # optionally create legend
        dpg.add_plot_legend()
        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, time=True)
        dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis")
        load_date('31HAJ00CF0010.csv')
        load_date('31HAJ10CT0010.csv')
        load_date('31HAJ20CT0010.csv')
        load_date('31HBK03CT0020.csv')
        
        load_date('31HBK03CT0010.csv')
        load_date('31HLA00CT0010.csv')
        load_date('31HNA00CT0010.csv')
        load_date('31HBK03CT0010.csv')

dpg.create_viewport(title='History Trend', always_on_top=True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()