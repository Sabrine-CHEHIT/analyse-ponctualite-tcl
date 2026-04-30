import pandas as pd
import numpy as np
from random import uniform, gauss

# Fixer la graine aléatoire pour que les résultats soient reproductibles
np.random.seed(42)

# ==================== 1. DÉFINITION DES DONNÉES DE BASE ====================

# Les lignes de métro
lignes = [
    {"route_id": "R001", "route_short_name": "A", "route_long_name": "Ligne A", "couleur": "Rouge"},
    {"route_id": "R002", "route_short_name": "B", "route_long_name": "Ligne B", "couleur": "Bleue"},
    {"route_id": "R003", "route_short_name": "C", "route_long_name": "Ligne C", "couleur": "Verte"}
]

# Les stations par ligne
stations_par_ligne = {
    "R001": ["Gare Centrale", "République", "Victor Hugo", "Jean Jaurès", "Mairie", 
             "Parc", "Université", "Stade", "Hôpital", "Aéroport"],
    "R002": ["Gare du Nord", "Voltaire", "Halles", "Gambetta", "Foch", 
             "Bastille", "Carnot", "Lac", "Forêt", "Zénith"],
    "R003": ["Beaujolais", "Plage", "Cité", "Europe", "Liberté", 
             "Molière", "Curie", "Pasteur", "Verdun", "Piscine"]
}

# Création du fichier stops.txt (stations)
stops = []
for route_id, stations in stations_par_ligne.items():
    ligne_nom = next(l["route_short_name"] for l in lignes if l["route_id"] == route_id)
    for i, station_nom in enumerate(stations):
        stops.append({
            "stop_id": f"{route_id}_{i+1:02d}",
            "stop_name": f"{station_nom} (Ligne {ligne_nom})",
            "stop_lat": 45.750000 + (i * 0.01) + (0.01 if "B" in route_id else -0.01),
            "stop_lon": 4.850000 + (i * 0.01) + (0.005 if "C" in route_id else -0.005),
            "stop_sequence": i
        })

df_stops = pd.DataFrame(stops)
df_stops.to_csv("stops.csv", index=False)
print(f"✅ stops.csv généré : {len(df_stops)} stations")

# ==================== 2. CRÉATION DES VOYAGES (trips.txt) ====================

trips = []
trip_id_counter = 0
service_id_semaine = "WD"
service_id_weekend = "WE"

# Création du fichier calendar
calendar_data = [
    {"service_id": "WD", "monday": 1, "tuesday": 1, "wednesday": 1, "thursday": 1, "friday": 1, "saturday": 0, "sunday": 0, "start_date": "20240101", "end_date": "20241231"},
    {"service_id": "WE", "monday": 0, "tuesday": 0, "wednesday": 0, "thursday": 0, "friday": 0, "saturday": 1, "sunday": 1, "start_date": "20240101", "end_date": "20241231"}
]
df_calendar = pd.DataFrame(calendar_data)
df_calendar.to_csv("calendar.csv", index=False)
print(f"✅ calendar.csv généré")

heures_service = [8, 12, 18]  # Heures de départ

# ==================== 3. CRÉATION DE stop_times.txt (avec retards SIMULÉS PLUS FORTS) ====================

stop_times = []
trip_counter = 0

for ligne in lignes:
    route_id = ligne["route_id"]
    stations_ligne = [s for s in stops if s["stop_id"].startswith(route_id)]
    stations_ligne.sort(key=lambda x: x["stop_sequence"])
    
    for heure in heures_service:
        for service_id in ["WD", "WE"]:
            trip_id = f"trip_{trip_counter:05d}"
            trip_counter += 1
            
            # Enregistrer le trip
            trips.append({
                "trip_id": trip_id,
                "route_id": route_id,
                "service_id": service_id,
                "trip_headsign": stations_ligne[-1]["stop_name"],
                "direction_id": 0
            })
            
            for seq, station in enumerate(stations_ligne):
                # Calcul de l'heure théorique (sans retard)
                minutes_depuis_depart = seq * 1
                arrival_sec_prev = (heure * 3600) + (minutes_depuis_depart * 60)
                
                # ========== SIMULATION DE RETARD PLUS AGRESSIVE ==========
                retard_secondes_float = 0.0
                
                # Règle 1: Plus de retards en heure de pointe (8h et 18h)
                if heure in [8, 18]:
                    retard_secondes_float += gauss(180, 60)  # 3 minutes en moyenne (180 sec)
                else:  # heure creuse (12h)
                    retard_secondes_float += gauss(30, 20)   # 30 secondes en moyenne
                
                # Règle 2: La ligne B est particulièrement mauvaise (ajouter du retard)
                if route_id == "R002":
                    if heure in [8, 18]:
                        retard_secondes_float += gauss(240, 90)  # 4 minutes de plus (240 sec)
                    else:
                        retard_secondes_float += gauss(60, 30)   # 1 minute de plus
                
                # Règle 3: La ligne A est moyenne
                if route_id == "R001" and heure in [8, 18]:
                    retard_secondes_float += gauss(60, 30)  # 1 minute de plus en heure de pointe
                
                # Règle 4: Le weekend est plus calme (moins de retard)
                if service_id == "WE":
                    retard_secondes_float = max(0.0, retard_secondes_float - 90)  # 1min30 de moins
                
                # Règle 5: Ajouter un aléa supplémentaire (panne mineure, affluence)
                retard_secondes_float += uniform(-20, 120)
                
                # Ne jamais avoir de retard négatif
                retard_secondes_float = max(0.0, retard_secondes_float)
                
                # Convertir en entier pour l'affichage (on arrondit)
                retard_secondes_int = int(round(retard_secondes_float))
                
                # Heure réelle = heure prévue + retard (en secondes)
                arrival_sec_reel = arrival_sec_prev + retard_secondes_int
                
                # Conversion en format HH:MM:SS avec des ENTIERS (int)
                # Heure prévue
                heure_prev = int(arrival_sec_prev // 3600)
                minute_prev = int((arrival_sec_prev % 3600) // 60)
                arrival_time_prev = f"{heure_prev:02d}:{minute_prev:02d}:00"
                
                # Heure réelle
                heure_reel = int(arrival_sec_reel // 3600)
                minute_reel = int((arrival_sec_reel % 3600) // 60)
                arrival_time_reel = f"{heure_reel:02d}:{minute_reel:02d}:00"
                
                # Départ prévu = arrivée prévue + 20 secondes
                depart_sec_prev = arrival_sec_prev + 20
                heure_dep_prev = int(depart_sec_prev // 3600)
                minute_dep_prev = int((depart_sec_prev % 3600) // 60)
                departure_time_prev = f"{heure_dep_prev:02d}:{minute_dep_prev:02d}:00"
                
                # Départ réel = arrivée réelle + 20 secondes
                depart_sec_reel = arrival_sec_reel + 20
                heure_dep_reel = int(depart_sec_reel // 3600)
                minute_dep_reel = int((depart_sec_reel % 3600) // 60)
                departure_time_reel = f"{heure_dep_reel:02d}:{minute_dep_reel:02d}:00"
                
                stop_times.append({
                    "trip_id": trip_id,
                    "arrival_time": arrival_time_prev,
                    "departure_time": departure_time_prev,
                    "stop_id": station["stop_id"],
                    "stop_sequence": seq,
                    "arrival_time_reel": arrival_time_reel,
                    "departure_time_reel": departure_time_reel,
                    "retard_secondes": float(retard_secondes_float)  # On garde le float pour les calculs
                })

# Conversion en DataFrame
df_stop_times = pd.DataFrame(stop_times)
df_stop_times.to_csv("stop_times.csv", index=False)
print(f"✅ stop_times.csv généré : {len(df_stop_times)} lignes")

# ==================== 4. CRÉATION DE routes.txt ====================

df_routes = pd.DataFrame(lignes)
df_routes = df_routes[["route_id", "route_short_name", "route_long_name"]]
df_routes["agency_id"] = "TCL"
df_routes.to_csv("routes.csv", index=False)
print(f"✅ routes.csv généré")

# ==================== 5. CRÉATION DE trips.csv ====================

df_trips = pd.DataFrame(trips)
df_trips.to_csv("trips.csv", index=False)
print(f"✅ trips.csv généré : {len(df_trips)} voyages")

print("\n🎉 Génération terminée !")
print("📁 Fichiers créés : stops.csv, trips.csv, stop_times.csv, routes.csv, calendar.csv")
print(f"📊 Statistiques :")
print(f"   - {len(df_stops)} stations")
print(f"   - {len(df_trips)} voyages (trajets complets)")
print(f"   - {len(df_stop_times)} arrêts individuels")
