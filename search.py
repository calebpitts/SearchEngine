import pandas as pd
import os
from pathlib import Path
from collections import defaultdict
from bs4 import BeautifulSoup
import re


def prompt_query():
    ''' Prompts user for seach query
    '''
    # Later add ability for user to specify that they want to look at history?
    query = input("What would you like to search? ")

    return query


def get_tokens(line):
    ''' Returns tokens from raw line parameter
    '''
    tokens = []
    for word in line.split():
        parts = re.split('[^a-zA-Z0-9]', word)  # Splits at non alphanumeric characters
        for part in parts:
            if len(part) > 0:  # Check whether it is not an empty string

                tokens.append(part.lower())

    return tokens


def compute_token_freqs(subdir_content):
    ''' Opens file path and computes the word frequencies in file by
        adding 1 to the token's assoicated value every time a token matches a key.
        Returns number of times each unique token appears in subdir content
    '''
    word_freqs = defaultdict(int)
    tokens = get_tokens(subdir_content)

    for token in tokens:

        word_freqs[token] += 1

    return word_freqs


# def updated_index(subdir_content, search_info):
#     ''' Opens file path and computes the word frequencies in file by
#         adding 1 to the token's assoicated value every time a token matches a key.
#         Returns number of times each unique token appears in subdir content
#     '''
#     tokens = get_tokens(subdir_content)

#     for token in tokens:
#         word_freqs[token] += 1
#         # print("num_unique: {} query_freq: {}".format(unique_count, query_freq))
#         token_freq = token_freqs[token]
#         num_unique_tokens = len(token_freqs.keys())
#         url = get_url(subdir, main_root, docid)

#                     #print("Query found!")
#                     #print("token:", query)
#                     #print("docid:", docid)
#                     #print("num_unique: {} query_freq: {}".format(unique_count, query_freq))
#                     #print("url:", url)
#                     search_info.append({"token": token, "docid": docid, "num_unique_on_page": num_unique_tokens, "token_freq": token_freq, "url": url})


#     return word_freqs

def get_url(subdir, main_root, docid):
    ''' Gets the subdirectory's corresponding url where query was found
    '''
    url_index_filename = 'bookkeeping.tsv'
    with open(main_root + '/' + url_index_filename, 'r') as file:
        for line in file:
            line_parts = line.split("\t")  # [subdir id, link]
            if docid == line_parts[0]:
                return line_parts[1].strip("\n")

    return "NA"


def extract_content(subdir):
    if "." not in subdir:
        with open(subdir, "r") as myfile:
            filedata = myfile.read()

        soup = BeautifulSoup(filedata, 'lxml')

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    else:
        return ""


def traverse_all_files(main_root, query):
    num_files_visited = 0
    search_info = []

    for root, dirs, files in os.walk(main_root):
        for file in files:
            subdir = os.path.join(root, file)
            docid = "/".join(subdir.split("/")[-2:])
            subdir_content = extract_content(subdir)

            if subdir_content != "":
                token_freqs = compute_token_freqs(subdir_content)
                url = get_url(subdir, main_root, docid)

                for token in list(token_freqs.keys()):
                    token_freq = token_freqs[token]
                    num_unique_tokens = len(token_freqs.keys())
                    #pd.DataFrame([{'a': [1, 2, 3, 4, 5, 6, 7, 8, 9]}, {'a': [1, 2, 3, 4, 5, 6, 7, 8, 9]}])
                    search_info.append({"token": token, "docid": str([docid, docid]), "num_unique_on_page": num_unique_tokens, "token_freq": token_freq, "url": url})

            num_files_visited += 1
            # if num_files_visited > 10:
            #     return search_info
            print("=== ", num_files_visited, " ===")

    print("Number of files traversed: {}".format(num_files_visited))
    return search_info


def get_search_info(query):
    ''' Collects all relevant search info on the query.
        Returns: List of dicts where each dict's keys are the col names and
                 each dict's values is the info associated with that key. The
                 list of dicts prepresent the rows of teh dataframe where each
                 row corresponds to a file found in the corpus.
    '''
    ROOT = '/Users/CalebPitts/Documents/Files/School/College/18-19-Year/Winter Quarter/COMPSCI 121/Homework/hw3/WEBPAGES_RAW'
    search_info = traverse_all_files(ROOT, query)

    return search_info


def format_search_info(search_info):
    ''' Puts list of dicts into pandas dataframe and creates a primary key column identifier
        where col 'search_id' is a concatanation of the search query and the docid where the
        query was found.
    '''
    search_df = pd.DataFrame(search_info)  # Converts search info into a pandas dataframe
    search_df = search_df.astype('object')
    search_df['search_id'] = search_df['token'].astype(str) + search_df['docid']  # concatanates two cols into one identifying string EX: 'Irvine' + 0/1' = 'Irvine0/1'
    cols = search_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index('search_id')))  # moving search_id to first col
    search_df = search_df.reindex(columns=cols)

    return search_df


def display_results(search_df, query):
    ''' Displays link results in increments of 10
    '''
    print("\n== Showing results for '{}' ==".format(query))

    threshold = 10  # Number of results displayed on first page of results
    for count, link in enumerate(list(search_df['url'])):  # sort relavent links later
        if count == threshold:
            cont = input("Would you like to see more results? ([y]/n): ").upper().strip()
            if cont == "Y":
                print(link)
                threshold += 10
            else:
                return
        else:
            print(link)  # later print out any other related info about the link here

    print("Reached end of relavant results.")  # If user wants 10 more queries but there aren't anymore, then this messages is displayed to console


def prompt_restart():
    ''' Prompts user if they would like to make another search query.
    '''
    restart_input = input("\nWould you like to make another query? ([y]/n): ").upper().strip()
    if restart_input == "Y":
        return True
    else:
        print("Goodbye!")
        return False


def main():
    restart = True
    while restart:
        query = prompt_query()

        search_info = get_search_info(query)
        search_df = format_search_info(search_info)
        # need to order/filter search results later...

        display_results(search_df, query)
        restart = prompt_restart()

    print(search_df)  # REMOVE LATER. TESTING ONLY FOR P1
    return search_df


if __name__ == '__main__':
    main()
