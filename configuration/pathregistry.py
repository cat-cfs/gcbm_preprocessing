import os, logging, json

class Node:
    def __init__(self, name):
        self.name = name
        self.edges = []
    def addEdge(self, node):
        self.edges.append(node)

class PathRegistry(object):
    def __init__(self, configPath):
        config = self.loadJson(configPath)
        self.region_name_placeholder = "{region_name}"
        if "Region_Name" in config:
            raise ValueError("Region_name is a reserved path item")
        config["Region_Name"] = [self.region_name_placeholder]

        nodes = {}
        for k,v in config.items():
            nodes[k] = Node(k)

        for k,v in config.items():
            for d in self.get_dependent_paths(v):
                if not k in nodes or not d in nodes:
                    raise ValueError("specified path reference not found '{}'"
                                     .format(k))

                nodes[k].addEdge(nodes[d])

        PathTokens = {}
        for k,v in config.items():
            if not k in PathTokens:
                resolved = []
                unresolved = []
                self.dep_resolve(nodes[k], resolved, unresolved)
                for a in resolved:
                    if a.name in PathTokens:
                        continue
                    tokens = self.sub_dependent_paths(config[a.name], PathTokens)
                    PathTokens[a.name] = tokens

        self.Paths={}
        for k,v in PathTokens.items():
            self.Paths[k] = os.path.join(*v)
            logging.debug("{k}: '{v}'".format(k=k, v= self.Paths[k]))

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def GetPath(self, name, region_path_name = None):
        if not name in self.Paths:
            raise ValueError("registered path '{0}' not present".format(name))
        path = self.Paths[name]
        if self.region_name_placeholder in path:
            if region_path_name is None:
                raise ValueError("region name must be specified for '{0}'".format(name))
            return path.format(region_name=region_path_name)
        else:
            return path

    def UnpackPath(self, path, region_path_name = None):
        if self.is_dependent_token(path):
            return self.GetPath(
               self.strip_dependent_token(path),
               region_path_name)
        else:
            return path

    def is_dependent_token(self, token):
        return token.startswith("${") and token.endswith("}")

    def strip_dependent_token(self, token):
        return token.replace("${", "").replace("}", "")

    def sub_dependent_paths(self, p_dependent, path_collection):
        tokens = []
        for t in p_dependent:
            if self.is_dependent_token(t):
                tokens.extend(path_collection[self.strip_dependent_token(t)])
            else:
                tokens.append(t)
        return tokens

    def get_dependent_paths(self, pathList):
        depNames = [x for x in pathList if self.is_dependent_token(x)]
        return [self.strip_dependent_token(x) for x in depNames]

    def dep_resolve(self, node, resolved, unresolved):
        '''
        dependency resolver algorithm copied from this article
        https://www.electricmonk.nl/docs/dependency_resolving_algorithm/dependency_resolving_algorithm.html
        '''
        unresolved.append(node)
        for edge in node.edges:
                if edge not in resolved:
                        if edge in unresolved:
                            raise Exception('Circular reference detected: %s -> %s' % (node.name, edge.name))
                        self.dep_resolve(edge, resolved, unresolved)
        resolved.append(node)
        unresolved.remove(node)