# stk-to-mavlink-waypoints
Given an STK aircraft `.ac` file, extract the aircraft's waypoints and create a MavLink `.waypoints` file that can then be loaded into APM Mission Planner or other ground control software supported by MavLink. You can read more about the MavLink file format here: [https://mavlink.io/en/file_formats/](https://mavlink.io/en/file_formats/)

Only fields that are common between STK and MavLink waypoints are extracted. Fields extracted are waypoint latitude (degrees), longitude (degrees), and altitude (meters). The remaining fields will need to be populated in the GCS once the waypoints have been loaded.

This tool has only been tested using APM Mission Planner, and the free version of STK12. Learn more about STK here: [https://www.agi.com/products/stk](https://www.agi.com/products/stk)

# Usage
To use this tool, pass the path to the aircraft file as an argument to the python script.

`python extract.py /path/to/file.ac`

The tool will then extract waypoints from the given `.ac` file, and save them into a `.waypoints` file in your current directory. 
