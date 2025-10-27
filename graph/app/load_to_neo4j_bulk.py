# load_to_neo4j.py
from py2neo import Graph, Node, Relationship
import pandas as pd
import os
import itertools

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASS", "password")

graph = Graph(uri, auth=(user, password))

print("Clearing Neo4j database...")
graph.run("MATCH (n) DETACH DELETE n")

# Load the big CSV
csv_path = os.path.join(os.getcwd(), "datasets", "all_leagues_combined.csv")
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} records from {csv_path}")

# Clean up data
df = df.drop_duplicates(subset=["player_name", "team_name", "start_year", "end_year"])
df["age"] = df["age"].apply(lambda x: int(x) if pd.notna(x) else None)

# --- 1️⃣ Create Player and Team Nodes with PLAYED_FOR relationships ---
print("Creating Player and Team nodes with PLAYED_FOR relationships...")

for _, row in df.iterrows():
    player = Node("Player", name=row["player_name"], age=row["age"], nationality=row["nationality"])
    team = Node("Team", name=row["team_name"])
    graph.merge(player, "Player", "name")
    graph.merge(team, "Team", "name")

    rel = Relationship(
        player,
        "PLAYED_FOR",
        team,
        start_year=int(row["start_year"]),
        end_year=int(row["end_year"]),
        league=row["league_name"]
    )
    graph.merge(rel)

print("Finished creating PLAYED_FOR relationships.")

# --- 2️⃣ Build teammate pairs in bulk ---
print("Building teammate pairs for bulk import...")

def overlap(s1, e1, s2, e2):
    return not (e1 < s2 or e2 < s1)

rows = []
for team, group in df.groupby("team_name"):
    players = group.to_dict("records")
    for p1, p2 in itertools.combinations(players, 2):
        if overlap(p1["start_year"], p1["end_year"], p2["start_year"], p2["end_year"]):
            rows.append((p1["player_name"], p2["player_name"], team))

pairs_path = os.path.join(os.getcwd(), "datasets", "teammates.csv")
pd.DataFrame(rows, columns=["player1", "player2", "team"]).to_csv(pairs_path, index=False)
print(f"✅ Teammate pairs CSV saved to {pairs_path}")
print(f"Total teammate pairs: {len(rows):,}")
