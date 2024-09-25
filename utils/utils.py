from espn_api.hockey import League
import pandas as pd
from matplotlib import pyplot as plt
from constants import LEAGUE_ID, ESPN_S2, SWID

def calculate_points(player, year: int) -> dict:

    player_stats = player.stats
    if f"Total {year}" not in player_stats:

        return {"Total Points": 0, "PPG": 0, "GP": 0}

    else:

        x = player_stats[f"Total {year}"]["total"]

        # League scoring formula
        if "G" in x:  # Skaters

            games_played = x["GP"]

            if games_played == 0:
                score = 0
            else:
                score = 3 * x["G"] + 2 * x["A"] + x["G"] + x["A"] + x["+/-"] + 0.3 * x["PIM"] + x["PPG"] + 0.5 * x["PPA"] + x[
                    "PPG"] + x["PPA"] + 2 * x["SHG"] + x["SHA"] + x["SHP"] + x["GWG"] + 0.2 * x["SOG"] + 0.3 * x["HIT"] + 0.5 * \
                        x["BLK"]

                if "DEF" in x:
                    score += x["DEF"]
                if "HAT" in x:
                    score += 10 * x["HAT"]

        elif "GS" in x:  # Goalies

            games_played = x["GS"]

            if games_played == 0:
                score = 0
            else:
                score = x["GS"] + 5 * x["W"] - 2 * x["L"] - x["GA"] + 0.22 * x["SV"] + 3 * x["SO"] + 2 * x["OTL"]

        else:
            raise ValueError(f"Unrecognized player: {player}")

        if games_played == 0:
            ppg = 0
        else:
            ppg = score / games_played

        return {"Total Points": score, "PPG": ppg, "GP": games_played}


def get_player_stats_single_league(league) -> pd.DataFrame:

    # Get free agents
    free_agents = league.free_agents(size=-1)

    # Get rostered players
    teams = league.teams
    still_rostered = []
    for i in range(len(teams)):
        still_rostered += league.teams[i].roster

    players = free_agents + still_rostered

    stats = pd.DataFrame(columns=["PPG", "Total Points", "GP", "Position", "Year"])
    stats.index.name = "Player"
    year = league.year
    for player in players:
        points = calculate_points(player=player, year=year)
        stats.loc[player.name, "PPG"] = round(points["PPG"], 2)
        stats.loc[player.name, "Total Points"] = points["Total Points"]
        stats.loc[player.name, "GP"] = round(points["GP"])
        stats.loc[player.name, "Year"] = year
        stats.loc[player.name, "Position"] = player.position

    return stats


def get_player_stats(
        years: list[int],
        league_id: int = LEAGUE_ID,
        espn_s2: str = ESPN_S2,
        swid: str = SWID
) -> pd.DataFrame:
    stats = []
    for year in years:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
        stats_year = get_player_stats_single_league(league=league)
        stats.append(stats_year.reset_index())
    stats = pd.concat(stats)
    return stats


def get_player_history(stats: pd.DataFrame, player_name: str, score_type: str) -> pd.Series:

    if score_type not in ["PPG", "Total Points"]:
        raise ValueError("Type must be either PPG or Total Points.")

    years = stats["Year"].unique()
    scores = pd.DataFrame(index=list(years), columns=[score_type, "GP"])
    for year in years:
        stats_year = stats[stats["Year"] == year]
        stats_year.set_index("Player", inplace=True)
        if player_name in stats_year.index:
            scores.loc[year, score_type] = stats_year.loc[player_name, score_type]
            scores.loc[year, "GP"] = stats_year.loc[player_name, "GP"]
        else:
            scores.loc[year, score_type] = 0
            scores.loc[year, "GP"] = 0

    return scores


def plot_player_history(stats: pd.DataFrame, player_name: str, score_type: str = "PPG"):

    scores = get_player_history(stats=stats, player_name=player_name, score_type=score_type)

    years = stats["Year"].unique()
    scores.index = [f"{year}\n{round(scores.loc[year, "GP"])} GP" for year in years]
    scores = scores[score_type]

    plt.figure(figsize=(14, 8))
    plt.grid()
    plt.plot(scores, linewidth=2, color="r")
    plt.title(f"{player_name} (Mean {score_type} = {round(scores.mean(), 2)})", fontname="STIXGeneral", fontsize=25)
    plt.ylabel(score_type, fontname="STIXGeneral", fontsize=20)
    ax = plt.gca()
    ax.tick_params(axis='both', which='major', labelsize=15)
    ax.tick_params(axis='both', which='minor', labelsize=15)
    plt.show()


def extract_player_names(rankings_text):
    # Split the text by lines
    lines = rankings_text.splitlines()

    # Initialize an empty list to store player names
    player_names = []

    # Loop through each line
    for line in lines:
        # Find the first period to remove the rank number
        period_index = line.find('.')

        # Extract the player name by taking the part after the period and before the first comma
        player_name = line[period_index + 2:line.find(',')]

        # Append the player's name to the list
        player_names.append(player_name)

    return player_names


def get_espn_rankings() -> list:
    # Example usage:
    rankings_text = """1. Nathan MacKinnon, Col (C1)
2. Auston Matthews, Tor (C2)
3. David Pastrnak, Bos (RW1)
4. Connor McDavid, Edm (C3)
5. Nikita Kucherov, TB (RW2)
6. Mikko Rantanen, Col (RW3)
7. Brady Tkachuk, Ott (LW1)
8. Leon Draisaitl, Edm (C4)
9. Roman Josi, Nsh (D1)
10. William Nylander, Tor (C5)
11. Kirill Kaprizov, Min (LW2)
12. J.T. Miller, Van (C6)
13. Matthew Tkachuk, Fla (LW3)
14. Elias Pettersson, Van (C7)
15. Sidney Crosby, Pit (C8)
16. Steven Stamkos, Nsh (C9)
17. Cale Makar, Col (D2)
18. Artemi Panarin, NYR (LW4)
19. Rasmus Dahlin, Buf (D3)
20. Brayden Point, TB (C10)
21. Kyle Connor, Wpg (LW5)
22. Jason Robertson, Dal (LW6)
23. Jack Hughes, NJ (C11)
24. Alex Ovechkin, Wsh (LW7)
25. Andrei Vasilevskiy, TB (G1)
26. Mika Zibanejad, NYR (C12)
27. Zach Hyman, Edm (RW4)
28. Filip Forsberg, Nsh (RW5)
29. Jake Guentzel, TB (LW8)
30. Sam Reinhart, Fla (RW6)
31. Frank Vatrano, Ana (LW9)
32. Carter Verhaeghe, Fla (C13)
33. Jack Eichel, Vgk (C14)
34. Connor Bedard, Chi (C15)
35. Dylan Larkin, Det (C16)
36. John Tavares, Tor (C17)
37. Nick Suzuki, Mon (C18)
38. Connor Hellebuyck, Wpg (G2)
39. Vincent Trocheck, NYR (C19)
40. Noah Dobson, NYI (D4)
41. Chris Kreider, NYR (LW10)
42. Wyatt Johnston, Dal (C20)
43. Joel Eriksson Ek, Min (C21)
44. Mitch Marner, Tor (RW7)
45. Matt Boldy, Min (LW11)
46. Evan Bouchard, Edm (D5)
47. Aleksander Barkov, Fla (C22)
48. Travis Konecny, Phi (RW8)
49. Tage Thompson, Buf (C23)
50. Adrian Kempe, LA (C24)
51. Jordan Kyrou, StL (RW9)
52. Victor Hedman, TB (D6)
53. Jonathan Marchessault, Nsh (LW12)
54. Clayton Keller, Utah (RW10)
55. Dougie Hamilton, NJ (D7)
56. Lucas Raymond, Det (RW11)
57. Alex DeBrincat, Det (RW12)
58. Sebastian Aho, Car (LW13)
59. Quinn Hughes, Van (D8)
60. Josh Morrissey, Wpg (D9)
61. Igor Shesterkin, NYR (G3)
62. MacKenzie Weegar, Cgy (D10)
63. Adam Fox, NYR (D11)
64. Tim Stutzle, Ott (C25)
65. Moritz Seider, Det (D12)
66. Nico Hischier, NJ (C26)
67. Fabian Zetterlund, SJ (LW14)
68. Evgeni Malkin, Pit (C27)
69. Jesper Bratt, NJ (LW15)
70. John Carlson, Wsh (D13)
71. Owen Tippett, Phi (RW13)
72. Mike Matheson, Mon (D14)
73. Erik Karlsson, Pit (D15)
74. Brock Nelson, NYI (C28)
75. Nazem Kadri, Cgy (C29)
76. Kevin Fiala, LA (LW16)
77. Ryan Nugent-Hopkins, Edm (LW17)
78. Tyler Toffoli, SJ (RW14)
79. Timo Meier, NJ (LW18)
80. Thatcher Demko, Van (G4)
81. Brock Faber, Min (D16)
82. Jared McCann, Sea (LW19)
83. Cole Caufield, Mon (RW15)
84. Jacob Trouba, NYR (D17)
85. Brandon Montour, Sea (D18)
86. Jake Sanderson, Ott (D19)
87. Anze Kopitar, LA (C30)
88. Patrik Laine, Mon (RW16)
89. Marco Rossi, Min (C31)
90. Darnell Nurse, Edm (D20)
91. Juuse Saros, Nsh (G5)
92. Bo Horvat, NYI (C32)
93. Tomas Hertl, Vgk (C33)
94. Roope Hintz, Dal (C34)
95. Miro Heiskanen, Dal (D21)
96. Trevor Moore, LA (LW20)
97. Martin Necas, Car (C35)
98. Juraj Slafkovsky, Mon (LW21)
99. Alexandar Georgiev, Col (G6)
100. Linus Ullmark, Ott (G7)
101. JJ Peterka, Buf (RW17)
102. Alex Tuch, Buf (RW18)
103. Brad Marchand, Bos (LW22)
104. Drake Batherson, Ott (RW19)
105. Sergei Bobrovsky, Fla (G8)
106. Alexis Lafreniere, NYR (LW23)
107. Andrei Svechnikov, Car (RW20)
108. Alex Pietrangelo, Vgk (D22)
109. Mats Zuccarello, Min (RW21)
110. Rasmus Andersson, Cgy (D23)
111. Tyson Foerster, Phi (RW22)
112. Claude Giroux, Ott (C36)
113. Zach Werenski, Cls (D24)
114. Yegor Sharangovich, Cgy (LW24)
115. Sam Bennett, Fla (LW25)
116. Jamie Benn, Dal (C37)
117. Joel Farabee, Phi (LW26)
118. Patrick Kane, Det (RW23)
119. Bryan Rust, Pit (RW24)
120. William Eklund, SJ (LW27)
121. Mikhail Sergachev, Utah (D25)
122. Nikolaj Ehlers, Wpg (LW28)
123. Evander Kane, Edm (LW29)
124. Brandon Hagel, TB (LW30)
125. Kris Letang, Pit (D26)
126. Anders Lee, NYI (LW31)
127. Pavel Buchnevich, StL (LW32)
128. Logan Cooley, Utah (C38)
129. Devon Toews, Col (D27)
130. Elias Lindholm, Bos (C39)
131. Brent Burns, Car (D28)
132. Drew Doughty, LA (D29)
133. Mark Scheifele, Wpg (C40)
134. Charlie McAvoy, Bos (D30)
135. Brock Boeser, Van (RW25)
136. Seth Jones, Chi (D31)
137. Dylan Cozens, Buf (C41)
138. Mathew Barzal, NYI (C42)
139. Artturi Lehkonen, Col (LW33)
140. Seth Jarvis, Car (RW26)
141. Blake Coleman, Cgy (C43)
142. Michael Bunting, Pit (LW34)
143. Dylan Strome, Wsh (C44)
144. Ryan O'Reilly, Nsh (C45)
145. Mikael Backlund, Cgy (C46)
146. Kirill Marchenko, Cls (LW35)
147. Brayden Schenn, StL (C47)
148. Matt Roy, Wsh (D32)
149. Brady Skjei, Nsh (D33)
150. Kyle Palmieri, NYI (RW27)
151. Charlie Coyle, Bos (C48)
152. Jeff Skinner, Edm (LW36)
153. Quinton Byfield, LA (C49)
154. Vince Dunn, Sea (D34)
155. Thomas Harley, Dal (D35)
156. William Karlsson, Vgk (C50)
157. Robert Thomas, StL (C51)
158. Oliver Bjorkstrand, Sea (RW28)
159. Viktor Arvidsson, Edm (LW37)
160. Leo Carlsson, Ana (C52)
161. Zach Benson, Buf (LW38)
162. Noah Hanifin, Vgk (D36)
163. Colton Parayko, StL (D37)
164. Logan Couture, SJ (C53)
165. Lawson Crouse, Utah (LW39)
166. Boone Jenner, Cls (LW40)
167. Matty Beniers, Sea (C54)
168. Sean Durzi, Utah (D38)
169. Yegor Chinakhov, Cls (RW29)
170. Jeremy Swayman, Bos (G9)
171. Matt Duchene, Dal (C55)
172. Alex Killorn, Ana (C56)
173. Ilya Sorokin, NYI (G10)
174. Cam York, Phi (D39)
175. Philipp Kurashev, Chi (LW41)
176. Ryan Hartman, Min (RW30)
177. Justin Faulk, StL (D40)
178. Morgan Rielly, Tor (D41)
179. Jake Oettinger, Dal (G11)
180. Tyler Seguin, Dal (C57)
181. Frederik Andersen, Car (G12)
182. Jakob Chychrun, Wsh (D42)
183. Eeli Tolvanen, Sea (LW42)
184. Nick Bjugstad, Utah (C58)
185. Dylan Guenther, Utah (RW31)
186. Gabriel Landeskog, FA (LW43)
187. Teuvo Teravainen, Chi (LW44)
188. Tyler Bertuzzi, Chi (LW45)
189. Phillip Danault, LA (C59)
190. Matias Maccelli, Utah (LW46)
191. Nino Niederreiter, Wpg (RW32)
192. Mark Stone, Vgk (RW33)
193. Mikael Granlund, SJ (C60)
194. Adam Larsson, Sea (D43)
195. Trevor Zegras, Ana (C61)
196. Neal Pionk, Wpg (D44)
197. Gustav Forsling, Fla (D45)
198. Rickard Rakell, Pit (C62)
199. Troy Terry, Ana (RW34)
200. Sean Monahan, Cls (C63)"""

    # Extract player names
    player_names = extract_player_names(rankings_text)

    return player_names


def get_goalie_names(stats: pd.DataFrame) -> list[str]:

    return list(stats[stats["Position"] == "Goalie"]["Player"].unique())
