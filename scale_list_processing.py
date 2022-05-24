from scales import ChromaBitmap, Scale
import pickle
import numpy as np
import pandas as pd
import copy
from utils import base_to_list


if __name__ == "__main__":    

    scale_list = pd.read_csv("scale-list.csv") 
    # scale_list.semitones = [base_to_list(x) for x in scale_list.semitones.tolist()]
    scale_list["scale_id"] = [ChromaBitmap(Scale.compute_successive_shifts(base_to_list(x))).bitmap for x in scale_list.semitones.tolist()]

    # scale_list["scale"] = [Scale(x) for x in scale_list.semitones.tolist()]
    scale_list = scale_list.sort_index(ascending=False)

    i = 0

    contained = {}
    # for n_notes in [3, 4, 5, 6, 7, 8]:
    for n_notes in scale_list.n_notes.unique():
        ids = np.array(scale_list.loc[scale_list.n_notes == n_notes].scale_id.astype(int)) 
        sub_ids = np.array(scale_list.loc[scale_list.n_notes < n_notes].scale_id.astype(int))
        
        for id in ids:
            id = int(id)
            contained_sub_ids = sub_ids[id & sub_ids == sub_ids]
            contained[id] = contained_sub_ids.astype(int).tolist()
            print(n_notes, "-", id, ":", len(contained_sub_ids))

    out_filename = "scale_legacy.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(contained, outfile)
    
    # contained = {1:[9],
    #              2:[],
    #              3:[2],
    #              4:[],
    #              5:[1,2,6,9],
    #              6:[1,9],
    #              7:[2,9],
    #              8:[1,2,3,4,5,6,7,9],
    #              9:[]}

    parents = {}


    root = None
    for id, cids in contained.items():
        valid = {}
        invalid = []
        for cid in contained.keys():
            if id in contained[cid]:
                new_invalid = [vid for vid, sids in valid.items() if cid in sids]
                invalid.extend(new_invalid)
                for i in new_invalid:
                    del valid[i]
                i = len(contained[cid]) - 1
                while i >= 0 and contained[cid][i] not in valid.keys():
                    i -= 1
                if i >= 0:
                    invalid.append(cid)
                else:
                    valid[cid] = list(contained[cid]).copy()
                    if id in valid[cid]:
                        valid[cid].remove(id)
                
        parents[id] = list(valid.keys())
        if len(parents[id]) == 0:
            root = id
            
    # out_filename = "scale_parents.json"

    # with open(out_filename, "w") as outfile:
    #     json.dump(parents, outfile)
    
    out_filename = "scale_parents.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(parents, outfile)
        
        
    scales_tree = {}
    available = {}
    for id in parents:
        available[id] = {id: {"self": id}}

    # print(parents)
    for id, id_parents in parents.items():
        for id_parent in id_parents:
            available[id_parent][id_parent][id] = available[id][id]

    scales_tree = copy.deepcopy(available[root]) 
    
    out_filename = "scale_tree.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(scales_tree, outfile)
    
    out_filename = "scale_forest.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(available, outfile)


            
