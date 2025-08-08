# This module contains functions to navigate a list of paths in its raw form,
# instead of dealing with them as nested lists in treeObjs
import re

def countMatches(  lst, regex_pattern):
    """
    Count the number of items that in the list that match the regex.
    """
    count = len( ["" for item in lst if re.search( regex_pattern, item)])
    return count 

def listMatches( lst, regex_pattern, foo = None):
    """
    Return a list of the matches for each regex expression
    Args:
    - foo (func): Defines how to format each match within the list
    """
    if foo:
        return [ foo( item ) for item in lst if re.search( regex_pattern, item)]
    else:
        return  [ item for item in lst if re.search( regex_pattern, item)]

# 
def findMatch(lst, regex_pattern, foo):
    """
    Args:
    - foo (func): This function defines how to output the result of the regex match
    """
    match = foo( lst, regex_pattern)
    return match 

def findAllMatches( lst, lst_regex_patterns, lst_names, foo):
    """
    Given a list of items and and a list of regex expressions, this function outputs for each regex a list of matches
    """
    output_dict = {}
    for regex_pattern, key in zip( lst_regex_patterns, lst_names):
        output_dict[key] = findMatch( lst, regex_pattern, foo)
    return output_dict