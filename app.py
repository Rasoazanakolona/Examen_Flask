import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "course_animaux_secret_key"

# Données du jeu
animaux = ["Lapin", "Elephant", "Tigre", "Giraphe", "Gepart", "Lion", "Cheval", "Torreau", "Loup", "Ours"]
puissance = {"Lapin": 50, "Elephant": 100, "Tigre": 120, "Giraphe": 80, "Gepart": 160, "Lion": 110, "Cheval": 90, "Torreau": 200, "Loup": 140, "Ours": 170}
intelligence = {"Lapin": 140, "Elephant": 140, "Tigre": 100, "Giraphe": 90, "Gepart": 150, "Lion": 105, "Cheval": 95, "Torreau": 140, "Loup": 160, "Ours": 135}
terrains = {"A": 1000, "B": 560, "C": 240, "D": 1250, "E": 850}

historique_courses = []

class GestionCourse:
    def __init__(self):
        self.epsilon = 0.2
        self.memoire = {t: {a: 0 for a in animaux} for t in terrains.keys()}
        self.votes_humains = {a: 0 for a in animaux}
        self.total_votes = 0

    def choisir_ia(self, terrain):
        if random.random() < self.epsilon:
            return random.choice(animaux), "EXPLORATION (Hasard)"
        scores_terrain = self.memoire[terrain]
        if max(scores_terrain.values()) == 0:
            return random.choice(animaux), "EXPLORATION (Premier essai)"
        meilleur = max(scores_terrain, key=scores_terrain.get)
        return meilleur, "EXPLOITATION (Intelligence)"

    def enregistrer_resultat(self, terrain, gagnant):
        self.memoire[terrain][gagnant] += 1

    def reinitialiser(self):
        self.memoire = {t: {a: 0 for a in animaux} for t in terrains.keys()}

course = GestionCourse()

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools():
    return jsonify({}), 200

@app.route('/', methods=['GET', 'POST'])
def index():
    animal_ia = request.form.get('animal_ia_hidden')
    mode_ia = request.form.get('mode_ia_hidden')
    animal_humain = request.form.get('animal_humain')
    terrain_sel = request.form.get('terrain')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'preparer':
            animal_ia, mode_ia = course.choisir_ia(terrain_sel)
            
            # ✅ CORRECTION 1 : Sauvegarder le terrain en session dès l'étape "préparer"
            session['terrain_sel'] = terrain_sel
            session['dernier_choix_ia'] = animal_ia
            session['dernier_mode_ia'] = mode_ia
            session['dernier_choix_humain'] = animal_humain

            if animal_humain:
                course.votes_humains[animal_humain] += 1
                course.total_votes += 1

        elif action == 'commencer':
            # ✅ CORRECTION 2 : Si terrain_sel est vide, récupérer depuis la session
            if not terrain_sel:
                terrain_sel = session.get('terrain_sel', 'A')
            if not animal_ia:
                animal_ia = session.get('dernier_choix_ia')
            if not mode_ia:
                mode_ia = session.get('dernier_mode_ia')
            if not animal_humain:
                animal_humain = session.get('dernier_choix_humain')

            diff = terrains[terrain_sel]
            resultats = {}
            for a in animaux:
                vitesse_calc = (puissance[a] * 0.5 + intelligence[a] * 0.3) - (diff / 50) + random.randint(0, 40)
                resultats[a] = round(max(vitesse_calc, 10), 2)

            gagnant_course = max(resultats, key=resultats.get)
            vitesse_max = resultats[gagnant_course]

            course.enregistrer_resultat(terrain_sel, gagnant_course)

            historique_courses.append({
                'terrain': terrain_sel,
                'humain': animal_humain,
                'ia': animal_ia,
                'gagnant': gagnant_course,
                'vitesse': vitesse_max
            })

            session['dernier_gagnant'] = gagnant_course
            session['derniere_vitesse'] = vitesse_max
            session['terrain_sel'] = terrain_sel
            session['dernier_choix_ia'] = animal_ia
            session['dernier_mode_ia'] = mode_ia
            session['dernier_choix_humain'] = animal_humain

            return redirect(url_for('index'))

    # Récupération après redirection (GET)
    gagnant = session.pop('dernier_gagnant', None)
    vitesse = session.pop('derniere_vitesse', 0)

    if gagnant:
        animal_ia = session.pop('dernier_choix_ia', None)
        mode_ia = session.pop('dernier_mode_ia', None)
        animal_humain = session.pop('dernier_choix_humain', None)

    # ✅ CORRECTION 3 : terrain_sel du formulaire a priorité sur la session
    t_sel = terrain_sel or session.get('terrain_sel') or "A"

    return render_template('index.html',
                           animaux=animaux, terrains=terrains,
                           choix_ia=animal_ia, mode_ia=mode_ia,
                           choix_humain=animal_humain, terrain_sel=t_sel,
                           gagnant=gagnant, vitesse=vitesse,
                           memoire_ia=course.memoire[t_sel],
                           historique=historique_courses)

@app.route('/reset_ia', methods=['POST'])
def reset_ia():
    course.reinitialiser()
    return redirect(url_for('index'))

@app.route('/supprimer_tout', methods=['POST'])
def supprimer_tout():
    global historique_courses
    historique_courses.clear()
    return jsonify({"success": True})

@app.route('/supprimer_ligne/<int:index>', methods=['POST'])
def supprimer_ligne(index):
    try:
        if 0 <= index < len(historique_courses):
            historique_courses.pop(index)
            return jsonify({"success": True})
    except Exception:
        pass
    return jsonify({"success": False}), 400

if __name__ == '__main__':
    app.run(debug=True)