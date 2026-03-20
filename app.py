from shiny.express import ui,render,input
from shiny import ui as ui_core
from shiny import reactive
from io import StringIO
import requests
import altair as alt
import polars as pl
from shinywidgets import render_widget

DataUrl = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuYSbC_H3vtCJlKiYdrO-22_1LkgegEJ1_rYkIBdpxhDlz55Nv8ZYZHP4b9expHxfn_aY8VeeLzgLL/pub?gid=1223006997&single=true&output=csv"
def get_live_data(url):
    response = requests.get(url)
    # Check if Google actually returned the data
    if response.status_code == 200:
        return pl.read_csv(
            StringIO(response.text),
            infer_schema_length=20000,
            truncate_ragged_lines=True
        )
    else:
        return pl.DataFrame() # Return empty if Google is down
    

df = get_live_data(DataUrl)
df2 = df.rename({"HEIGHT(M)":"Height_of_tree_in_meter", "GIRTH(CM)":"Girth_of_tree_in_cmeter"})


@reactive.calc
def range_df():
    return df2.filter((pl.col("RANGE")== input.range()) if input.range() !="all" else True)

@reactive.calc
def spp_df():
    return df2.filter((pl.col("SPECIES")== input.species()) if input.species() !="all" else True)

@reactive.calc
def cent_df():
    return df2.filter((pl.col("RESEARCH CENTER")== input.center()) if input.center() !="all" else True)

@reactive.calc
def summ_range():    # for summary of range
    
    df3 = df2.filter((pl.col("RANGE")== input.range2()) if input.range2() !="all" else True)
    return ( 
        df3.group_by("RESEARCH CENTER")
        .agg(pl.len().alias("Trees"),pl.col("Height_of_tree_in_meter").mean().round(2).alias("Avg_Height"),
             pl.col("Girth_of_tree_in_cmeter").mean().round(2).alias("Avg_Girth"))
    )

@reactive.calc
def summ_center():    # for summary of center
    
    df3 = df2.filter((pl.col("RESEARCH CENTER")== input.center2()) if input.center2() !="all" else True)
    return ( 
        df3.group_by("PLOT NAME")
        .agg(pl.len().alias("Trees"),pl.col("Height_of_tree_in_meter").mean().round(2).alias("Avg_Height"),
             pl.col("Girth_of_tree_in_cmeter").mean().round(2).alias("Avg_Girth"))
    )

@reactive.calc
def plot1():    # for summary of center
    
    df3 = df2.filter((pl.col("RANGE")== input.range2()) if input.range2() !="all" else True)
    df4 = (df3.group_by("RESEARCH CENTER")
        .agg(pl.len().alias("Trees"),pl.col("Height_of_tree_in_meter").mean().round(2).alias("Avg_Height"),
             pl.col("Girth_of_tree_in_cmeter").mean().round(2).alias("Avg_Girth")))
    return ( 
        alt.Chart(df4).mark_bar().encode(
            x= alt.X("RESEARCH CENTER:N"),
            y= alt.Y("Avg_Girth:Q"),
        )
    )

ui.page_opts(title= "Second Cycle of Measurement 2025-26")

with ui.layout_column_wrap(width=1/2):
    with ui.card():
            ui.input_select("range2", "Select Range For Summary", choices = ["all",*df.select(pl.col("RANGE").unique()).to_series().sort().to_list()] )
            @render.data_frame
            def summ_range_show():
                return (summ_range())
    with ui.card():
        @render_widget
        def plot1_show():
            return (plot1())        
        
with ui.card():
        ui.input_select("center2", "Select Center For Summary", choices = ["all",*df.select(pl.col("RESEARCH CENTER").unique()).to_series().sort().to_list()] )
        @render.data_frame
        def summ_center_show():
            return (summ_center())

with ui.layout_column_wrap(width=1/3):
    with ui.card():
        "The Total Trees Measured Rangewise"
        ui.input_select("range", "Select Range", choices = ["all",*df.select(pl.col("RANGE").unique()).to_series().sort().to_list()] )
        @render.text
        def raj_range():
            return (f"Total trees measured in {input.range() } is {range_df().height}")
        
    with ui.card():
        "The Total Species Measured"
        ui.input_select("species", "Select Species", choices = ["all",*df.select(pl.col("SPECIES").unique()).to_series().sort().to_list()] )
        @render.text
        def raj_spp():
            return (f"Total trees of {input.species() } measured are {spp_df().height}")
        
    with ui.card():
        " The Total Trees Measured Centerwise "
        ui.input_select("center", "Select Center", choices = ["all",*df.select(pl.col("RESEARCH CENTER").unique()).to_series().sort().to_list()] )
        @render.text
        def raj_cent():
            return (f"Total trees measured in  {input.center() } are {cent_df().height}")
        
   
"Find the Master Data Here"
@render.data_frame
def all_data():
    return render.DataGrid(
        df2,
        filters= True,
        editable = True,
        summary= True
        
    )



@render.download(filename="Silva_data.csv", label="Download Selected Data")
def download_filtered():
    view_df = all_data.data_view()
    
    yield view_df.write_csv()
