from flask import Flask, request, render_template_string
from datetime import date
from padel_logic import search_all

app = Flask(__name__)


HTML_TEMPLATE = """
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Padel Finder – Caen</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        :root {
            --bg-body: #020617;
            --bg-panel: #020617;
            --bg-card: rgba(15,23,42,0.9);
            --accent: #22c55e;
            --accent-soft: rgba(34,197,94,0.18);
            --accent-strong: #16a34a;
            --text-main: #e5e7eb;
            --text-muted: #9ca3af;
            --border-subtle: rgba(148,163,184,0.4);
            --error: #f97373;
            --shadow-soft: 0 18px 45px rgba(15,23,42,0.9);
            --radius-lg: 18px;
            --radius-xl: 22px;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top, #0f172a 0, #020617 55%, #000 100%);
            color: var(--text-main);
            display: flex;
            justify-content: center;
            padding: 20px 12px;
        }

        .app-shell {
            width: 100%;
            max-width: 1120px;
            background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(15,23,42,0.9));
            border-radius: 28px;
            border: 1px solid rgba(148,163,184,0.5);
            box-shadow: var(--shadow-soft);
            padding: 22px 22px 26px;
            backdrop-filter: blur(18px);
        }

        header {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }

        .title-block h1 {
            font-size: 1.4rem;
            margin: 0;
            letter-spacing: 0.03em;
        }

        .title-block p {
            margin: 6px 0 0;
            font-size: 0.86rem;
            color: var(--text-muted);
        }

        .pill-env {
            font-size: 0.76rem;
            padding: 6px 11px;
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.5);
            background: radial-gradient(circle at top left, rgba(34,197,94,0.18), rgba(15,23,42,0.85));
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        main {
            display: grid;
            grid-template-columns: minmax(0, 320px) minmax(0, 1.6fr);
            gap: 18px;
        }

        @media (max-width: 880px) {
            main {
                grid-template-columns: minmax(0, 1fr);
            }
        }

        .card {
            background: var(--bg-card);
            border-radius: var(--radius-xl);
            border: 1px solid rgba(148,163,184,0.35);
            padding: 16px 16px 18px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 10px;
        }

        .card-header h2 {
            font-size: 1.02rem;
            margin: 0;
        }

        .card-header span {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        /* Formulaire */
        form {
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 0.87rem;
        }

        .field-group {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
        }

        .field {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        label span {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        input[type="date"],
        input[type="time"],
        .duration-pills label {
            font: inherit;
        }

        input[type="date"],
        input[type="time"] {
            padding: 7px 9px;
            border-radius: 11px;
            border: 1px solid rgba(148,163,184,0.6);
            background: rgba(15,23,42,0.96);
            color: var(--text-main);
            outline: none;
        }

        input[type="date"]:focus,
        input[type="time"]:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.65);
        }

        .duration-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 3px;
        }

        .duration-pills label {
            padding: 5px 10px;
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.6);
            color: var(--text-muted);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            background: rgba(15,23,42,0.9);
        }

        .duration-pills input {
            display: none;
        }

        .duration-pills input:checked + span {
            color: var(--accent);
        }

        .duration-pills input:checked ~ .pill-bg {
            background: var(--accent-soft);
            border-color: var(--accent);
        }

        .pill-bg {
            position: absolute;
            inset: 0;
            border-radius: inherit;
            border: 1px solid transparent;
            z-index: -1;
        }

        .duration-pill-wrapper {
            position: relative;
        }

        button[type="submit"] {
            margin-top: 4px;
            padding: 9px 13px;
            border-radius: 999px;
            border: none;
            font-size: 0.86rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            cursor: pointer;
            background: linear-gradient(135deg, var(--accent), var(--accent-strong));
            color: #022c22;
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(16,185,129,0.35);
        }

        button[type="submit"]:hover {
            filter: brightness(1.05);
        }

        button[type="submit"]:active {
            transform: translateY(1px);
            box-shadow: 0 6px 18px rgba(16,185,129,0.45);
        }

        /* Résultats */
        .results-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            font-size: 0.8rem;
            margin-bottom: 10px;
        }

        .chip {
            border-radius: 999px;
            border: 1px solid rgba(148,163,184,0.6);
            padding: 3px 9px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .chip strong {
            font-weight: 500;
        }

        .chip-accent {
            border-color: rgba(34,197,94,0.7);
            background: rgba(22,163,74,0.05);
        }

        .chip-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--accent);
        }

        .club-block {
            margin-top: 14px;
            padding-top: 10px;
            border-top: 1px dashed rgba(148,163,184,0.45);
        }

        .club-block:first-of-type {
            border-top: none;
            padding-top: 2px;
        }

        .club-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }

        .club-header h3 {
            margin: 0;
            font-size: 0.95rem;
        }

        .club-header span {
            font-size: 0.76rem;
            color: var(--text-muted);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
            font-size: 0.8rem;
        }

        thead {
            background: rgba(15,23,42,0.96);
        }

        th, td {
            padding: 6px 8px;
            border-bottom: 1px solid rgba(15,23,42,0.9);
        }

        th {
            text-align: left;
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.78rem;
        }

        tbody tr:nth-child(2n) {
            background: rgba(15,23,42,0.7);
        }

        .no-slots {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-style: italic;
            margin: 3px 0 8px;
        }

        .errors {
            margin-top: 12px;
            padding: 8px 10px;
            border-radius: 12px;
            border: 1px solid rgba(248,113,113,0.7);
            background: rgba(127,29,29,0.24);
            font-size: 0.8rem;
        }

        .errors h3 {
            margin: 0 0 4px;
            font-size: 0.86rem;
            color: var(--error);
        }

        .errors ul {
            margin: 0;
            padding-left: 18px;
        }

        .errors li {
            margin: 2px 0;
        }

        .hint {
            margin-top: 6px;
            font-size: 0.76rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="app-shell">
        <header>
            <div class="title-block">
                <h1>Padel Finder – Caen</h1>
                <p>Compare les créneaux dispo sur les complexes Doinsport, R Padel Arena &amp; Padelshot.</p>
            </div>
            <div class="pill-env">
                <span style="width:7px;height:7px;border-radius:999px;background:#22c55e;"></span>
                <span>Serveur local</span>
            </div>
        </header>

        <main>
            <!-- Carte de gauche : formulaire -->
            <section class="card">
                <div class="card-header">
                    <h2>Paramètres de recherche</h2>
                    <span>Choisis quand tu veux jouer</span>
                </div>

                <form method="post">
                    <div class="field">
                        <label>
                            <span>Date</span>
                            <input type="date" name="date" value="{{ form_values.date }}">
                        </label>
                    </div>

                    <div class="field-group">
                        <div class="field">
                            <label>
                                <span>Heure de début</span>
                                <input type="time" name="from_time" value="{{ form_values.from_time }}">
                            </label>
                        </div>
                        <div class="field">
                            <label>
                                <span>Heure de fin</span>
                                <input type="time" name="to_time" value="{{ form_values.to_time }}">
                            </label>
                        </div>
                    </div>

                    <div class="field">
                        <span>Durées souhaitées</span>
                        <div class="duration-pills">
                            <label class="duration-pill-wrapper">
                                <input type="checkbox" name="durations" value="60"
                                    {% if 60 in form_values.durations %}checked{% endif %}>
                                <span>60 min</span>
                                <span class="pill-bg"></span>
                            </label>
                            <label class="duration-pill-wrapper">
                                <input type="checkbox" name="durations" value="90"
                                    {% if 90 in form_values.durations %}checked{% endif %}>
                                <span>90 min</span>
                                <span class="pill-bg"></span>
                            </label>
                            <label class="duration-pill-wrapper">
                                <input type="checkbox" name="durations" value="120"
                                    {% if 120 in form_values.durations %}checked{% endif %}>
                                <span>120 min</span>
                                <span class="pill-bg"></span>
                            </label>
                        </div>
                    </div>

                    <button type="submit">Lancer la recherche</button>

                    <p class="hint">
                        Les créneaux proposés commencent exactement à l’heure de début choisie
                        et doivent tenir entièrement dans la plage (début → fin).
                    </p>
                </form>
            </section>

            <!-- Carte de droite : résultats -->
            <section class="card">
                <div class="card-header">
                    <h2>Résultats</h2>
                    <span>
                        {% if results %}
                            Dernière recherche effectuée
                        {% else %}
                            Lance une recherche pour voir les créneaux
                        {% endif %}
                    </span>
                </div>

                {% if results %}
                <div class="results-meta">
                    <div class="chip chip-accent">
                        <span class="chip-dot"></span>
                        <span><strong>Date :</strong> {{ results.date_iso }}</span>
                    </div>
                    <div class="chip">
                        <span><strong>Plage :</strong> {{ results.window_from }} → {{ results.window_to }}</span>
                    </div>
                    <div class="chip">
                        <span><strong>Durées :</strong> {{ results.durations|join(", ") }} min</span>
                    </div>
                </div>

                <!-- Doinsport -->
                <div class="club-block">
                    <div class="club-header">
                        <h3>Doinsport (Stadium / Pommeraie / Area)</h3>
                        <span>3 complexes</span>
                    </div>

                    {% for club in results.doinsport %}
                        <div style="margin-bottom:10px;">
                            <strong style="font-size:0.85rem;">{{ club.club_name }}</strong>
                            {% if club.slots %}
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Heure</th>
                                            <th>Durée</th>
                                            <th>Terrain</th>
                                            <th>Prix / joueur</th>
                                            <th>Nb joueurs</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for s in club.slots %}
                                        <tr>
                                            <td>{{ s.startAt }}</td>
                                            <td>{{ s.duration_min }} min</td>
                                            <td>{{ s.terrain }}</td>
                                            <td>
                                                {% if s.price_per_participant %}
                                                    {{ "%.2f"|format(s.price_per_participant / 100) }} €
                                                {% else %}
                                                    -
                                                {% endif %}
                                            </td>
                                            <td>{{ s.participant_count or "-" }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            {% else %}
                                <p class="no-slots">Aucun créneau correspondant pour ce club.</p>
                            {% endif %}
                        </div>
                    {% endfor %}
                </div>

                <!-- R Padel Arena -->
                {% if results.rpadel %}
                <div class="club-block">
                    <div class="club-header">
                        <h3>{{ results.rpadel.club_name }}</h3>
                        <span>mymobileapp.fr</span>
                    </div>

                    {% if results.rpadel.slots %}
                        <table>
                            <thead>
                                <tr>
                                    <th>Heure</th>
                                    <th>Durée</th>
                                    <th>Détail</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for s in results.rpadel.slots %}
                                <tr>
                                    <td>{{ s.startAt }}</td>
                                    <td>{{ s.duration_min }} min</td>
                                    <td>{{ s.raw_text }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% else %}
                        <p class="no-slots">Aucun créneau correspondant.</p>
                    {% endif %}
                </div>
                {% endif %}

                <!-- Padelshot -->
                {% if results.padelshot %}
                <div class="club-block">
                    <div class="club-header">
                        <h3>{{ results.padelshot.club_name }}</h3>
                        <span>Matchpoint</span>
                    </div>

                    {% if results.padelshot.slots %}
                        <table>
                            <thead>
                                <tr>
                                    <th>Heure</th>
                                    <th>Durée</th>
                                    <th>Terrain</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for s in results.padelshot.slots %}
                                <tr>
                                    <td>{{ s.startAt }}</td>
                                    <td>{{ s.duration_min }} min</td>
                                    <td>{{ s.terrain }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% else %}
                        <p class="no-slots">Aucun créneau correspondant.</p>
                    {% endif %}
                </div>
                {% endif %}

                {% if results.errors %}
                <div class="errors">
                    <h3>Erreurs rencontrées</h3>
                    <ul>
                        {% for err in results.errors %}
                            <li>{{ err }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}

                {% else %}
                <p style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;">
                    Choisis une date, une plage horaire et une ou plusieurs durées,
                    puis clique sur <strong>« Lancer la recherche »</strong>.
                </p>
                {% endif %}
            </section>
        </main>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    # Valeurs par défaut
    default_date = date.today().isoformat()
    default_from = "18:00"
    default_to = "19:30"
    default_durations = [90]

    if request.method == "POST":
        date_str = request.form.get("date") or default_date
        from_time = request.form.get("from_time") or default_from
        to_time = request.form.get("to_time") or default_to

        durations_str_list = request.form.getlist("durations")
        if durations_str_list:
            try:
                durations = [int(d) for d in durations_str_list]
            except ValueError:
                durations = default_durations
        else:
            durations = default_durations

        results = search_all(date_str, from_time, to_time, durations)

        form_values = {
            "date": date_str,
            "from_time": from_time,
            "to_time": to_time,
            "durations": durations,
        }

        return render_template_string(
            HTML_TEMPLATE,
            form_values=form_values,
            results=results,
        )

    # GET : juste le formulaire
    form_values = {
        "date": default_date,
        "from_time": default_from,
        "to_time": default_to,
        "durations": default_durations,
    }

    return render_template_string(
        HTML_TEMPLATE,
        form_values=form_values,
        results=None,
    )


if __name__ == "__main__":
    app.run(debug=True)
