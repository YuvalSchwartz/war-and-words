import pickle


def save_pickle(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)