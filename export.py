"""The purpose of these functions is to convert STK aircraft waypoints into
MavLink waypoints. This means you can mission plan in STK, and then export your
waypoints to a GCS suite like MissionPlanner to actually fly the mission. The
MavLink mission file format can be found here:
https://mavlink.io/en/file_formats/"""

from pathlib import Path
import sys
import pandas as pd

def extract_raw_waypoints(ac_file):
    """Extracts waypoint entries from the given STK .ac (aircraft) file and
    returns the "raw" waypoint strings as a dataframe"""
    with open(ac_file,'r', encoding="utf8") as datafile:
        # Grab all the lines from the aircraft data file
        ac_data = datafile.readlines()

    # Convert the list of lines from the aircraft datafile into a single string
    # to be parsed
    ac_data = ''.join(ac_data)

    # Split the string based on known waypoint start/end markers
    raw_waypoints = ac_data.split('BEGIN Waypoints')[1]
    raw_waypoints = raw_waypoints.split('END Waypoints')[0]

    # Strip the leading/following whitespace
    raw_waypoints = raw_waypoints.strip()

    # Split the string by newlines to separate waypoints
    raw_waypoints = raw_waypoints.splitlines()

    # For each waypoint string, split it into individual parameters using the
    # spaces (' ') between each parameter
    # Also filter out any empty strings ('') from the waypoint
    # This results in a list of lists where each sublist is an individual
    # waypoint [[waypoint1_params], [waypoint2_params], ...]
    # Also convert the list items to floats from strings
    waypoints = [
        list(map(float, filter(None, wp.split(' ')))) for wp in raw_waypoints
    ]

    # Need to transform the list of waypoints so that each list represents an
    # individual column of data. This is a requirement for making a pandas
    # dataframe. First, set the column names. Names and units come from STK
    stk_column_names = [
            'Time [sec]', 'Lat [deg]', 'Long [deg]', 'Alt [m]',
            'Speed [m/s]', 'Accel [m/s/s]', 'TurnRadius [m]'
    ]

    # Finally, create the pandas dataframe and return it
    waypoints = pd.DataFrame.from_records(waypoints, columns=stk_column_names)

    return waypoints

def filter_raw_waypoints(raw_waypoints):
    """Filter a dataframe of waypoints down into the values we want to keep.
    The only parameters relevant to MavLink are the lat, long, and altitude of
    each waypoint."""
    # List of headers that we want to extract from the raw_waypoints
    extract_headers = ['Lat [deg]', 'Long [deg]', 'Alt [m]']

    # Extract the relevant columns from the raw waypoints dataframe into a
    # trimmed waypoints dataframe
    trimmed_waypoints = raw_waypoints[[*extract_headers]]

    return trimmed_waypoints

def create_mavlink_waypoints(trimmed_waypoints):
    """This function converts the filtered waypoints dataframe into a dataframe
    of MavLink-formatted waypoints"""

    # MavLink waypoints have a number of columns that our STK data does not, so
    # we need to add the columns to our trimmed_waypoints dataframe with dummy
    # values so that. MavLink can read the waypoints. In order to add a column
    # to the dataframe, we need a column name and column values.
    # 'column_name : default_column_value'
    # None's are present in this dictionary to represent the columns that were
    # extracted from the STK waypoints
    default_columns = {
        'Current WP': 0, 'Coord Frame': 3, 'Command': 16, 'Param 1': 0,
        'Param 2': 0, 'Param 3': 0, 'Param 4': 0, None:None, None:None,
        None:None, 'AutoContinue': 1
    }

    num_waypoints = len(trimmed_waypoints.index)

    # Loop through the default columns dictionary and the columns + values
    # to the dataframe
    for col_num, col_name in enumerate(default_columns):
        if col_name is not None:
            trimmed_waypoints.insert(
                col_num, col_name,
                [default_columns[col_name]]*num_waypoints,
                True
            )

    # MavLink also expects an initial dummy waypoint before any of the 'real'
    # waypoints. We'll make another dictionary for this row
    initial_header = {
        'Current WP': 1, 'Coord Frame': 0, 'Command': 0, 'Param 1': 0,
        'Param 2': 0, 'Param 3': 0, 'Param 4': 0, 'Lat [deg]':0.,
        'Long [deg]': 0., 'Alt [m]':0., 'AutoContinue': 1
    }

    # And finally, insert the dummy row at the top of the waypoints dataframe
    waypoints = pd.concat(
        [pd.DataFrame([initial_header], dtype=object),trimmed_waypoints],
        ignore_index=True
    )

    # We now have a dataframe of complete MavLink waypoints
    return waypoints

def create_waypoint_file(waypoints, filename):
    """This function takes a dataframe of complete MavLink waypoints and writes
    them to a MavLink .waypoints file"""

    # Every MavLink waypoints file has this header
    wpfile_header = 'QGC WPL 0\n'

    # And finally open a new waypoints file and write the waypoints to it
    with open(f'{filename}.waypoints', 'w', encoding='utf8') as wp_file:
        # write the header
        wp_file.write(wpfile_header)

        # Convert each line of the dataframe into a string and loop thru
        for wp_index, wp in enumerate(waypoints.astype(str).values.tolist()):
            # Insert a waypoint index number at the beginning of each waypoint
            # since we lost those when we converted the dataframe to a list
            wp.insert(0, str(wp_index))

            # Finally, tab delimit the waypoint list, add a newline char,
            # and write to the file.
            wp_file.write('\t'.join(wp) + '\n')

def extract_stk_waypoints(ac_file):
    """This is the main function of this tool. It takes in a file path to an
    STK aircraft datafile and uses our helper functions to create a MavLink
    waypoints file"""

    # Get the name of the aircraft from the datafile that was passed
    ac_name = Path(ac_file).stem.split('.')[0]

    # Extract the raw STK waypoints
    raw_waypoints = extract_raw_waypoints(ac_file)

    # Trim the raw STK waypoints down to what MavLink can use
    trimmed_waypoints = filter_raw_waypoints(raw_waypoints)

    # Convert the trimmed waypoints into the MavLink format
    waypoints = create_mavlink_waypoints(trimmed_waypoints)

    # Write out the mavlink .waypoints file
    create_waypoint_file(waypoints, ac_name)

    # Give a nice message
    print(
        f"Created waypoints file {ac_name}.waypoints in the current directory."
    )

if __name__ == "__main__":
    # If we are running this file directly, then lets check for a filepath
    # given as an argument in the command line. If no arguments were given,
    # then throw an error message.
    if len(sys.argv) < 2:
        # No arguments given in this case
        print(
            "You must provide a filepath for the aircraft file you wish to \
            extract the waypoints from as an argument to the python script. \
            For example: python export.py /home/f22.ac"
        )
    else:
        # Otherwise, grab the filepath and give it to the extractor
        ac_filepath = str(sys.argv[1])
        extract_stk_waypoints(ac_filepath)
