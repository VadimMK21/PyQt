import dearpygui.dearpygui as dpg
from add_kks_pl import add_kks

dpg.create_context()

def callback(sender, app_data):
    #print(app_data)
    x,y = add_kks(app_data['file_path_name'], x="TimeString", y="VarValue")
    dpg.add_line_series(x=x.tolist(), y=y.tolist(), label=app_data['file_name'], parent="y_axis")
    dpg.fit_axis_data("y_axis")
    dpg.fit_axis_data("x_axis")
    list_items.append(app_data['file_name'])
    dpg.configure_item('list_kks', items=list_items)

def cancel_callback(sender, app_data):
    pass

def my_function(sender):
    print(dpg.get_value(sender))

with dpg.file_dialog(directory_selector=False, show=False, callback=callback, id="file_dialog_id", cancel_callback=None, width=700 ,height=400):
    dpg.add_file_extension(".csv", color=(0, 255, 0, 255), custom_text="[CSV]")

with dpg.window(tag="Primary Window", autosize=True):
    list_items = []
    dpg.add_button(label="add history", callback=lambda: dpg.show_item("file_dialog_id"))
    dpg.add_listbox(label='list_kks', items=list_items, width=140, num_items=10, tag='list_kks', callback=my_function)

    with dpg.plot(width=-1,height=-1, pos=[155,10], use_24hour_clock=True, use_ISO8601=True, tag='hs_plot'):
        # optionally create legend
        dpg.add_plot_legend()
        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, tag="x_axis", time=True)
        dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis")

dpg.create_viewport(title='History Trend', always_on_top=True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()