import pickle


with  open("data.pkl", "rb") as infile:
    output = pickle.load(infile)
print(output)