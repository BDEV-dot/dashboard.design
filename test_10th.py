import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State, ALL
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd

# Load OMG Channel Curated Lists
omg_clist = pd.read_csv(r"C:\Users\BenLynch(PHDMedia)\Desktop\R Coding\VS Coding\Datasets\OMG Channel Curated Lists\omg_channel_curated_lists.csv")
omg_clist = omg_clist[omg_clist["Group_Thumbnail_URL"].notna()].reset_index(drop=True)

# Create Main OMG Channel Lists For Session
main_omg_clist = omg_clist.copy()
main_omg_clist['Included'] = 'No'

# Create Starting Temp OMG Channel List For Session
temp_omg_clist = main_omg_clist.copy()

# Created Filtered Temp OMG Channel List For Session
filtered_omg_clist = temp_omg_clist.copy()  # No filters applied at first

# Get unique values for filters (remove "View All")
genres = sorted(main_omg_clist["Video_Genre"].dropna().unique())
languages = sorted(main_omg_clist["Video_Language_Output"].dropna().unique())
countries = sorted(main_omg_clist["Channel_Country"].dropna().unique())

# Generate placements per channel group with the checkbox state based on the Included column
def generate_group_placements(group_id, filtered_df, temp_omg_clist_df):
    # Get the URLs for the group
    urls = filtered_df[filtered_df["Channel_Group_ID"] == group_id]["Channel_URL"].tolist()
    names = filtered_df[filtered_df["Channel_Group_ID"] == group_id]["Channel_Name"].tolist()
    channel_genre = filtered_df[filtered_df["Channel_Group_ID"] == group_id]["Channel_Genre_Manual"].tolist()
    channel_country = filtered_df[filtered_df["Channel_Group_ID"] == group_id]["Channel_Country"].tolist()

    # Initialize the Include column and Checkbox column based on the Included column from temp_omg_clist_df
    included = []
    checkbox = []
    
    for url in urls:
        # Check the corresponding 'Included' value in temp_omg_clist_df
        include_value = temp_omg_clist_df[temp_omg_clist_df["Channel_URL"] == url]["Included"].values
        
        # If include_value exists and is "Yes", check the checkbox, else uncheck it
        if include_value and include_value[0] == "Yes":
            included.append("Yes")
            checkbox.append(True)  # Check the checkbox
        else:
            included.append("No")
            checkbox.append(False)  # Uncheck the checkbox
    
    # Return a DataFrame with the updated Include and Checkbox columns
    return pd.DataFrame({
        "Channel Name": names,
        "Channel Genre": channel_genre,
        "Channel Country": channel_country,
        "Included": included,
        "Channel_URL": urls,
        "Checkbox": checkbox  # This will hold boolean values for checked/unchecked
    })

# App setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Channel Cards with Selection"
app.config.suppress_callback_exceptions = True

# Layout with the button to open modal and the table for filtered results
app.layout = dbc.Container([
    html.Br(),
    dbc.Button("Open Curated Picks", id="open-modal", color="primary"),

    # Stores
    dcc.Store(id="selected-urls", data=[]),  # Stores selected Channel_URLs (yes/no)
    dcc.Store(id="temp-selected", data={}),  # Tracks temporary checkbox states
    dcc.Store(id="filtered-omg-clist", data=filtered_omg_clist.to_dict("records")),  # Store filtered dataframe
    dcc.Store(id="accordion-open-channel", data=None),  # Tracks open accordion row
    dcc.Store(id="selected-channel-urls", data=[]),  # Store selected channel URLs
    dcc.Store(id="temp_omg_clist", data=temp_omg_clist.to_dict("records")),  # Store temp_omg_clist data

    # Modal with filters + group cards
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Curated Channel Group Picks")),
        dbc.ModalBody(
            dbc.Row([ 
                dbc.Col([
                    html.H6("Filter By Genre"),
                    dcc.Dropdown(
                        id="genre-sort-dropdown",
                        options=[{"label": g, "value": g} for g in genres],
                        placeholder="Select Genre",
                        clearable=True,
                        multi=True  # Enable multi-selection
                    ),
                    html.H6("Spoken Language", style={"marginTop": "15px"}),
                    dcc.Dropdown(
                        id="language-sort-dropdown",
                        options=[{"label": l, "value": l} for l in languages],
                        placeholder="Select Language",
                        clearable=True,
                        multi=True  # Enable multi-selection
                    ),
                    html.H6("Channel Country", style={"marginTop": "15px"}),
                    dcc.Dropdown(
                        id="country-sort-dropdown",
                        options=[{"label": c, "value": c} for c in countries],
                        placeholder="Select Country",
                        clearable=True,
                        multi=True  # Enable multi-selection
                    )
                ], width=3),
                
                # Group Cards + Placement Panels
                dbc.Col([
                    html.Div(
                        id="card-gallery-body",
                        style={
                            "maxHeight": "70vh",
                            "overflowY": "auto",
                            "padding": "10px",
                            "marginTop": "10px"
                        }
                    )
                ], width=9)
            ])
        ),
        dbc.ModalFooter([
            dbc.Button("Apply", id="apply-selection", color="primary", className="ms-auto"),
            dbc.Button("Close", id="close-modal", color="dark", className="ms-2")
        ])
    ], id="card-modal", is_open=False, size="xl", scrollable=True, centered=True),

    # Output below modal
    html.Hr(),
    html.H5("Curated List Output"),
    html.Div(id="filtered-output")
])

# Callback to manage accordion toggle (open/close)
@app.callback(
    Output("accordion-open-channel", "data"),
    Input({"type": "toggle-accordion", "index": ALL}, "n_clicks_timestamp"),
    State({"type": "toggle-accordion", "index": ALL}, "id"),
    State("accordion-open-channel", "data"),
    prevent_initial_call=True
)
def update_open_accordion(n_clicks_ts, ids, current_open):
    if not any(n_clicks_ts):
        return dash.no_update
    idx = n_clicks_ts.index(max(filter(None, n_clicks_ts)))  # Find the last clicked button
    new_open = ids[idx]["index"]  # Get the group id from the button clicked
    return None if new_open == current_open else new_open

# Callback to render cards and accordion (without redundant filtering)
@app.callback(
    Output("card-gallery-body", "children"),    
    [
        Input("filtered-omg-clist", "data"),  # Get the filtered dataframe
        Input("accordion-open-channel", "data")  # Track open accordion state
    ],
    State("selected-channel-urls", "data"),  # Get the selected URLs state
    State("temp_omg_clist", "data")  # Get the temp_omg_clist data
)
def render_cards_and_accordion(filtered_omg_clist, open_channel, selected_channel_urls, temp_omg_clist):
    # Convert filtered_omg_clist and temp_omg_clist back to DataFrames
    filtered_df = pd.DataFrame(filtered_omg_clist)
    temp_omg_clist_df = pd.DataFrame(temp_omg_clist)
    
    # Filter temp_omg_clist by Channel_URL based on matches with filtered_omg_clist
    filtered_df = temp_omg_clist_df[temp_omg_clist_df["Channel_URL"].isin(filtered_df["Channel_URL"])]

    # If the filtered dataframe is empty, return a message instead of rendering cards
    if filtered_df.empty:
        return html.Div("No channels found based on the selected filters.")  # Display message when no data is available

    # Group the data by Channel_Group_ID
    grouped = filtered_df.groupby("Channel_Group_ID")
    gallery = []
    row_cards = []

    for group_id, group in grouped:
        group_info = group.iloc[0]
        group_img = group_info["Group_Thumbnail_URL"]
        group_name = group_info["Channel_Group"]
        genre = group_info["Channel_Genre_Manual"]
        clickthrough_url = group_info["Group_Clickthrough_URL"]
        count = group.shape[0]
        channel_urls = group["Channel_URL"].tolist()
        included_all = all(url in selected_channel_urls for url in channel_urls)

        card = dbc.Col([ 
            dbc.Card([ 
                html.A(html.Div(style={ 
                    "width": "100%", "height": "105px", "borderRadius": "15px 15px 0 0", 
                    "backgroundImage": f"url('{group_img}')", "backgroundSize": "cover", 
                    "backgroundPosition": "center", "backgroundColor": "#969EF8" 
                }), href=clickthrough_url, target="_blank"), 
                dbc.CardBody([ 
                    html.Div(group_name, style={"fontSize": "15px", "fontWeight": "bold", "textAlign": "center", "marginBottom": "5px"}), 
                    html.Div(genre, style={"fontSize": "13px", "textAlign": "center", "marginBottom": "5px"}), 
                    html.Div(f"Channels: {count}", style={"fontSize": "12px", "textAlign": "center", "marginBottom": "10px"}), 
                    dcc.Checklist( 
                        options=[{"label": "Included" if included_all else "Unselected", "value": group_id}], 
                        value=[group_id] if included_all else [], 
                        id={"type": "card-check", "index": group_id}, 
                        inputStyle={"display": "none"}, 
                        labelStyle={"display": "inline-block", "backgroundColor": "#0d6efd" if included_all else "#adb5bd", "color": "white", "padding": "6px 12px", "borderRadius": "8px", "marginBottom": "10px", "width": "90%", "textAlign": "center"}, 
                        style={"textAlign": "center"} 
                    ), 
                    html.Div( 
                        dbc.Button("Channel List", id={"type": "toggle-accordion", "index": group_id}, size="sm", color="secondary", style={"width": "90%"}), 
                        style={"textAlign": "center"} 
                    ) 
                ]) 
            ], style={"width": "175px", "padding": "10px", "marginBottom": "15px", "backgroundColor": "white", "borderRadius": "15px"}) 
        ], xs=12, sm=6, md=4, lg=3)

        row_cards.append((group_id, card))

    # Second pass to render rows (4 cards per row)
    for i in range(0, len(row_cards), 4):  # Loop over row_cards in steps of 4
        current_row = row_cards[i:i+4]
        gallery.append(dbc.Row([col for _, col in current_row], className="gy-3"))

        # If open_channel is in this row, add accordion below
        if open_channel in [group_id for group_id, _ in current_row]:
            placements = generate_group_placements(open_channel, filtered_df, temp_omg_clist_df)
            
            gallery.append(
                dbc.Row(dbc.Col([  # Wrap DataTable in a Column
                    html.Div([  # Accordion content
                        dash_table.DataTable(
                            columns=[
                                {"name": "Channel Name", "id": "Channel Name", "presentation": "markdown"},
                                {"name": "Channel Genre", "id": "Channel Genre"},
                                {"name": "Channel Country", "id": "Channel Country"},
                            ],
                            data=[{
                                **row,
                                "Channel Name": f"[{row['Channel Name']}]({row['Channel_URL']})"  # Make Channel Name a hyperlink
                            } for row in placements.to_dict("records")],
                            editable=True,  # Allow checkbox to be editable
                            row_selectable="multi",  # Allow multiple rows to be selected
                            selected_rows=[i for i, row in enumerate(placements.to_dict("records")) if row["Checkbox"]],
                            page_size=20,
                            style_table={"overflowX": "auto"},
                            style_cell={"fontSize": 12, "padding": "5px"},
                            style_header={"fontWeight": "bold"},
                            id={"type": "datatable", "index": open_channel}
                        )
                    ], style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "10px"})
                ], width=12)) 
            )

    return gallery

# Callback to toggle the modal visibility
@app.callback(
    Output("card-modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("card-modal", "is_open")]
)
def toggle_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open

# Callback to update selected URLs based on datatable selections
@app.callback(
    Output("temp_omg_clist", "data"),  # Store updated temp_omg_clist
    Input({"type": "datatable", "index": ALL}, "selected_rows"),  # Trigger when any datatable row is selected
    State({"type": "datatable", "index": ALL}, "data"),  # Get the datatable data
    State("selected-channel-urls", "data"),  # The current selected URLs
    State("temp_omg_clist", "data")  # Get the temp_omg_clist data
)
def update_selected_urls(selected_rows_list, datatable_data_list, current_selected_urls, temp_omg_clist_data):
    # Stage 1: Receive selected-channel-urls data
    selected_urls = set(current_selected_urls)  # Use a set to avoid duplicates

    for selected_rows, datatable_data in zip(selected_rows_list, datatable_data_list):
        for row_index in selected_rows:
            selected_urls.add(datatable_data[row_index]["Channel_URL"])

    # Condition: Ensure there are selected URLs before proceeding
    if not selected_urls:
        return temp_omg_clist_data

    # Convert temp_omg_clist to DataFrame
    temp_omg_clist_df = pd.DataFrame(temp_omg_clist_data)
    
    # Print column names to debug the KeyError
    print("Columns in temp_omg_clist_df:", temp_omg_clist_df.columns)

    # Stage 2: Use the first row from selected-channel-urls to find Channel_Group_ID
    first_selected_url = next(iter(selected_urls))
    matching_row = temp_omg_clist_df[temp_omg_clist_df["Channel_URL"] == first_selected_url]
    if matching_row.empty:
        return temp_omg_clist_data
    
    channel_group_id = matching_row.iloc[0]["Channel_Group_ID"]

    # Stage 3: Create new DataFrame with rows matching Channel_Group_ID
    new_df = temp_omg_clist_df[temp_omg_clist_df["Channel_Group_ID"] == channel_group_id][["Channel_Group_ID", "Channel_URL", "Included"]]

    # Stage 4: Update Included column based on selected-channel-urls
    new_df["Included"] = new_df["Channel_URL"].apply(lambda url: "Yes" if url in selected_urls else "No")

    # Stage 5: Update temp_omg_clist with values from new_df
    temp_omg_clist_df.set_index("Channel_URL", inplace=True)
    new_df.set_index("Channel_URL", inplace=True)
    temp_omg_clist_df.update(new_df["Included"])
    temp_omg_clist_df.reset_index(inplace=True)

    # Convert updated DataFrame back to dictionary for storage
    updated_temp_omg_clist_data = temp_omg_clist_df.to_dict("records")

    return updated_temp_omg_clist_data

# Callback To Filter The OMG Channel List In Session
@app.callback(
    Output("filtered-omg-clist", "data"),  # Update the filtered_omg_clist store
    [
        Input("genre-sort-dropdown", "value"),
        Input("language-sort-dropdown", "value"),
        Input("country-sort-dropdown", "value"),
        Input("filtered-omg-clist", "data")  # Get the filtered dataframe
    ]
)
def update_filtered_list(selected_genre, selected_language, selected_country, filtered_omg_clist):
    # Start with the original temp_omg_clist dataset (no pre-filters)
    filtered_df = pd.DataFrame(temp_omg_clist)

    # Apply filtering logic based on dropdowns
    if selected_genre:
        filtered_df = filtered_df[filtered_df["Video_Genre"].isin(selected_genre)]
    if selected_language:
        filtered_df = filtered_df[filtered_df["Video_Language_Output"].isin(selected_language)]
    if selected_country:
        filtered_df = filtered_df[filtered_df["Channel_Country"].isin(selected_country)]

    # Save the filtered data back into filtered_omg_clist for future use
    filtered_omg_clist = filtered_df

    # Return the updated filtered dataframe to the store and the table to the UI
    return filtered_omg_clist.to_dict('records')

# Function to create the table based on filtered DataFrame
def create_table(filtered_df):
    # Pagination: Show only the first 20 rows
    page_size = 20
    filtered_df_page = filtered_df.head(page_size)

# Function to create the table based on filtered DataFrame
def create_table(filtered_df):
    # Pagination: Show only the first 20 rows
    page_size = 20
    filtered_df_page = filtered_df.head(page_size)

    # Create the table with column headers even if no data is present
    return html.Div([ 
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in filtered_df.columns],  # Column headers
            data=filtered_df_page.to_dict('records') if not filtered_df.empty else [],  # No data but headers
            page_size=page_size,  # Set initial page size to 20
            style_table={"overflowX": "auto"},
            style_cell={"fontSize": 12, "padding": "5px"},
            style_header={"fontWeight": "bold"},
            page_action='native',  # Native pagination
            page_current=0  # Start at the first page
        )
    ])

# Callback to update the table display based on the selected URLs
@app.callback(
    Output("filtered-output", "children"),  # Display the table in the main section
    [Input("temp_omg_clist", "data")]  # Get the selected URLs from the store
)
def display_selected_urls(temp_omg_clist):
    # Create a DataFrame with temp_omg_clist (ensure the column names match your dataset)
    temp_omg_clist_df = pd.DataFrame(temp_omg_clist)

    # Filter the rows where the 'Included' column is 'Yes'
    filtered_df = temp_omg_clist_df[temp_omg_clist_df['Included'] == 'Yes']

    # Generate the table using the create_table function
    return create_table(filtered_df)


if __name__ == "__main__":
    app.run_server(debug=True)