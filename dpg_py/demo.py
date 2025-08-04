import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title='Plot demo', width=600, height=600)
# demo
dpg.show_implot_demo()

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()