from argparse import ArgumentParser
import csv
import re
import requests
import os
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict
import pprint
#import util

## Utility functions
def write_list(l,file_path, header= True, initial_pos= 0):
    f = open(file_path,"w+")

    if len(l) > 0:
        #header
        if header:
            str_header = ''
            for k_header in l[0].keys():
                str_header = str_header + str(k_header) + ","
            f.write(str_header[:-1]+"\n")

        #content
        for l_index in range(initial_pos,len(l)):
            str_row = ''
            for k_att in l[l_index]:
                str_row = str_row + '"'+str(l[l_index][k_att]) +'"'+','
            f.write(str_row[:-1]+"\n")
    else:
        f.write("")
def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
def df_to_dict_list(a_df, extra_keys = {}, fields = []):
    l = []
    for index, row in a_df.iterrows():

        dict_elem = {}
        for k_field in fields:
            if k_field in row:
                dict_elem[k_field] = row[k_field]

        l.append(merge_two_dicts(dict_elem, extra_keys))
    return l
## ------------------------------------
## ------------------------------------


class Method:
    def __init__(self):
        self.STEPS = {
            "0": {"title":"Before start", "description":"Define the directory of the workflow output", "input":"The directory of the methodology outputs *OPTIONAL*", "output":""},
            "1": {"title":"Identifying and retrieving the resources", "description":"Identifying the list of entities citing the retracted article and annotating their main attributes", "input":"Retracted article DOI", "output":"Creates the Cits_Dataset with the initial variables: <doi>, <title>, <year>, <source_id>, <source_title>"},
            "2": {"title":"Annotating the citing entities characteristics", "description":"Annotating whether the citing entities are/aren’t retracted", "input":"Citing entities DOIs", "output":"Extends the Cits_Dataset with the new <is_retracted> variable"},
            "3": {"title":"Classifying the citing entities into subjects of study", "description":"Classifying the citing entities macro subjects and specific areas of study following the SCImago classification", "input":"Citing entities ISSN/ISBN values", "output":"Extends the Cits_Dataset with the new variables: <area>, and <category>"},
            "4": {"title":"", "description":"", "input":"", "output":""},
            "5": {"title":"", "description":"", "input":"", "output":""}
        }

    def handle_step(self, step, input, output):

        def step_1(sub_step, input, output):

            def init_dataset():
                #Define the output Directory
                try:
                    if not os.path.exists(output):
                        os.makedirs(output)
                    return output + "/cits_dataset.csv"
                except Exception as e:
                    print("Error: invalid output directory")

            if sub_step == 1:
                print("Step-1.1 Done: This substep does not have any code to run")
                return True
            if sub_step == 2:

                def call_api_coci(operation, vals, fields, params=""):
                    COCI_API = "https://opencitations.net/index/coci/api/v1/"
                    if len(vals) == 0:
                        return {}

                    val_key = vals.pop(0)
                    item = {}
                    item[val_key] = {}
                    r = requests.get(COCI_API + str(operation) + "/" + str(val_key) + str(params))
                    if len(r.json()) > 0:
                        if fields == "*":
                            item[val_key] = r.json()[0]
                        else:
                            for f in fields:
                                item[val_key][f] = None
                                if f in r.json()[0]:
                                    item[val_key][f] = r.json()[0][f]

                    return merge_two_dicts(item, call_api_coci(operation, vals, fields, params))

                CITS_DATASET = init_dataset()

                RET_ART_DOI = None
                if (re.compile("10\.\d{4,9}\/.*").match(str(input))):
                    RET_ART_DOI = input.strip()

                if RET_ART_DOI == None:
                    print("Error: please enter a valid DOI value as input")
                    return False

                # All the citations in COCI
                ret_meta = call_api_coci("metadata", [RET_ART_DOI],["citation"],'?json=array("; ",citation,doi)')
                coci_cits = ret_meta[RET_ART_DOI]["citation"]
                # ---- <TEST> ----- COMMENT
                # coci_cits = coci_cits[0:10]
                # ---- </TEST> ----- COMMENT

                # Get the metadata of citing document
                coci_cits_meta = call_api_coci("metadata", coci_cits, "*")

                #write the partial results of this step
                step_a_data = []
                for c in coci_cits_meta:
                    step_a_data.append({
                        "doi": coci_cits_meta[c]["doi"],
                        "title": coci_cits_meta[c]["title"],
                        "year": coci_cits_meta[c]["year"],
                        "source_id": coci_cits_meta[c]["source_id"],
                        "source_title": coci_cits_meta[c]["source_title"]
                    })

                write_list(step_a_data, CITS_DATASET, header= True)
                print("Step-1.2 Done !")
                return True

        def step_2(sub_step, input):
            if sub_step == 1:
                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False

                CITS_DATASET = input
                cits_df = pd.read_csv(CITS_DATASET)
                step_2_1_data = df_to_dict_list(cits_df,{"is_retracted":"todo"},["doi","title","year","source_id","source_title"])
                write_list(step_2_1_data, CITS_DATASET, header= True)
                print("Step-2.1 Done !")
                return True
            if sub_step == 2:
                print("Step-2.2 Done: This substep does not have any code to run")
                return True

        def step_3(sub_step, input):
            if sub_step == 1:
                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False

                CITS_DATASET = input
                cits_df = pd.read_csv(CITS_DATASET)
                ISSN_DATASET = CITS_DATASET.replace("/cits_dataset.csv","")+"/issn_dataset.csv"
                ISBN_DATASET = CITS_DATASET.replace("/cits_dataset.csv","")+"/isbn_dataset.csv"

                # ISSNs: citations having an issn value in the source id
                cits_df_issn = cits_df[cits_df["source_id"].str.contains('^issn')]
                cits_df_issn = cits_df_issn[["source_id","source_title"]].drop_duplicates(subset ="source_id", keep = 'first')
                step_3_1_data = df_to_dict_list(cits_df_issn,{"scimago_area":"todo","scimago_category":"todo"},["source_id","source_title"])
                write_list(step_3_1_data, ISSN_DATASET, header= True)

                # ISBNs: citations having an isbn value in the source id
                cits_df_isbn = cits_df[cits_df["source_id"].str.contains('^isbn')]
                cits_df_isbn = cits_df_isbn[["source_id","source_title"]].drop_duplicates(subset ="source_id", keep = 'first')
                step_3_1_data = df_to_dict_list(cits_df_isbn,{"lcc":"todo","scimago_area":"todo","scimago_category":"todo"},["source_id","source_title"])
                write_list(step_3_1_data, ISBN_DATASET, header= True)
                print("Step-3.1 Done!")
                return True
            if sub_step == 2:
                print("Step-3.2 Done: This substep does not have any code to run")
                return True
            if sub_step == 3:
                print("Step-3.3 Done: This substep does not have any code to run")
                return True
            if sub_step == 4:

                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False
                CITS_DATASET = input
                ISBN_DATASET = CITS_DATASET.replace("/cits_dataset.csv","")+"/isbn_dataset.csv"
                lcc_lookup_df = pd.read_csv("lcc_lookup.csv")
                scimago_lookup_df = pd.read_csv("scimago_lookup.csv")
                isbn_df = pd.read_csv(ISBN_DATASET)

                step_3_4_data = []
                for index, row in isbn_df.iterrows():

                    step_3_4_data.append(row.to_dict())

                    #1. Consider only the alphabetic part of the LCC code
                    alphabetic_code = re.findall('[a-zA-Z]+', row['lcc'])
                    if len(alphabetic_code) == 0:
                        print("Error: invalid LCC code '"+row['lcc']+"': doesn't start with alphabetic characters")
                        return False
                    alphabetic_code = alphabetic_code[0].upper()
                    query_df = lcc_lookup_df.loc[lcc_lookup_df['lcc_code'] == alphabetic_code]
                    lcc_subject = None
                    if len(query_df) > 0:
                        lcc_subject = query_df["lcc_subject"].values[0]
                    else:
                        print("Error: invalid LCC code '"+row['lcc']+"': not found")
                        return False

                    area = "todo_manual"
                    category = "todo_manual"
                    #2. Checks whether the value of the LCC subject is also a Scimago subject area
                    query_df = scimago_lookup_df.loc[scimago_lookup_df['area'].str.lower() == lcc_subject.lower()]
                    if len(query_df) > 0:
                        area = query_df["area"].values[0]
                        category = area + " (miscellaneous)"

                    #3. Checks whether the value of the LCC subject is also a Scimago subject category
                    else:
                        query_df = scimago_lookup_df.loc[scimago_lookup_df['category'].str.lower() == lcc_subject.lower()]
                        if len(query_df) > 0:
                            area = query_df["area"].values[0]
                            category = query_df["category"].values[0]

                    step_3_4_data[0]["scimago_area"] = area
                    step_3_4_data[0]["scimago_category"] = category

                write_list(step_3_4_data, ISBN_DATASET, header= True)
                print("Step-3.4 Done!")
                return True
            if sub_step == 5:
                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False
                CITS_DATASET = input
                ISSN_DATASET = CITS_DATASET.replace("/cits_dataset.csv","")+"/issn_dataset.csv"
                ISBN_DATASET = CITS_DATASET.replace("/cits_dataset.csv","")+"/isbn_dataset.csv"

                cits_df = pd.read_csv(CITS_DATASET)

                issn_df = pd.read_csv(ISSN_DATASET)
                for index, row in issn_df.iterrows():
                    query_df = cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower()]
                    if(len(query_df) > 0):
                        cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower(), 'area'] = row["scimago_area"]
                        cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower(), 'category'] = row["scimago_category"]

                isbn_df = pd.read_csv(ISBN_DATASET)
                for index, row in isbn_df.iterrows():
                    query_df = cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower()]
                    if(len(query_df) > 0):
                        cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower(), 'area'] = row["scimago_area"]
                        cits_df.loc[cits_df.source_id.str.lower() == row["source_id"].lower(), 'category'] = row["scimago_category"]


                step_3_5_data = cits_df.to_dict("records")
                write_list(step_3_5_data, CITS_DATASET, header= True)
                print("Step-3.5 Done!")
                return True

        def step_4(sub_step, input):
            if sub_step == 1:
                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False
                CITS_DATASET = input
                cits_df = pd.read_csv(CITS_DATASET)
                step_4_1_data = df_to_dict_list(cits_df,{"abstract":"todo","intext_citation.section":"todo","intext_citation.context":"todo","intext_citation.pointer":"todo"},["doi","title","year","source_id","source_title","is_retracted","area","category"])
                write_list(step_4_1_data, CITS_DATASET, header= True)
                print("Step-4.1 Done!")
                return True
            if sub_step == 2:
                print("Step-4.2 Done: This substep does not have any code to run")
                return True

        def step_5(sub_step, input):
            if sub_step == 1:
                if not os.path.exists(str(input)):
                    print("Error: invalid input file")
                    return False
                CITS_DATASET = input
                cits_df = pd.read_csv(CITS_DATASET)
                step_5_1_data = df_to_dict_list(
                    cits_df,
                    {"intext_citation.intent":"todo","intext_citation.sentiment":"todo","intext_citation.ret_mention":"todo"},
                    ["doi","title","year","source_id","source_title","is_retracted","area","category","abstract","intext_citation.section","intext_citation.context","intext_citation.pointer"])
                write_list(step_5_1_data, CITS_DATASET, header= True)
                print("Step-5.1 Done!")
                return True
            if sub_step == 2:
                print("Step-5.2 Done: This substep does not have any code to run")
                return True

        step_parts = step.split(".")
        if len(step_parts) > 0:
            main_step = step_parts[0]

            sub_step = step_parts[1:]
            if len(sub_step) == 0:
                step_def =  self.STEPS[main_step]
                print(step_def["title"]+"\n"+step_def["description"]+"\n"+step_def["input"]+"\n"+step_def["output"])
                return True

            command = "step_"+main_step+"("+str(sub_step[0])+",'"+str(input)+"'"
            if main_step == "1":
                command = command +",'"+str(output)+"'"
            #print("Executes: "+command+")")
            return eval(command+")")

        return "Error: please specify a step"


if __name__ == "__main__":
    arg_parser = ArgumentParser("method.py", description="A methodology for annotating the in-text citations toward a retracted article \n Starting from a seed retracted article, we present a step by step methodology for collecting and annotating the citing entities in-text citations \n This methodology is divided into 5 steps: (1) identifying and retrieving the resources, (2) annotating the citing entities characteristics, (3) classifying the citing entities into subjects of study, (4) extracting textual values from the citing entities, and (5) annotating the in-text citations characteristics.")
    arg_parser.add_argument("-s", "--step", dest="step", required=True, help="The step of the methodology. E.g. 2 or 3.1")
    arg_parser.add_argument("-in", "--input", dest="input", default="-1", required=False, help="The input of the step")
    arg_parser.add_argument("-out", "--output", dest="output", default="output_data", required=False, help="The output directory where the results will be stored")

    args = arg_parser.parse_args()

    method = Method()
    method.handle_step(args.step, args.input, args.output)
