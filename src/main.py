import pandas as pd
from matplotlib import pyplot as plt
from utils.utils import get_player_stats, get_player_history, plot_player_history, get_espn_rankings, get_goalie_names
pd.set_option('expand_frame_repr', False)


if __name__ == '__main__':

    years = [2019, 2020, 2021, 2022, 2023, 2024]

    # Takes about 10 seconds using API. For speed, comment this out and just load it as a csv once you've run it once
    stats = get_player_stats(years=years)
    stats.to_csv("../data/stats.csv", index=False)

    stats = pd.read_csv("../data/stats.csv")

    current_year = years[-1]

    # # Print the DataFrame
    # print(f"\nStats DataFrame for {current_year}:\n")
    # print(stats[stats["Year"] == current_year].head())

    # Filter and sort by PPG
    min_gp = 15
    current_stats = stats[stats["Year"] == current_year]
    filtered = current_stats[current_stats["GP"] >= min_gp].sort_values(by="PPG", ascending=False)
    filtered = filtered[filtered["Position"] != "Goalie"]
    filtered = filtered.reset_index().drop("index", axis=1)
    filtered.index.name = "PPG Rank"
    filtered["EWMA PPG"] = None
    for idx in filtered.index:
        player_name = filtered.loc[idx, "Player"]
        player_history = get_player_history(stats=stats, player_name=player_name, score_type="PPG")["PPG"]
        filtered.loc[idx, f"EWMA PPG"] = round(player_history.ewm(alpha=0.75).mean().iloc[-1], 2)
    filtered = filtered[["Player", "PPG", "EWMA PPG", "Total Points", "GP", "Position", "Year"]]
    print(f"\n\n\nSkater stats sorted by PPG and filtered for minimum of {min_gp} GP:\n\n")
    print(filtered.head(200).to_string())

    # Compare player histories
    player_name = "David Pastrnak"
    score_type = "PPG"  # Either "PPG" or "Total Points"
    plot_player_history(stats=stats, player_name=player_name, score_type=score_type)

    # Try to find some gems based on ESPN's rankings
    espn_rankings = get_espn_rankings()
    player_projections = pd.DataFrame(index=espn_rankings, columns=[score_type, f"EWMA {score_type}"])
    player_projections.index.name = "Player"
    for player_name in espn_rankings:
        player_history = get_player_history(stats=stats, player_name=player_name, score_type=score_type)[score_type]
        player_projections.loc[player_name, score_type] = round(player_history.iloc[-1], 2)
        player_projections.loc[player_name, f"EWMA {score_type}"] = round(player_history.ewm(alpha=0.75).mean().iloc[-1], 2)
    player_projections.reset_index(inplace=True)
    player_projections.index = [x+1 for x in player_projections.index]
    player_projections.index.name = "ESPN Ranking"

    # Remove goalies
    goalies = get_goalie_names(stats=stats)
    player_projections = player_projections[~player_projections["Player"].isin(goalies)]

    plt.figure(figsize=(14, 8))
    plt.grid()
    plt.plot(player_projections["PPG"], linewidth=2, color="b")
    plt.title("Player Projections", fontname="STIXGeneral", fontsize=25)
    plt.xlabel("ESPN Ranking", fontname="STIXGeneral", fontsize=20)
    plt.ylabel("EWMA PPG", fontname="STIXGeneral", fontsize=20)
    plt.show()

    player_projections = player_projections.sort_values(by="PPG", ascending=False)
    player_projections.reset_index(inplace=True)
    player_projections.index = [x+1 for x in player_projections.index]
    player_projections.index.name = "PPG Ranking"
    player_projections["Steal Value"] = player_projections["ESPN Ranking"] - player_projections.index

    print("\n\n\nGems:\n\n")
    print(player_projections.sort_values(by="Steal Value", ascending=False).to_string())
