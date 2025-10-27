# takes in the csv file, then clears the neo4j databse before adding the nodes and edges
from py2neo import Graph, Node, Relationship
import pandas as pd
import os
import itertools

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASS", "password")

graph = Graph(uri, auth=(user, password))

# Optional: clear database
graph.run("MATCH (n) DETACH DELETE n")

# Load the big CSV
csv_path = os.path.join(os.getcwd(), "datasets", "all_leagues_combined.csv")
df = pd.read_csv(csv_path)

# Remove duplicates
df = df.drop_duplicates(subset=["player_name", "team_name", "start_year", "end_year"])

# Replace missing ages with None
df["age"] = df["age"].apply(lambda x: int(x) if pd.notna(x) else None)

# Helper to check overlap
def overlap(s1, e1, s2, e2):
    return not (e1 < s2 or e2 < s1)

# Create nodes and PLAYED_FOR relationships
for _, row in df.iterrows():
    player = Node("Player", name=row["player_name"], age=row["age"], nationality=row["nationality"])
    team = Node("Team", name=row["team_name"])
    graph.merge(player, "Player", "name")
    graph.merge(team, "Team", "name")

    rel = Relationship(player, "PLAYED_FOR", team,
                       start_year=int(row["start_year"]),
                       end_year=int(row["end_year"]),
                       league=row["league_name"])
    graph.merge(rel)

# Create PLAYED_WITH edges between overlapping teammates
for team, group in df.groupby("team_name"):
    players = group.to_dict("records")
    for p1, p2 in itertools.combinations(players, 2):
        if overlap(p1["start_year"], p1["end_year"], p2["start_year"], p2["end_year"]):
            graph.run("""
                MATCH (a:Player {name: $p1_name})
                MATCH (b:Player {name: $p2_name})
                MERGE (a)-[r:PLAYED_WITH {team: $team}]->(b)
            """, p1_name=p1["player_name"], p2_name=p2["player_name"], team=team)


print("All data loaded into Neo4j!")
