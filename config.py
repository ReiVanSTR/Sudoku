import yaml

def load_config(path):
    with open(path, 'r') as file:
        # Load the content of the file into a Python dictionary
        data = yaml.safe_load(file)

    return data