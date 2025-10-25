
#Xabi Alonso,26,Spain,Liverpool,2004,2008,143,Premier League
#Michael Owen,23,England,Liverpool,1996,2003,216,Premier League
#Michael Owen,31,England,Man Utd,2009,2011,31,Premier League
#Roy Keane,33,Ireland,Man Utd,1993,2005,326,Premier League
import itertools
import networkx as nx
import pandas as pd
import glob
import os

# Adjust the path and pattern to match your CSV filenames
data_path = os.path.join(os.getcwd(), "datasets")
csv_files = glob.glob(os.path.join(data_path, "*_cumulative.csv"))

if not csv_files:
    raise FileNotFoundError(f"No CSV files found in {data_path}")
print(f"Found {len(csv_files)} CSV files:")
# Read and concatenate all CSVs
df_list = [pd.read_csv(file) for file in csv_files]
combined_df = pd.concat(df_list, ignore_index=True)

# Optional: remove duplicates just in case
combined_df = combined_df.drop_duplicates(subset=["player_name", "team_name", "start_year", "end_year"])

#make this new dataset
combined_csv_path = os.path.join(data_path, "all_leagues_combined.csv")
combined_df.to_csv(combined_csv_path, index=False)
print(f"Saved combined CSV saved to {combined_csv_path}")

df = pd.read_csv(combined_csv_path)
G = nx.Graph()

# Add player nodes
for player in df["player_name"].unique():
    G.add_node(player, type="player")

# Helper function to check overlap
def overlap(start1, end1, start2, end2):
    return not (end1 < start2 or end2 < start1)

# Build connections between overlapping teammates
# Essentially, convert them into data pairs then connect them if they played together
for team, group in df.groupby("team_name"):
    players = group.to_dict("records")
    for p1, p2 in itertools.combinations(players, 2):
        if overlap(p1["start_year"], p1["end_year"], p2["start_year"], p2["end_year"]):
            G.add_edge(p1["player_name"], p2["player_name"], team=team)

# use nx get shortest path function
def find_connection(graph, player_a, player_b):
    if player_a not in graph:
        raise ValueError(f"Player '{player_a}' not found in dataset.")
    if player_b not in graph:
        raise ValueError(f"Player '{player_b}' not found in dataset.")
    """Find the shortest connection between two players."""
    try:
        path = nx.shortest_path(graph, source=player_a, target=player_b)
        return path
    except nx.NetworkXNoPath:
        return None

def print_connection(graph, path):
    """Print connection as Player → Team → Player → Team → ..."""
    chain = []
    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        team = graph.edges[p1, p2]["team"]
        chain.append(p1)
        chain.append(team)
    chain.append(path[-1])
    print(" → ".join(chain))

# Example: Rooney ↔ Gerrard
connection = find_connection(G, "Cristiano Ronaldo", "Virgil van Dijk")

if connection:
    print_connection(G, connection)
else:
    print("No connection found.")
