from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import subprocess, sys, os
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        # Lance ton scraper avec le même interpréteur
        subprocess.run([sys.executable, 'welcome.py', query], check=True)
        return redirect(url_for('results', query=query))
    return render_template('form.html')

@app.route('/results')
def results():
    query         = request.args.get('query', '')
    loc_f         = request.args.get('location', '').strip()
    cont_f        = request.args.get('contract', '').strip()
    comp_f        = request.args.get('company', '').strip()
    created_order = request.args.get('created_order', '')

    csv_path = os.path.join(os.getcwd(), 'offres_et_compagnies.csv')
    if not os.path.exists(csv_path):
        return "<p>Le fichier CSV n'a pas été trouvé.</p>"

    df = pd.read_csv(csv_path)

    # Appliquer les filtres textuels
    if loc_f:
        df = df[df['Localisation'].str.contains(loc_f, case=False, na=False)]
    if cont_f:
        df = df[df['Type Contrat'].str.contains(cont_f, case=False, na=False)]
    if comp_f:
        df = df[df['Entreprise nom'].str.contains(comp_f, case=False, na=False)]

    # Tri “Créée en”
    if 'Crée en' in df.columns:
        # On extrait l'année (4 chiffres) en float pour pouvoir trier
        df['__year'] = (
            df['Crée en']
              .astype(str)
              .str.extract(r'(\d{4})', expand=False)
              .astype(float)
              .fillna(0)
        )
        if created_order == 'asc':
            df = df.sort_values('__year', ascending=True)
        elif created_order == 'desc':
            df = df.sort_values('__year', ascending=False)
        df.drop(columns='__year', inplace=True)

    # Générer HTML
    table_html = df.head().to_html(classes='data', header="true", index=False)

    return render_template('results.html',
                           table=table_html,
                           query=query,
                           filters={
                             'location':      loc_f,
                             'contract':      cont_f,
                             'company':       comp_f,
                             'created_order': created_order
                           })

@app.route('/download')
def download_csv():
    return send_from_directory(os.getcwd(),
                               'offres_et_compagnies.csv',
                               as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
