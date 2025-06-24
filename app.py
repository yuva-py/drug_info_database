from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import spacy
from sqlalchemy import Column, Integer, ForeignKey, Table
from spacy.matcher import PhraseMatcher
import os
from dotenv import load_dotenv
import logging

# Load spaCy model for NLP
nlp = spacy.load("en_core_web_sm")
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = 'the_name_is_yuvaraj'

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize SQLAlchemy ONCE and bind it to app
db = SQLAlchemy(app)  # ✅ DO THIS ONCE ONLY

# Set up logging
logging.basicConfig(level=logging.INFO)

# Global variable to store extracted and normalized symptoms
extracted_symptoms_store = []

@app.route('/')
def home():
    return render_template('home.html')

# Define association tables
disease_symptom = db.Table('disease_symptom',
    db.Column('disease_id', db.Integer, db.ForeignKey('disease.id'), primary_key=True),
    db.Column('symptom_id', db.Integer, db.ForeignKey('symptom.id'), primary_key=True)
)

drug_symptom = db.Table('drug_symptom',
    db.Column('drug_id', db.Integer, db.ForeignKey('drugs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('symptom_id', db.Integer, db.ForeignKey('symptom.id', ondelete='CASCADE'), primary_key=True)
)

# Drug model
class Drug(db.Model):
    __tablename__ = 'drugs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    uses = db.Column(db.Text, nullable=True)
    side_effects = db.Column(db.Text, nullable=True)
    symptoms = db.relationship('Symptom', secondary=drug_symptom, back_populates='drugs')

# Symptom model
class Symptom(db.Model):
    __tablename__ = 'symptom'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    symptom_type_id = db.Column(db.Integer, db.ForeignKey('symptom_type.id'), nullable=False)
    symptom_category_id = db.Column(db.Integer, db.ForeignKey('symptom_category.id'), nullable=True)
    diseases = db.relationship('Disease', secondary=disease_symptom, back_populates='symptoms')
    drugs = db.relationship('Drug', secondary=drug_symptom, back_populates='symptoms')

# Disease model
class Disease(db.Model):
    __tablename__ = 'disease'
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(255), nullable=False, unique=True)
    category = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icd_code = db.Column(db.String(50), nullable=False)
    symptoms = db.relationship('Symptom', secondary=disease_symptom, back_populates='diseases')

# SymptomType model
class SymptomType(db.Model):
    __tablename__ = 'symptom_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    body_system_id = db.Column(db.Integer, db.ForeignKey('body_system.id'), nullable=False)
    symptoms = db.relationship('Symptom', backref='symptom_type', lazy=True)

# BodySystem model
class BodySystem(db.Model):
    __tablename__ = 'body_system'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    symptom_types = db.relationship('SymptomType', backref='body_system', lazy=True)

# Causes model
class Causes(db.Model):
    __tablename__ = 'causes'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    cause_description = db.Column(db.String(255), nullable=False)

# Diagnosis model
class Diagnosis(db.Model):
    __tablename__ = 'diagnosis'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    diagnosis_description = db.Column(db.String(255), nullable=False)

# DifferentialDiagnosis model
class DifferentialDiagnosis(db.Model):
    __tablename__ = 'differential_diagnosis'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    differential_description = db.Column(db.String(255), nullable=False)

# TreatmentOptions model
class TreatmentOptions(db.Model):
    __tablename__ = 'treatment_options'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    treatment_description = db.Column(db.String(255), nullable=False)

# Pathophysiology model
class Pathophysiology(db.Model):
    __tablename__ = 'pathophysiology'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)

# Prognosis model
class Prognosis(db.Model):
    __tablename__ = 'prognosis'
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    prognosis_description = db.Column(db.Text, nullable=False)

# SymptomCategory model
class SymptomCategory(db.Model):
    __tablename__ = 'symptom_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    body_system_id = db.Column(db.Integer, db.ForeignKey('body_system.id'), nullable=True)
SYNONYM_MAP = {
    'fever': ['high temperature', 'elevated temperature', 'pyrexia', 'febrile', 'hot', 'feverish', 'burning up'],
    'headache': ['head pain', 'throbbing head', 'migraine', 'pressure in the head', 'cephalalgia', 'headache', 'head pain'],
    'cough': ['coughing', 'dry cough', 'wet cough', 'tickle in the throat', 'productive cough', 'non-productive cough'],
    'nausea': ['upset stomach', 'feeling sick', 'queasy', 'nauseated', 'vomiting sensation', 'stomach upset'],
    'pain': ['ache', 'discomfort', 'hurt', 'soreness', 'tenderness', 'throbbing', 'aching'],
    'shortness of breath': ['trouble breathing', 'feeling breathless', 'difficulty catching breath', 'dyspnea', 'air hunger'],
    'sore throat': ['scratchy throat', 'pain in throat', 'pharyngitis', 'throat irritation'],
    'fatigue': ['feeling tired', 'exhaustion', 'low energy', 'feeling worn out', 'lethargy', 'weakness'],
    'dizziness': ['feeling dizzy', 'lightheaded', 'spinning sensation', 'vertigo', 'balance problems'],
    'chills': ['feeling cold', 'shivering', 'getting the chills', 'cold sweats'],
    'muscle pain': ['sore muscles', 'muscle ache', 'muscle discomfort', 'myalgia'],
    'joint pain': ['achy joints', 'joint discomfort', 'pain in the joints', 'arthralgia'],
    'diarrhea': ['loose stools', 'runny stools', 'frequent trips to the bathroom', 'diarrhea'],
    'constipation': ['trouble with bowel movements', 'hard stools', 'not being able to go', 'constipation'],
    'abdominal pain': ['stomach ache', 'belly pain', 'pain in the stomach', 'abdominal discomfort'],
    'numbness': ['tingling sensation', 'loss of feeling', 'numb feeling', 'paresthesia'],
    'rash': ['skin rash', 'irritated skin', 'skin breakout', 'eruption', 'skin irritation'],
    'swelling': ['swollen area', 'inflammation', 'puffiness', 'edema'],
    'heart palpitations': ['racing heart', 'fluttering heart', 'feeling heart pound', 'tachycardia'],
    'weight loss': ['losing weight', 'unintentional weight loss', 'weight drop', 'weight loss'],
    'weight gain': ['gaining weight', 'putting on pounds', 'weight increase', 'weight gain'],
    'sleep disturbances': ['trouble sleeping', 'difficulty falling asleep', 'restless nights', 'insomnia'],
    'anxiety': ['feeling anxious', 'nervousness', 'worried', 'uneasy', 'fear', 'apprehension'],
    'depression': ['feeling down', 'low spirits', 'sadness', 'melancholy', 'depressed mood'],
    'coughing up blood': ['coughing blood', 'blood in my cough', 'hemoptysis'],
    'chest pain': ['pain in the chest', 'chest discomfort', 'angina', 'heart pain'],
    'shortness of breath': ['trouble breathing', 'feeling breathless', 'difficulty catching breath', 'dyspnea', 'air hunger'],
    'fever': ['high temperature', 'elevated temperature', 'pyrexia', 'febrile', 'hot', 'feverish', 'burning up'],
    'headache': ['head pain', 'throbbing head', 'migraine', 'pressure in the head', 'cephalalgia', 'headache', 'head pain'],
    'cough': ['coughing', 'dry cough', 'wet cough', 'tickle in the throat', 'productive cough', 'non-productive cough'],
    'nausea': ['upset stomach', 'feeling sick', 'queasy', 'nauseated', 'vomiting sensation', 'stomach upset'],
    'pain': ['ache', 'discomfort', 'hurt', 'soreness', 'tenderness', 'throbbing', 'aching'],
    'shortness of breath': ['trouble breathing', 'feeling breathless', 'difficulty catching breath', 'dyspnea', 'air hunger'],
    'sore throat': ['scratchy throat', 'pain in throat', 'pharyngitis', 'throat irritation'],
    'fatigue': ['feeling tired', 'exhaustion', 'low energy', 'feeling worn out', 'lethargy', 'weakness'],
    'dizziness': ['feeling dizzy', 'lightheaded', 'spinning sensation', 'vertigo', 'balance problems'],
    'chills': ['feeling cold', 'shivering', 'getting the chills', 'cold sweats'],
    'muscle pain': ['sore muscles', 'muscle ache', 'muscle discomfort', 'myalgia'],
    'joint pain': ['achy joints', 'joint discomfort', 'pain in the joints', 'arthralgia'],
    'diarrhea': ['loose stools', 'runny stools', 'frequent trips to the bathroom', 'diarrhea'],
    'constipation': ['trouble with bowel movements', 'hard stools', 'not being able to go', 'constipation'],
    'abdominal pain': ['stomach ache', 'belly pain', 'pain in the stomach', 'abdominal discomfort'],
    'numbness': ['tingling sensation', 'loss of feeling', 'numb feeling', 'paresthesia'],
    'rash': ['skin rash', 'irritated skin', 'skin breakout', 'eruption', 'skin irritation'],
    'swelling': ['swollen area', 'inflammation', 'puffiness', 'edema'],
    'heart palpitations': ['racing heart', 'fluttering heart', 'feeling heart pound', 'tachycardia'],
    'weight loss': ['losing weight', 'unintentional weight loss', 'weight drop', 'weight loss'],
    'weight gain': ['gaining weight', 'putting on pounds', 'weight increase', 'weight gain'],
    'sleep disturbances': ['trouble sleeping', 'difficulty falling asleep', 'restless nights', 'insomnia'],
    'anxiety': ['feeling anxious', 'nervousness', 'worried', 'uneasy', 'fear', 'apprehension'],
    'depression': ['feeling down', 'low spirits', 'sadness', 'melancholy', 'depressed mood'],
    'coughing up blood': ['coughing blood', 'blood in my cough', 'hemoptysis'],
    'chest pain': ['pain in the chest', 'chest discomfort', 'angina', 'heart pain'],
    'shortness of breath': ['trouble breathing', 'feeling breathless', 'difficulty catching breath', 'dyspnea', 'air hunger'],
    'fever': ['high temperature', 'elevated temperature', 'pyrexia', 'febrile', 'hot', 'feverish', 'burning up'],
    'headache': ['head pain', 'throbbing head', 'migraine', 'pressure in the head', 'cephalalgia', 'headache', 'head pain'],
    'cough': ['coughing', 'dry cough', 'wet cough', 'tickle in the throat', 'productive cough', 'non-productive cough'],
    'nausea': ['upset stomach', 'feeling sick', 'queasy', 'nauseated', 'vomiting sensation', 'stomach upset'],
    'pain': ['ache', 'discomfort', 'hurt', 'soreness', 'tenderness', 'throbbing', 'aching'],
    'shortness of breath': ['trouble breathing', 'feeling breathless', 'difficulty catching breath', 'dyspnea', 'air hunger'],
    'sore throat': ['scratchy throat', 'pain in throat', 'pharyngitis', 'throat irritation'],
    'fatigue': ['feeling tired', 'exhaustion', 'low energy', 'feeling worn out', 'lethargy', 'weakness'],
    'dizziness': ['feeling dizzy', 'lightheaded', 'spinning sensation', 'vertigo', 'balance problems'],
    'chills': ['feeling cold', 'shivering', 'getting the chills', 'cold sweats'],
    'muscle pain': ['sore muscles', 'muscle ache', 'muscle discomfort', 'myalgia'],
    'joint pain': ['achy joints', 'joint discomfort', 'pain in the joints', 'arthralgia'],
    'diarrhea': ['loose stools', 'runny stools', 'frequent trips to the bathroom', 'diarrhea'],
    'constipation': ['trouble with bowel movements', 'hard stools', 'not being able to go', 'constipation'],
    'abdominal pain': ['stomach ache', 'belly pain', 'pain in the stomach', 'abdominal discomfort'],
    'numbness': ['tingling sensation', 'loss of feeling', 'numb feeling', 'paresthesia'],
    'rash': ['skin rash', 'irritated skin', 'skin breakout', 'eruption', 'skin irritation'],
    'swelling': ['swollen area', 'inflammation', 'puffiness', 'edema'],
    'heart palpitations': ['racing heart', 'fluttering heart', 'feeling heart pound', 'tachycardia'],
    'weight loss': ['losing weight', 'unintentional weight loss', 'weight drop', 'becoming fat']}

@app.route('/search', methods=['GET', 'POST'])
def search_drugs_page():
    if request.method == 'POST':
        query = request.form.get('query')

        if not query:
            flash('Please enter a search query.', 'danger')
            return redirect(url_for('search_drugs_page'))

        # Search the database for matching drugs
        results = Drug.query.filter(Drug.name.ilike(f'%{query}%')).all()

        if not results:
            flash('No drugs found matching your query.', 'warning')
            return redirect(url_for('search_drugs_page'))

        # Render search_results.html with the search results and query
        return render_template('search_results.html', results=results, query=query)

    # If it's a GET request, just show the search form
    return render_template('search.html')


# Route for handling drug search (AJAX)
# Route for handlifng drug search
@app.route('/search_drug', methods=['POST'])
def search_drug():
    search_query = request.form.get('search_query')
    
    if not search_query:
        return jsonify({"error": "Please enter a search query."}), 400

    # Search the database
    results = Drug.query.filter(Drug.name.ilike(f'%{search_query}%')).all()

    if not results:
        return jsonify({"error": "No drugs found."}), 404

    # Prepare the response data
    result_data = []
    for drug in results:
        # Convert the related symptoms to a list of symptom names
        symptoms = [symptom.name for symptom in drug.symptoms]  # Assuming drug.symptoms is a list of Symptom objects
        
        result_data.append({
            "name": drug.name,
            "uses": drug.uses,
            "symptoms": symptoms,  # List of symptom names
            "side_effects": drug.side_effects
        })

    return jsonify({"results": result_data})

# Function to search the database for matching drugs
def search_matching_drugs(user_input):
    # Debugging line to ensure input is correctly passed
    print("User input:", user_input)

    # Query the database for drugs matching the input
    drugs = Drug.query.filter(Drug.name.ilike(f'%{user_input}%')).all()
    print("Found drugs:", drugs)

    results = []
    for drug in drugs:
        # Query the related symptoms through the drug_symptom join table
        symptoms = [symptom.name for symptom in drug.symptoms]  # Accessing symptoms via relationship
        print("Drug:", drug.name, "Symptoms:", symptoms)  # Debugging line

        results.append({
            'name': drug.name,
            'symptoms': symptoms,
            'uses': drug.uses,
            'side_effects': drug.side_effects
        })

    print("Results:", results)  # Debugging line
    return results


@app.route('/list_drugs')
def list_drugs():
    drugs = Drug.query.all()
    return render_template('list_drugs.html', drugs=drugs)

@app.route('/edit_drug/<int:drug_id>', methods=['GET', 'POST'])
def edit_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)  # Fetch the drug or return a 404 if not found

    if request.method == 'POST':
        # Get data from the form
        drug.name = request.form.get('name')  # Make sure your form has a field with name='name'
        drug.uses = request.form.get('uses')  # Make sure your form has a field with name='uses'
        
        # Optional: Validate input here
        if not drug.name or not drug.uses:
            flash('Name and Uses are required!', 'danger')
            return render_template('edit_drug.html', drug=drug)
        
        # Commit changes to the database
        db.session.commit()  # Make sure you've imported db from your app

        flash('Drug updated successfully!', 'success')
        return redirect(url_for('list_drugs'))  # Redirect to the list of drugs

    # If it's a GET request, render the edit form
    return render_template('edit_drug.html', drug=drug)

# Function to normalize symptoms
def normalize_symptoms(symptoms):
    normalized_symptoms = set()
    symptom_map = {symptom.lower(): standard for standard, synonyms in SYNONYM_MAP.items() for symptom in synonyms}
    symptom_map.update({standard.lower(): standard for standard in SYNONYM_MAP.keys()})

    for symptom in symptoms:
        normalized_symptom = symptom_map.get(symptom.lower(), None)

        if normalized_symptom:
            normalized_symptoms.add(normalized_symptom)
        else:
            if "temperature is spiking" in symptom.lower():
                normalized_symptoms.add('fever')
            elif "feeling tired" in symptom.lower():
                normalized_symptoms.add('fatigue')
            else:
                normalized_symptoms.add(symptom)

    return list(normalized_symptoms)

# Function to extract symptoms from user input
def extract_symptoms(user_input):
    try:
        doc = nlp(user_input)
        matcher = PhraseMatcher(nlp.vocab)

        # Get all symptoms from the database
        all_symptoms = Symptom.query.with_entities(Symptom.name).all()

        if not all_symptoms:
            logging.error("No symptoms found in the database!")
            return []

        # Log the retrieved symptoms
        logging.info(f"Symptoms retrieved from database: {all_symptoms}")

        # Create the list of symptoms for matching
        symptom_list = [symptom[0].lower().strip() for symptom in all_symptoms]
        logging.info(f"Formatted symptom list for matching: {symptom_list}")

        # Create matching patterns for PhraseMatcher
        patterns = [nlp(symptom) for symptom in symptom_list]
        matcher.add("SYMPTOM_DB", patterns)

        # Match the user input against symptoms in the database
        matches_db = matcher(doc)
        extracted_symptoms_db = {doc[start:end].text.lower().strip() for match_id, start, end in matches_db}
        logging.info(f"Extracted symptoms from database: {extracted_symptoms_db}")

        # Extract symptoms from the synonym map
        extracted_symptoms_syn = set()
        for key, synonyms in SYNONYM_MAP.items():
            for synonym in synonyms:
                if synonym in user_input.lower():
                    extracted_symptoms_syn.add(key)
                    logging.info(f"Extracted symptom from synonym map: {key}")

        # Combine symptoms from both sources
        combined_symptoms = extracted_symptoms_db.union(extracted_symptoms_syn)

        # Log final extracted symptoms
        logging.info(f"Combined extracted symptoms: {combined_symptoms}")

        return list(combined_symptoms)

    except Exception as e:
        logging.error(f"Error extracting symptoms: {e}")
        return []

# Function to handle user input and check diseases and drugs
# Function to handle user input and check diseases and drugs
def handle_user_input(user_input):
    response = {"message": ""}  # Initialize response
    logging.info(f"Received user_input: {user_input}")

    if not user_input:
        response["message"] = "Invalid input. Please provide symptoms."
        return response

    extracted_symptoms = extract_symptoms(user_input)
    logging.info(f"Extracted symptoms: {extracted_symptoms}")

    if not extracted_symptoms:
        response["message"] = "No symptoms extracted."
        return response

    # Check for diseases associated with the extracted symptoms
    related_diseases = set()
    for symptom_name in extracted_symptoms:
        diseases = db.session.query(Disease).join(Disease.symptoms).filter(Symptom.name == symptom_name).all()
        related_diseases.update(diseases)

    if related_diseases:
        disease_info = []
        for disease in related_diseases:
            # Fetch associated information for each disease
            causes = db.session.query(Causes).filter_by(disease_id=disease.id).all()
            prognosis = db.session.query(Prognosis).filter_by(disease_id=disease.id).all()
            diagnosis = db.session.query(Diagnosis).filter_by(disease_id=disease.id).all()
            differential_diagnosis = db.session.query(DifferentialDiagnosis).filter_by(disease_id=disease.id).all()
            treatment_options = db.session.query(TreatmentOptions).filter_by(disease_id=disease.id).all()
            disease_symptoms = db.session.query(Symptom).join(disease_symptom).filter(Symptom.diseases.contains(disease)).all()

            # Retrieve symptom types associated with each symptom in the disease
            symptom_types = [SymptomType.query.get(symptom.symptom_type_id).name for symptom in disease_symptoms if symptom.symptom_type_id]

            # Append the disease information to the response
            disease_info.append({
                "name": disease.disease_name,
                "description": disease.description,
                "causes": [cause.cause_description for cause in causes],
                "prognosis": [prog.prognosis_description for prog in prognosis],
                "diagnosis": [diag.diagnosis_description for diag in diagnosis],
                "differential_diagnosis": [dd.differential_description for dd in differential_diagnosis],
                "treatment_options": [treatment.treatment_description for treatment in treatment_options],
                "symptom_types": symptom_types
            })

        response["diseases"] = disease_info
        return response  # Return early if diseases are found

    # Check for symptom categories if no diseases are found
    symptom_categories = set()
    for symptom in extracted_symptoms:
        categories = db.session.query(SymptomCategory).join(Symptom).filter(Symptom.name == symptom).all()
        symptom_categories.update(categories)

    if symptom_categories:
        category_info = []
        for category in symptom_categories:
            drugs = db.session.query(Drug).join(Drug.symptoms).filter(Symptom.symptom_category_id == category.id).all()

            drug_info = []
            for drug in drugs:
                symptom_types = []
                drug_symptoms = db.session.query(Symptom).filter(Symptom.id == drug.id).all()

                for symptom in drug_symptoms:
                    symptom_type = SymptomType.query.get(symptom.symptom_type_id)
                    if symptom_type:
                        symptom_types.append(symptom_type.name)

                drug_info.append({
                    "name": drug.name,
                    "uses": drug.uses,
                    "side_effects": drug.side_effects,
                    "symptom_types": symptom_types
                })

            category_info.append({
                "category": category.name,
                "suitable_drugs": drug_info
            })

        response["symptom_categories"] = category_info
        return response  # Return early if symptom categories are found

    # If no symptom categories are found, check for suitable drugs directly
    suitable_drugs = set()
    for symptom in extracted_symptoms:
        drugs = db.session.query(Drug).join(Drug.symptoms).filter(Symptom.name == symptom).all()
        suitable_drugs.update(drugs)

    if suitable_drugs:
        drug_info = []
        for drug in suitable_drugs:
            symptom_types = []
            drug_symptoms = db.session.query(Symptom).filter(Symptom.id == drug.id).all()

            for symptom in drug_symptoms:
                symptom_type = SymptomType.query.get(symptom.symptom_type_id)
                if symptom_type:
                    symptom_types.append(symptom_type.name)

            drug_info.append({
                "name": drug.name,
                "uses": drug.uses,
                "side_effects": drug.side_effects,
                "symptom_types": symptom_types
            })

        response["drugs"] = drug_info
    else:
        response["drugs"] = "No suitable drugs found for the extracted symptoms."

    return response

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        logging.info(f"Received user_input: {data.get('user_input')}")

        user_input = data.get('user_input')

        if not user_input:
            return jsonify({"error": "No input provided"}), 400  # Return error if no input

        # Handle user input
        response_data = handle_user_input(user_input)

        # Return the response
        return jsonify({"response": response_data})

    except Exception as e:
        logging.error(f"Error processing chat: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
@app.route('/chat', methods=['GET'])
def chat_interface():
    return render_template('chat.html')  # Serve the chat interface on a separate GET request

@app.route('/add_drug', methods=['POST'])
def add_drug():
    # Get data from the form
    drug_name = request.form.get('drug_name')
    side_effect = request.form.get('side_effects')
    drug_uses = request.form.get('drug_uses')

    # Validate required fields
    if not drug_name or not drug_uses:
        flash('Drug name and uses are required.', 'danger')
        return redirect(url_for('show_add_drug_form'))

    try:
        # Create a new drug instance
        new_drug = Drug(
            name=drug_name,
            uses=drug_uses,
            side_effects=side_effect
        )
        
        # Add and commit to the database
        db.session.add(new_drug)
        db.session.commit()
        
        flash('Drug added successfully!', 'success')
        return redirect(url_for('home'))
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('show_add_drug_form'))

@app.route('/add_drug_form', methods=['GET'])
def show_add_drug_form():
    return render_template('add_drug.html')  # Renders the HTML form for adding a drug

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

