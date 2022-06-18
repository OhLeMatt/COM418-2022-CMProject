import pickle
import numpy as np
import pandas as pd
import copy
from music_tools.scales import *
from music_tools.utils import base_to_list, list_to_str

FOLDER = "scale_researches/"


def treat_scale_coding_jan_2011():
    df = pd.read_excel("scale_researches/ScaleCodingJan2011_Cleaned_More.xlsx")
    rotation_ids = []
    circular_distance = []
    history = {}
    rot_id_inc = 0
    rid_to_id = {}
    
    for j, id in enumerate(df.scale_id):
        b = ChromaBitmap()
        b.bitmap = id
        n = b.note_count()
        
        if n not in history:
            history[n] = {}
        if id not in history[n]:
            rotation_id = n << 12 | id
            for i in range(12):
                history[n][b.roll(i)] = rotation_id
            rid_to_id[rotation_id] = j
        rotation_ids.append(history[n][id])
        circular_distance.append(b.circular_distance(history[n][id]))
    
    df["rotation_id"] = rotation_ids
    df["circular_distance"] = circular_distance
    
    whitelist = ["major", "minor", "blues", "chromatic", "dominant", 
                 "augmented", "diminished", "suspended", "pentatonic", 
                 "enigmatic", "altered", "harmonic", "melodic", "gipsy", "neapolitan",
                 "bebop", "jazz", "rock", "tone", "diatonic", "tetratonic",
                 "japan", "greece", "spanish", "north america", "israel", "algerian", "arabia" 
                 "hungarian", "romanian", "hawaiian", "egyptian", "eskimo", "sumerian", "ethiopia"]

    blacklist = ["interval", "chord", "triad"]
    
    filtered = []
    for scale in df.itertuples():
        valid = False
        if scale.note_count > 4:
            for keyword in whitelist:
                if keyword in str(scale.name).lower() or keyword in str(scale.alt_name).lower():
                    valid = True
                    break
        if valid:
            for keyword in blacklist:
                if keyword in str(scale.name).lower() or keyword in str(scale.alt_name).lower():
                    valid = False
                    break
        if valid and scale.circular_distance != 0:
            filtered[rid_to_id[scale.rotation_id]] = True
        filtered.append(valid)
            
    filtered_df = df[filtered]

    filtered_df.to_csv("scale_researches/scale_coding_filtered.csv", index=False)
    
    cleaned_df = filtered_df.copy()
    name_is_na = pd.isna(cleaned_df.name)
    cleaned_df.loc[name_is_na, "name"] = ""  # type: ignore
    
    theory_name_is_not_na = ~pd.isna(cleaned_df.theory_name)
    cleaned_df.loc[~name_is_na & theory_name_is_not_na, "name"] += ", " # type: ignore
    cleaned_df.loc[theory_name_is_not_na, "name"] += cleaned_df.theory_name[theory_name_is_not_na] # type: ignore
    
    alt_name_is_not_na = ~pd.isna(cleaned_df.alt_name)
    cleaned_df.loc[alt_name_is_not_na, "name"] += ", " + cleaned_df.alt_name[alt_name_is_not_na] # type: ignore
    
    cleaned_df = cleaned_df[["scale_id", "scale_bits", "rotation_id", "circular_distance", "note_count", "name"]]
    cleaned_df = cleaned_df.drop_duplicates()
    cleaned_df = cleaned_df.sort_values(["rotation_id", "circular_distance"])
    cleaned_df.to_csv("scale_researches/scale_coding_cleaned.csv", index=False)
    
def create_scale_trees():
    scale_list = pd.read_csv(FOLDER + "scale_final_data.csv")
    scale_list.set_index("scale_id")
    scale_list = scale_list.sort_index(ascending=False)

    i = 0

    contained = {}
    for n_notes in scale_list.note_count.unique():
        ids = np.array(scale_list.loc[scale_list.note_count == n_notes].scale_id.astype(int)) 
        sub_ids = np.array(scale_list.loc[scale_list.note_count < n_notes].scale_id.astype(int))
        
        for id in ids:
            id = int(id)
            contained_sub_ids = sub_ids[id & sub_ids == sub_ids]
            contained[id] = contained_sub_ids.astype(int).tolist()
            print(n_notes, "-", id, ":", len(contained_sub_ids))

    out_filename = FOLDER + "scale_legacy.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(contained, outfile)
    
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
            
    out_filename = FOLDER + "scale_parents.pkl"

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

    for id in available:
        available[id] = available[id][id]
    
    scales_tree = copy.deepcopy(available[root]) 
    
    out_filename = FOLDER + "scale_tree.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(scales_tree, outfile)
    
    out_filename = FOLDER + "scale_forest.pkl"

    with open(out_filename, "wb") as outfile:
        pickle.dump(available, outfile)


if __name__ == "__main__":      
    create_scale_trees()

    