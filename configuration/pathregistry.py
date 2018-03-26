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
        path_variables = config["Path_Variables"]
        path_map = config["Paths"]

        for variable in path_variables:
            if variable in path_map:
                raise ValueError("variable and config duplicates not allowed")
            placeHolder = "{" + variable + "}"
            if not placeHolder.format(**{variable: ""}) == "":
                raise ValueError("invalid variable name {}".format(variable))
            path_map[variable] = [placeHolder]
            
        nodes = {}
        for k,v in path_map.items():
            nodes[k] = Node(k)

        for k,v in path_map.items():
            for d in self.get_dependent_paths(v):
                if not k in nodes:
                    raise ValueError("specified path reference not found '{}'"
                                     .format(k))
                if not d in nodes:
                    raise ValueError("specified path reference not found '{}'"
                                     .format(d))

                nodes[k].addEdge(nodes[d])

        PathTokens = {}
        for k,v in path_map.items():
            if not k in PathTokens:
                resolved = []
                unresolved = []
                self.dep_resolve(nodes[k], resolved, unresolved)
                for a in resolved:
                    if a.name in PathTokens:
                        continue
                    tokens = self.sub_dependent_paths(path_map[a.name], PathTokens)
                    PathTokens[a.name] = tokens

        self.Paths={}
        for k,v in PathTokens.items():
            self.Paths[k] = os.path.join(*v)
            logging.debug("{k}: '{v}'".format(k=k, v= self.Paths[k]))

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def GetPath(self, name, **kwargs):
        if not name in self.Paths:
            raise ValueError("registered path '{0}' not present".format(name))
        path = self.Paths[name]
        if kwargs:
            return path.format(**kwargs)
        else:
            return path

    def UnpackPath(self, path, **kwargs):
        if self.is_dependent_token(path):
            return self.GetPath(
               self.strip_dependent_token(path),
               **kwargs)
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