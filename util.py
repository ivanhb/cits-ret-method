#!/usr/bin/env python
# coding: utf-8

# In[ ]:


## Usefull functions
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
    
    #if len(l) == 0:
    #    header = {}
    #    for k_field in fields:
    #        header[k_field] = ""
    #    l.append(merge_two_dicts(header, extra_keys))
        
    return l

