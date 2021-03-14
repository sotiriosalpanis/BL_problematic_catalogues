import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import os
import re

print("Welcome to the Cataloguers Friend application, please wait while it loads\n")
# xml export from IAMS containing all catalogue records with the BL/QFP project tag.
cat_records = 'Qatar archive description records 2019-12-11.xml'

# Based on the list created by the Tropenmuseum and detailed in 'Words Matter' pdf and augmented with terms collected by the BL/QFP team.
problematic_list = ["Aboriginal","Allochtoon","Barbarian","Banyan","Banyan Merchant","Berber","Black","Blank",
                    "Bombay","Bush Negro","Caucasian","Colored","Coolie","Descent","Disabled","Discover",
                    "Dwarf","Eskimo","Ethnicity","Exotic","Galla","Gay","Gypsy","Half-blood","Headhunter",
                    "Hermaphrodite","Homosexual","Hottentot","Inboorling","Indian","Indigenous","Indisch","Indo",
                    "Jappenkampen","Kaffir","Maroon","Medicine Man","Mohammedan","Mongoloid","Moor","Mulatto",
                    "Native","Negro","Oriental","Politionele actie","Primitive","Pygmy","Queer","Race","Roots",
                    "Servant","Slave","Third World","Traditional","Trans","Tribe","Western","White","Hawala","Holis",
                    "Hoola","Lascars","Hooli","Sepoy","Indian Mutiny","Riots","Imperial","Arab"]

woke_list = ["racist","offensive","racism","graphic",'disturbing',"upsetting","sensitive","racialised",'insulting']


def user_search_choice(search_terms):
    flag = False
    while flag == False:
        for term in search_terms:
            print(search_terms.index(term)+1, term)
        print("Input the number of the term you'd like to analyse, or enter 0 to search a term not on the list ")
        search_term_index = input()
        if int(search_term_index) == 0:
            search_term  = input("What term would you like to search for? ")
            flag = True
        elif int(search_term_index) <= len(search_terms):
            search_term = search_terms[int(search_term_index) -1]
            flag = True
        else:
            print("Sorry {0} is not in range, please try again".format(search_term_index))
            flag = False
    return search_term

def false_positive_list_builder():
    false_positive_list = []
    flag = False
    while flag == False:
        false_postive = input("Please enter a false positive term that you'd like to exclude from your results \n(leave blank to continue) ")
        if false_postive != '':
            false_positive_list.append(false_postive)
            print("The list has the following entries {0}".format(false_positive_list))
            print('It currently has {0} entries'.format(len(false_positive_list)))
            flag = False
        else:
            flag = True
    return false_positive_list


def search_term_builder(term_list):
    term_list = sorted(term_list)
    search_term_list = []
    flag = False
    while flag == False:
        for term in term_list:
            print(term_list.index(term)+1,term)
        if len(search_term_list) > 0:
            print('Already added to the list of terms to search: {0}'.format(search_term_list))
        search_term_index = input("Input the number of the term you'd like to search for, or enter 0 to add a search term not on the list.\n(leave blank to continue) ")
        if search_term_index == '':
            flag = True
        elif int(search_term_index) == 0: 
            search_term  = input("What term would you like to search for? ")
            search_term_list.append(search_term)
        elif int(search_term_index) <= len(term_list):
            search_term = term_list[int(search_term_index) -1]
            search_term_list.append(search_term)
            term_list.remove(search_term)

        else:
            print("Sorry {0} is not in range, please try again".format(search_term_index))
    return search_term_list


def term_padder(search_term,string_to_search,padding):
    match_index = string_to_search.find(search_term)
    if match_index != -1:
        front_padding = max(match_index-padding,0)
        end_padding = len(search_term) + match_index + padding
        return "'{0}'".format(string_to_search[front_padding:end_padding])
    else:
        return ''

def pandas_read_catalogue(xml_file,search_terms):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    df_cols =["Shelfmark Reference",'Start Date','End Date','ScopeContent','Padded term']
    reference_list = [reference.text for reference in root.iter('Reference')]
    start_date_list = [start_date.text for start_date in root.iter('StartDate')]
    end_date_list = [end_date.text for end_date in root.iter('EndDate')]
    scope_content_list = [ET.tostring(scope_content,encoding='utf8').decode('utf8') for scope_content in root.iter('ScopeContent')]
    
    string_match_list = [[1 if term.casefold() in scope_content.casefold() else 0 for term in search_terms ] for scope_content in scope_content_list]
    space_match_list = [[1 if " {0} ".format(term.casefold()) in scope_content.casefold() else 0 for term in search_terms ] for scope_content in scope_content_list]
    leading_space_list = [[1 if " {0}".format(term.casefold()) in scope_content.casefold() else 0 for term in search_terms ] for scope_content in scope_content_list]
    treated_match_list = [[1 if "'{0}'".format(term.casefold()) in scope_content.casefold() else 0 for term in search_terms ] for scope_content in scope_content_list]
    
    padded_term_list = [[term_padder(term.casefold(),scope_content.casefold(),50) for term in search_terms if term.casefold() in scope_content.casefold()] for scope_content in scope_content_list]
    
    rows = zip(reference_list,start_date_list,end_date_list,scope_content_list,padded_term_list)
    
    
    catalogue_df = pd.DataFrame(string_match_list, columns = search_terms).add_prefix('String-')
    catalogue_df = pd.DataFrame(space_match_list, columns = search_terms).add_prefix('Space-').join(catalogue_df,how ='right')
    catalogue_df = pd.DataFrame(leading_space_list, columns = search_terms).add_prefix('Leading Space-').join(catalogue_df,how ='right')    
    catalogue_df = pd.DataFrame(treated_match_list, columns = search_terms).add_prefix('Treated-').join(catalogue_df,how ='right')
    catalogue_df = pd.DataFrame(rows, columns = df_cols).join(catalogue_df,how ='right')
    
    return catalogue_df



# catalogue_df = pandas_read_catalogue(cat_records,problematic_list)

# string_columns = ['String-{0}'.format(column) for column in problematic_list]
# string_df = catalogue_df[string_columns]
# string_df = string_df.sum()
# string_df.to_excel('String Sum.xlsx')


# space_columns = ['Space-{0}'.format(column) for column in problematic_list]
# space_df = catalogue_df[space_columns]
# space_df  = space_df .sum()
# space_df.to_excel('Space Sum.xlsx')

# lead_space_columns = ['Leading Space-{0}'.format(column) for column in problematic_list]
# lead_space_df = catalogue_df[lead_space_columns]
# lead_space_df = lead_space_df .sum()
# lead_space_df.to_excel('Leading Space Sum.xlsx')

# treated_columns = ['Treated-{0}'.format(column) for column in problematic_list]
# treated_df = catalogue_df[treated_columns]
# treated_df = treated_df.sum()
# treated_df.to_excel('Treated Sum.xlsx')

def regex_search(search_term,search_string):
    search_regex = re.compile(r'\W{0}\W'.format(search_term))
    return len(search_regex.findall(search_string.casefold()))

def cataloguers_friend(xml_file,search_terms):
    search_term_list  = search_term_builder(search_terms)
    
    date_time = str(datetime.now()).split('.')[0]
    date_time = date_time.replace(' ', '_')
    date_time = date_time.replace(':', '-')
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    df_cols =["Shelfmark Reference",'ScopeContent','Padded term']
    reference_list = [reference.text for reference in root.iter('Reference')]
    scope_content_list = [ET.tostring(scope_content,encoding='utf8').decode('utf8') for scope_content in root.iter('ScopeContent')]
    treated_match_list = [[1 if "'{0}'".format(search_term.casefold()) in scope_content.casefold() else 0 for search_term in search_term_list] for scope_content in scope_content_list]
    
    regex_list = [[1 if regex_search(search_term.casefold(),scope_content.casefold()) > 0 else 0 for search_term in search_term_list] for scope_content in scope_content_list]
    padded_term_list = [[term_padder(search_term.casefold(),scope_content.casefold(),50) if search_term.casefold() in scope_content.casefold() else ''  for search_term in search_term_list] for scope_content in scope_content_list]
    rows = zip(reference_list,scope_content_list,padded_term_list)
    
    catalogue_df = pd.DataFrame(regex_list, columns = search_term_list).add_prefix('String-')    
    catalogue_df['String sum'] = catalogue_df.sum(axis=1)
    catalogue_df = pd.DataFrame(treated_match_list, columns = search_term_list).add_prefix('Treated-').join(catalogue_df,how ='right')
    catalogue_df = pd.DataFrame(rows, columns = df_cols).join(catalogue_df,how ='right')
    
    
    print('There are {0} direct string matches for {1}'.format(catalogue_df['String sum'].sum(),search_term_list))
    false_positive_terms = false_positive_list_builder()
    
    if len(false_positive_terms) != 0:
        false_positive_list = [[1 if false_positive.casefold() in scope_content.casefold() else 0  for false_positive in false_positive_terms] for scope_content in scope_content_list] 
        catalogue_df = pd.DataFrame(false_positive_list, columns = false_positive_terms).add_prefix('False Positive-').join(catalogue_df,how ='right')
        for false_positive_term in false_positive_terms:
            catalogue_df = catalogue_df[(catalogue_df['False Positive-{0}'.format(false_positive_term)] == 0) & (catalogue_df['String sum'] > 0)]
            catalogue_df = catalogue_df.drop(columns='False Positive-{0}'.format(false_positive_term))
    else:
        catalogue_df = catalogue_df[catalogue_df['String sum'] > 0]
    
    search_df = pd.DataFrame(search_term_list, columns =['Search terms'])
    search_df = pd.DataFrame(false_positive_terms, columns = ['Exluded terms']).join(search_df,how='right')
    search_df = search_df.set_index('Search terms')
    
    catalogue_df = catalogue_df.drop(columns='String sum')
    catalogue_df = catalogue_df.set_index("Shelfmark Reference")
    excel_name = 'CatFriend_{0}_{1}.xlsx'.format(search_term_list[0],date_time)

    with pd.ExcelWriter(excel_name) as writer:
        catalogue_df.to_excel(writer,sheet_name='Results')
        search_df.to_excel(writer,sheet_name='Search + excluded terms')
    print('{0} has been created and saved here-{1}'.format(excel_name,os.getcwd()))
    return catalogue_df

cataloguers_friend(cat_records, problematic_list)

# def cataloguers_friend(xml_file,search_terms):
#     search_term_list  = search_term_builder(search_terms)
    
#     date_time = str(datetime.now()).split('.')[0]
#     date_time = date_time.replace(' ', '_')
#     date_time = date_time.replace(':', '-')
    
#     tree = ET.parse(xml_file)
#     root = tree.getroot()
#     df_cols =["Shelfmark Reference",'ScopeContent','Padded term']
#     reference_list = [reference.text for reference in root.iter('Reference')]
#     scope_content_list = [ET.tostring(scope_content,encoding='utf8').decode('utf8') for scope_content in root.iter('ScopeContent')]
#     string_match_list = [[1 if search_term.casefold() in scope_content.casefold() else 0 for search_term in search_term_list] for scope_content in scope_content_list]
#     space_match_list = [[1 if " {0} ".format(search_term.casefold()) in scope_content.casefold() else 0 for search_term in search_term_list] for scope_content in scope_content_list]
#     leading_space_list = [[1 if " {0}".format(search_term.casefold()) in scope_content.casefold() else 0 for search_term in search_term_list] for scope_content in scope_content_list]
#     treated_match_list = [[1 if "'{0}'".format(search_term.casefold()) in scope_content.casefold() else 0 for search_term in search_term_list] for scope_content in scope_content_list]

#     padded_term_list = [[term_padder(search_term.casefold(),scope_content.casefold(),50) if search_term.casefold() in scope_content.casefold() else ''  for search_term in search_term_list] for scope_content in scope_content_list]
#     rows = zip(reference_list,scope_content_list,padded_term_list)
    
#     catalogue_df = pd.DataFrame(string_match_list, columns = search_term_list).add_prefix('String-')
#     catalogue_df['String sum'] = catalogue_df.sum(axis=1)
#     catalogue_df = pd.DataFrame(treated_match_list, columns = search_term_list).add_prefix('Treated-').join(catalogue_df,how ='right')
#     catalogue_df = pd.DataFrame(leading_space_list, columns = search_term_list).add_prefix('Leading space-').join(catalogue_df,how ='right')
#     catalogue_df = pd.DataFrame(space_match_list, columns = search_term_list).add_prefix('Space-').join(catalogue_df,how ='right')
#     catalogue_df = pd.DataFrame(rows, columns = df_cols).join(catalogue_df,how ='right')
    
    
#     print('There are {0} direct string matches for {1}'.format(catalogue_df['String sum'].sum(),search_term_list))
#     false_positive_terms = false_positive_list_builder()
    
#     if len(false_positive_terms) != 0:
#         false_positive_list = [[1 if false_positive.casefold() in scope_content.casefold() else 0  for false_positive in false_positive_terms] for scope_content in scope_content_list] 
#         catalogue_df = pd.DataFrame(false_positive_list, columns = false_positive_terms).add_prefix('False Positive-').join(catalogue_df,how ='right')
#         for false_positive_term in false_positive_terms:
#             catalogue_df = catalogue_df[(catalogue_df['False Positive-{0}'.format(false_positive_term)] == 0) & (catalogue_df['String sum'] > 0)]
#             catalogue_df = catalogue_df.drop(columns='False Positive-{0}'.format(false_positive_term))
#     else:
#         catalogue_df = catalogue_df[catalogue_df['String sum'] > 0]
    
#     search_df = pd.DataFrame(search_term_list, columns =['Search terms'])
#     search_df = pd.DataFrame(false_positive_terms, columns = ['Exluded terms']).join(search_df,how='right')
#     search_df = search_df.set_index('Search terms')
    
#     catalogue_df = catalogue_df.drop(columns='String sum')
#     catalogue_df = catalogue_df.set_index("Shelfmark Reference")
#     excel_name = 'CatFriend_{0}_{1}.xlsx'.format(search_term_list[0],date_time)

#     with pd.ExcelWriter(excel_name) as writer:
#         catalogue_df.to_excel(writer,sheet_name='Results')
#         search_df.to_excel(writer,sheet_name='Search + excluded terms')
#     print('{0} has been created and saved here-{1}'.format(excel_name,os.getcwd()))
#     return catalogue_df

# cataloguers_friend(cat_records, problematic_list)


