from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
DB_FILE = 'sigma_rules.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.template_filter('fromjson')
def fromjson_filter(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

@app.template_filter('pretty_json_format')
def pretty_json_format_filter(value):
    if value is None:
        return "N/A"
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except TypeError:
        return str(value)

@app.template_filter('format_datetime')
def format_datetime_filter(value):
    if not value:
        return "N/A"
    if isinstance(value, str):
        try:
            dt_obj = datetime.fromisoformat(value.split('.')[0])
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    elif isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value

def _get_filtered_rules(cursor, search_query, mitre_id_query, level_query, status_query):
    """
    Erstellt und führt eine Abfrage für Sigma-Regeln basierend auf den bereitgestellten Filtern aus.
    Dies ist eine interne Hilfsfunktion.
    """
    query_conditions = []
    params = []

    if search_query:
        # ERWEITERT: Die Suche schließt jetzt auch den Inhalt der rohen Regel ein.
        query_conditions.append("(title LIKE ? OR description LIKE ? OR id LIKE ? OR raw_rule LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
    if mitre_id_query:
        query_conditions.append("tags LIKE ?")
        params.append(f"%{mitre_id_query}%")
    if level_query:
        query_conditions.append("level = ?")
        params.append(level_query)
    if status_query:
        query_conditions.append("status = ?")
        params.append(status_query)

    base_query = "SELECT id, title, level, status FROM sigma_rules"
    if query_conditions:
        query = f"{base_query} WHERE {' AND '.join(query_conditions)} ORDER BY title ASC"
    else:
        query = f"{base_query} ORDER BY title ASC"

    return cursor.execute(query, tuple(params)).fetchall()

@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    mitre_id_query = request.args.get('mitre_id', '').strip()
    level_query = request.args.get('level', '').strip()
    status_query = request.args.get('status', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    rules = _get_filtered_rules(cursor, search_query, mitre_id_query, level_query, status_query)
    
    distinct_levels = [row['level'] for row in cursor.execute("SELECT DISTINCT level FROM sigma_rules WHERE level IS NOT NULL AND level != '' ORDER BY level").fetchall()]
    distinct_statuses = [row['status'] for row in cursor.execute("SELECT DISTINCT status FROM sigma_rules WHERE status IS NOT NULL AND status != '' ORDER BY status").fetchall()]

    conn.close()

    return render_template('index.html',
                           rules=rules,
                           search_query=search_query,
                           mitre_id_query=mitre_id_query,
                           level_query=level_query,
                           status_query=status_query,
                           distinct_levels=distinct_levels,
                           distinct_statuses=distinct_statuses,
                           selected_rule_id=None)

@app.route('/rule/<rule_id>')
def get_rule_details_page(rule_id):
    search_query = request.args.get('search', '').strip()
    mitre_id_query = request.args.get('mitre_id', '').strip()
    level_query = request.args.get('level', '').strip()
    status_query = request.args.get('status', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    rules_list = _get_filtered_rules(cursor, search_query, mitre_id_query, level_query, status_query)
    selected_rule = cursor.execute("SELECT * FROM sigma_rules WHERE id = ?", (rule_id,)).fetchone()
    
    distinct_levels = [row['level'] for row in cursor.execute("SELECT DISTINCT level FROM sigma_rules WHERE level IS NOT NULL AND level != '' ORDER BY level").fetchall()]
    distinct_statuses = [row['status'] for row in cursor.execute("SELECT DISTINCT status FROM sigma_rules WHERE status IS NOT NULL AND status != '' ORDER BY status").fetchall()]
    
    conn.close()

    if not selected_rule:
        return render_template('index.html',
                               rules=rules_list,
                               error_message="Regel nicht gefunden.",
                               selected_rule_id=None,
                               search_query=search_query,
                               mitre_id_query=mitre_id_query,
                               level_query=level_query,
                               status_query=status_query,
                               distinct_levels=distinct_levels,
                               distinct_statuses=distinct_statuses), 404

    return render_template('index.html',
                           rules=rules_list,
                           selected_rule=selected_rule,
                           selected_rule_id=rule_id,
                           search_query=search_query,
                           mitre_id_query=mitre_id_query,
                           level_query=level_query,
                           status_query=status_query,
                           distinct_levels=distinct_levels,
                           distinct_statuses=distinct_statuses)

@app.route('/api/rule/<rule_id>')
def api_get_rule(rule_id):
    conn = get_db_connection()
    rule = conn.execute('SELECT * FROM sigma_rules WHERE id = ?', (rule_id,)).fetchone()
    conn.close()
    
    if rule is None:
        return jsonify({'error': 'Rule not found'}), 404
        
    rule_dict = dict(rule)
    for key in ['references', 'detection', 'falsepositives', 'tags']:
        if rule_dict.get(key):
            try:
                rule_dict[key] = json.loads(rule_dict[key])
            except (json.JSONDecodeError, TypeError):
                pass
                
    return jsonify(rule_dict)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
