# CS122, Winter 2021: Course search engine: search
###
# Rhedintza Audryna and James Yunzhang Hu

from math import radians, cos, sin, asin, sqrt
import sqlite3
import os


# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course-info.db')

MASTER_LOOKUP = [("day",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["meeting_patterns.day = ?"]}),
                 ("time_start",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["meeting_patterns.time_start >= ?"]}),
                 ("time_end",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["meeting_patterns.time_end <= ?"]}),
                 ("building",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["loc_a.building_code = ?"]}),
                 ("walking_time",
                  {"select": ["loc_b.building_code",
                              ("time_between(loc_a.lon, loc_a.lat, "
                               "loc_b.lon, loc_b.lat) AS walking_time")],
                   "join": ["gps AS loc_a", "gps AS loc_b"],
                   "on": ["sections.building_code = loc_b.building_code"],
                   "where": ["walking_time <= ?"]}),
                 ("enroll_lower",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end",
                              "sections.enrollment"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["sections.enrollment >= ?"]}),
                 ("enroll_upper",
                  {"select": ["sections.section_num",
                              "meeting_patterns.day",
                              "meeting_patterns.time_start",
                              "meeting_patterns.time_end",
                              "sections.enrollment"],
                   "join": ["sections", "meeting_patterns"],
                   "on": ["courses.course_id = sections.course_id",
                          ("sections.meeting_pattern_id = "
                           "meeting_patterns.meeting_pattern_id")],
                   "where": ["sections.enrollment <= ?"]}),
                 ("dept",
                  {"select": ["courses.title"],
                   "join": [],
                   "on": [],
                   "where": ["courses.dept = ?"]}),
                 ("terms",
                  {"select": ["courses.title"],
                   "join": ["catalog_index"],
                   "on": ["courses.course_id = catalog_index.course_id"],
                   "where": ["word = ?"]})]


def find_courses(args_from_ui):
    '''
    Take a dictionary containing search criteria and find courses 
    that match the criteria. The input dictionary will contain some of
    the following fields:
      - dept: string
      - day: list with variable number of elements, e.g. ["MWF", "TR"]
      - time_start: integer in the range 0-2359
      - time_end: integer in the range 0-2359
      - building: string (paired with walking_time)
      - walking_time: integer (paired with building)
      - enroll_lower: integer
      - enroll_upper: integer
      - terms: string, e.g. "quantum plato"

    Inputs:
      - args_from_ui (dictionary): user input representing query

    Returns: a tuple consisting of a list of attribute names in order
             and a list containing query results
    '''
    connection = sqlite3.connect(DATABASE_FILENAME)

    if "walking_time" in args_from_ui:
        connection.create_function("time_between", 4, compute_time_between)

    c = connection.cursor()

    select, join, on = get_select_join_on(args_from_ui)

    select_str = "SELECT " + ", ".join(select)
    from_str = "FROM " + " JOIN ".join(join)
    if on:
        on_str = "ON " + " AND ".join(on)
    else:
        on_str = ""

    wheres, params = get_wheres_params(args_from_ui)
    where_str = "WHERE " + " AND ".join(wheres)

    s = select_str + " " + from_str + " " + on_str + " " + where_str

    results = c.execute(s, params)
    results_lst = results.fetchall()
    headers = get_header(c)
    connection.close()

    return (headers, results_lst)


def get_select_join_on(args_from_ui):
    '''
    Parse the user's input to generate the appropriate columns for SELECT,
    tables for JOIN, and criteria for ON.

    Inputs:
      - args_from_ui (dictionary): user input representing query

    Returns: a tuple consisting of three lists of strings
    '''
    select = ["courses.dept", "courses.course_num"]
    join = ["courses"]
    on = []

    for key, lookup in MASTER_LOOKUP:
        if key in args_from_ui:
            for s in lookup["select"]:
                if s not in select:
                    select.append(s)

            for j in lookup["join"]:
                if j not in join:
                    join.append(j)

            for o in lookup["on"]:
                if o not in on:
                    on.append(o)

    return (select, join, on)


def get_wheres_params(args_from_ui):
    '''
    Parse the user's input to generate the appropriate criteria for WHERE
    within the larger SQL query, as well as the appropriate parameters to
    pass in when executing the query.

    Inputs:
      - args_from_ui (dictionary): user input representing query

    Returns: a tuple consisting of two lists of strings
    '''
    wheres = []
    params = []

    for key, lookup in MASTER_LOOKUP:
        if key in args_from_ui:
            if key == "day":
                days = []

                for _ in args_from_ui["day"]:
                    days += lookup["where"]
                    
                days_str = " OR ".join(days)
                wheres.append("({})".format(days_str))
                params += args_from_ui["day"]

            elif key == "terms":
                terms = args_from_ui["terms"].split(" ")
                num = len(terms)
                
                if num == 1:
                    wheres += lookup["where"]
                else:
                    term_wheres = lookup["where"] * num
                    search_criteria = " OR ".join(term_wheres)
                    term_str = ("({}) GROUP BY catalog_index.course_id, "
                                "section_num HAVING COUNT(*) = "
                                "{}").format(search_criteria, num)
                    wheres.append(term_str)
                
                params += terms

            else:
                wheres += lookup["where"]
                params.append(args_from_ui[key])

    return (wheres, params)


########### auxiliary functions #################
########### do not change this code #############


def compute_time_between(lon1, lat1, lon2, lat2):
    '''
    Converts the output of the haversine formula to walking time in minutes
    '''
    meters = haversine(lon1, lat1, lon2, lat2)

    # adjusted downwards to account for manhattan distance
    walk_speed_m_per_sec = 1.1
    mins = meters / (walk_speed_m_per_sec * 60)

    return mins


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m


def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    desc = cursor.description
    header = ()

    for i in desc:
        header = header + (clean_header(i[0]),)

    return list(header)


def clean_header(s):
    '''
    Removes table name from header
    '''
    for i, _ in enumerate(s):
        if s[i] == ".":
            s = s[i + 1:]
            break

    return s


########### some sample inputs #################

EXAMPLE_0 = {"time_start": 930,
             "time_end": 1500,
             "day": ["MWF"]}

EXAMPLE_1 = {"dept": "CMSC",
             "day": ["MWF", "TR"],
             "time_start": 1030,
             "time_end": 1500,
             "enroll_lower": 20,
             "terms": "computer science"}
