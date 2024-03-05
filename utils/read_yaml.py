import yaml

def read_yaml(yaml_file_path):
    #try:
    with open( yaml_file_path, "r",encoding="utf-8") as f:
        value = yaml.load(stream=f, Loader=yaml.FullLoader)
    #except:
        #with open(yaml_file_path, "r",encoding="gbk") as f:
            #value = yaml.load(stream=f, Loader=yaml.FullLoader)
    print(value)
    return value