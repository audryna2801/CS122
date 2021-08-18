# CS122: Linking restaurant records in Zagat and Fodor's data sets
#
# Rhedintza Audryna


import numpy as np
import pandas as pd
import jellyfish
import util


def load_data():
    '''
    Function to load data from csv to dataframe

    Inputs:
        - None

    Returns: three pandas dataframes
    '''

    zagat = pd.read_csv("zagat.csv", names=["resto_name", "city", "address"],
                        index_col=0)
    fodors = pd.read_csv("fodors.csv", names=["resto_name", "city", "address"],
                         index_col=0)
    known_links = pd.read_csv("known_links.csv", names=["zagat", "fodors"])

    return (zagat, fodors, known_links)


def get_match_and_unmatch(zagat, fodors, known_links):
    '''
    Generates the match and unmatch training dataframes

    Inputs:
        - zagat (pd df): The zagat restaurants dataframe
        - fodors (pd df): The fadors restaruants dataframe
        - known_links (pd df): The known-matches between the
            zagat and fodors restaurants

    Returns: two pandas dataframes
    '''

    # Matches
    matches = zagat.merge(known_links, left_index=True, right_on="zagat")
    matches = matches.merge(fodors, left_on="fodors",
                            right_index=True, suffixes=('_zagat', '_fodors'))
    matches = matches.reset_index(drop=True).drop(columns=["zagat", "fodors"])

    # Unmatches
    zs = zagat.sample(1000, replace=True, random_state=1234)
    fs = fodors.sample(1000, replace=True, random_state=5678)
    unmatches = zs.reset_index(drop=True).join(fs.reset_index(drop=True),
                                               lsuffix='_zagat',
                                               rsuffix='_fodors')

    return (matches, unmatches)


def generate_all_possible_tuples():
    '''
    Generates the 27 possible combinations of three similarity levels 
    in three different positions

    Input: 
        - None

    Returns: list of all possible tuples
    '''

    values = ('high', 'medium', 'low')
    tuple_possibilities = []
    for a in values:
        for b in values:
            for c in values:
                tuple_possibilities.append((a, b, c))

    return tuple_possibilities


def get_tuple_score(row):
    '''
    Takes a row from a dataframe that matches restaurants 
    from zagat and fodors to generate tuple containing 
    similarity levels for name, city, and address

    Inputs: 
        - row (pd series): a row from a df

    Returns: a tuple consisting of three strings 
    '''

    name_label = util.get_jw_category(jellyfish.jaro_winkler(row.iloc[0],
                                                             row.iloc[3]))
    address_label = util.get_jw_category(jellyfish.jaro_winkler(row.iloc[1],
                                                                row.iloc[4]))
    city_label = util.get_jw_category(jellyfish.jaro_winkler(row.iloc[2],
                                                             row.iloc[5]))

    return (name_label, city_label, address_label)


def count_tuple_probabilities(df, tuple_possibilities):
    '''
    Takes a dataframe that matches restaurants from zagat
    and fodors, and calculate the relative frequencies
    of tuples that correspond to the pairs in the dataframe

    Inputs:
        - df (pd df): dataframe consisting of zagat
            and fodors restaurant pairings
        - tuple_possibilities (list of tuples): list of all possible 
            combinations of similarity levels tuple

    Returns:
        - dictionary that maps the 27 tuples to its relative frequency
    '''

    tuple_count = {tup: 0 for tup in tuple_possibilities}
    for _, row in df.iterrows():
        tuple_score = get_tuple_score(row)
        tuple_count[tuple_score] += 1

    return {tup: count/len(df) for tup, count in tuple_count.items()}


def sort_tuples(mw, uw, leftover_tuples):
    '''
    Sorts tuples by how likely it is to be associated with a match

    Inputs:
        - mw (dict): dictionary of probabilities given match
        - uw (dict): dictionary of probabilities given unmatch
        - leftover_tuples (list): list of tuples, with those not appearing
            in both match and unmmatch dataset removed

    Returns: list of sorted tuples
    '''

    sorted_tuples = []
    ratios = {}

    for tup in leftover_tuples:
        if uw[tup] == 0:
            sorted_tuples.append(tup)
        else:
            ratio = mw[tup] / uw[tup]
            ratios[tup] = ratio

    sorted_ratios = [tup for tup, _ in sorted(ratios.items(), reverse=True,
                                              key=lambda item: item[1])]
    sorted_tuples += sorted_ratios

    return sorted_tuples


def assign_match(uw, sorted_tuples, mu, assignment):
    '''
    Assigns tuples that correspond to matches

    Inputs:
        - uw (dict): dictionary of probabilities given unmatch
        - sorted_tuples (list): list of sorted tuples
        - mu (float): maximum false positive rate
        - assignment (dict): the dictionary that stores the sets

    Returns: None, modifies assignment dict in place
    '''

    cumsum = 0
    for tup in sorted_tuples:
        cumsum += uw[tup]
        if cumsum <= mu:
            assignment['match_tuples'].add(tup)
        else:
            break


def assign_unmatch(mw, sorted_tuples, lambda_, assignment):
    '''
    Assigns tuples that correspond to unmatches

    Inputs:
        - mw (dict): dictionary of probabilities given match
        - sorted_tuples (list): list of sorted tuples
        - lambda_ (float): maximum false negative rate
        - assignment (dict): the dictionary that stores the sets

    Returns: None, modifies assignment dict in place
    '''

    cumsum = 0
    for tup in reversed(sorted_tuples):
        cumsum += mw[tup]
        if (cumsum <= lambda_) and (tup not in assignment['match_tuples']):
            assignment['unmatch_tuples'].add(tup)
        else:
            break


def assign_additional_possible(sorted_tuples, assignment):
    '''
    Assigns unassigned tuples to possible_tuples

    Inputs:
        - sorted_tuples (list): the list of sorted tuples
        - assignment (dict): the dictionary that stores the sets

    Returns: None, modifies assignment dict in place
    '''

    for tup in sorted_tuples:
        if (tup not in assignment["match_tuples"] and
                tup not in assignment["unmatch_tuples"]):
            assignment["possible_tuples"].add(tup)


def assign_tuples(mw, uw, tuple_possibilities, mu, lambda_):
    '''
    Assign tuples to 3 sets: match, unmatch and possible_matches

    Inputs:
        - mw (dict): dictionary of probabilities given match
        - uw (dict): dictionary of probabilities given unmatch
        - tuple_possibilities (list): list of all possible tuples
        - mu (float): maximum false positive rate
        - lambda_ (float): maximum false negative rate

    Returns: dictionary that maps a string to set of tuples
    '''

    assignment = {"match_tuples": set(), "unmatch_tuples": set(),
                  "possible_tuples": set()}
    leftover_tuples = tuple_possibilities[:]

    for tup in tuple_possibilities:
        if (mw[tup] == 0) and (uw[tup] == 0):
            assignment["possible_tuples"].add(tup)
            leftover_tuples.remove(tup)

    sorted_tuples = sort_tuples(mw, uw, leftover_tuples)

    assign_match(uw, sorted_tuples, mu, assignment)
    assign_unmatch(mw, sorted_tuples, lambda_, assignment)
    assign_additional_possible(sorted_tuples, assignment)

    return assignment


def update_indices(indices, index_zagat, index_fodors, row_zagat,
                   row_fodors, assignment):
    '''
    Updates the dictionary that stores the index that corresponds
    to each of the three output dataframes

    Inputs:
        - indices (dict): the index dictionary
        - index_zagat (int): the row index of the zagat row
        - index_fodors (int): the row index of the fodors row
        - row_zagat (pd series): a row from the zagat dataset
        - row_fodors (pd series): a row from the fodors dataset
        - assignment (dict): dictionary storing the 3 sets of tuples

    Returns: None, modifies indices dictionary in place
    '''

    row = pd.concat([row_zagat, row_fodors])
    tuple_score = get_tuple_score(row)

    if tuple_score in assignment["match_tuples"]:
        indices["match_zagat"].append(index_zagat)
        indices["match_fodors"].append(index_fodors)
    elif tuple_score in assignment["unmatch_tuples"]:
        indices["unmatch_zagat"].append(index_zagat)
        indices["unmatch_fodors"].append(index_fodors)
    else:
        indices["possible_zagat"].append(index_zagat)
        indices["possible_fodors"].append(index_fodors)


def generate_df(zagat, fodors, zagat_key, fodors_key, indices):
    '''
    Given the appropriate key to the indices dictionary, 
    generates the output dataframe by slicing the original 
    zagat and fodors dataframes using the appropriate indices, 
    and joining them

    Inputs:
        - zagat (pd df): the zagat dataframe
        - fodors (pd df): the fodor dataframe
        - zagat_key (str): the zagat key for indices dict
        - fodors_key (str): the fodors key for indices dict
        - indices (dict): the index dictionary

    Returns: final output dataframe
    '''

    df = zagat.iloc[indices[zagat_key]].reset_index(drop=True).join(
        fodors.iloc[indices[fodors_key]].reset_index(drop=True),
        lsuffix='_zagat', rsuffix='_fodors')

    return df


def apply_model(zagat, fodors, assignment, block_on_city):
    '''
    Iterate through every pair in zagat and fodors to create 
    three DataFrames of matches: possible matches, and unmatches

    Inputs:
        - zagat (pd df): the zagat dataframe
        - fodors (pd df): the fodor dataframe
        - assignment (dict): dictionary storing the 3 sets of tuples
        - block_on_city (boolean): True if dataframe merged on city,
            False otherwise

    Returns: tuple of three dataframes
    '''

    indices = {"match_zagat": [], "match_fodors": [], "unmatch_zagat": [],
               "unmatch_fodors": [], "possible_zagat": [],
               "possible_fodors": []}

    for index_zagat, row_zagat in zagat.iterrows():
        for index_fodors, row_fodors in fodors.iterrows():
            if block_on_city:
                if row_zagat['city'] == row_fodors['city']:
                    update_indices(indices, index_zagat, index_fodors,
                                   row_zagat, row_fodors, assignment)
            else:
                update_indices(indices, index_zagat, index_fodors,
                               row_zagat, row_fodors, assignment)

    matches = generate_df(zagat, fodors, "match_zagat", "match_fodors",
                          indices)

    possible_matches = generate_df(zagat, fodors, "possible_zagat",
                                   "possible_fodors", indices)

    unmatches = generate_df(zagat, fodors, "unmatch_zagat", "unmatch_fodors",
                            indices)

    return (matches, possible_matches, unmatches)


def find_matches(mu, lambda_, block_on_city=False):
    '''
    Loads the zagat and fodor restaurant data. Train model on
    sample unmatch and match datasets. Apply model to all the
    zagat and fodor restaurant dataset.

    Inputs: 
        - mu (float): maximum false positive rate
        - lambda_ (float): maximum false negative rate
        - block_on_city (boolean): True if dataframe merged on city,
            False otherwise

    Returns: tuple of three dataframes
    '''

    # Data
    zagat, fodors, known_links = load_data()
    matches, unmatches = get_match_and_unmatch(zagat, fodors, known_links)

    # Training
    tuple_possibilities = generate_all_possible_tuples()
    mw = count_tuple_probabilities(matches, tuple_possibilities)
    uw = count_tuple_probabilities(unmatches, tuple_possibilities)
    assignment = assign_tuples(mw, uw, tuple_possibilities, mu, lambda_)

    # Applying
    return apply_model(zagat, fodors, assignment, block_on_city)


if __name__ == '__main__':
    matches, possibles, unmatches = \
        find_matches(0.005, 0.005, block_on_city=False)

    print("Found {} matches, {} possible matches, and {} "
          "unmatches with no blocking.".format(matches.shape[0],
                                               possibles.shape[0],
                                               unmatches.shape[0]))
