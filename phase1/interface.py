from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()
        
    def bfs(self, start_node, last_node):
        with self._driver.session() as session:
            # TOdo:
            # Project the graph
            session.run("""
                CALL gds.graph.project(
                    'tripGraph',
                    'Location',
                    'TRIP'
                )
            """)

            # Run BFS from start_node to last_node
            result = session.run("""
                MATCH (source:Location {name: $start}), (target:Location {name: $end})
                CALL gds.bfs.stream('tripGraph', {
                    sourceNode: id(source),
                    targetNodes: [id(target)]
                })
                YIELD path
                RETURN [node in nodes(path) | node { .name }] AS path
            """, start=start_node, end=last_node)

            data = result.data()
            session.run("CALL gds.graph.drop('tripGraph') YIELD graphName")

            return data

    def pagerank(self, max_iterations, weight_property):
        with self._driver.session() as session:
            #todo part: 
            session.run("""
                CALL gds.graph.project(
                    'locationGraph',
                    'Location',
                    {
                        TRIP: {
                            properties: $weight_prop
                        }
                    }
                )
            """, weight_prop=weight_property)

            # Run PageRank
            result = session.run("""
                CALL gds.pageRank.stream('locationGraph', {
                    maxIterations: $max_iterations,
                    relationshipWeightProperty: $weight_prop
                })
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
                ORDER BY score DESC
            """, max_iterations=max_iterations, weight_prop=weight_property)

            data = result.data()
            session.run("CALL gds.graph.drop('locationGraph') YIELD graphName")

            return [{"name": int(row["name"]), "score": row["score"]} for row in [data[0], data[-1]]]