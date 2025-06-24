from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

class DrugForm(FlaskForm):
    name = StringField('✨ Drug Name ✨', 
        validators=[DataRequired(message="Drug name is required!")],
        render_kw={"placeholder": "Enter the name of the drug...", "class": "form-control"})
    
    symptoms = StringField('🤕 Symptoms 🤕', 
        validators=[DataRequired(message="Symptoms are required!")],
        render_kw={"placeholder": "Enter symptoms for the drug...", "class": "form-control"})
    
    uses = TextAreaField('💊 Drug Uses 💊', 
        validators=[DataRequired(message="Drug uses are required!"), 
                    Length(min=5, max=200, message="Description should be between 5 and 200 characters.")],
        render_kw={"placeholder": "Describe the uses of the drug...", "rows": 4, "class": "form-control"})
    
    side_effects = TextAreaField('⚠️ Side Effects ⚠️', 
        validators=[DataRequired(message="Side effects are required!")],
        render_kw={"placeholder": "List any side effects...", "rows": 4, "class": "form-control"})
    
    submit = SubmitField('🚀 Submit 🚀', render_kw={"class": "btn btn-primary btn-lg btn-block"})

class SearchForm(FlaskForm):
    query = StringField('Search', 
        validators=[DataRequired()],
        render_kw={"placeholder": "Search for a drug...", "class": "form-control"})
    
    submit = SubmitField('🔍 Search', render_kw={"class": "btn btn-secondary"})
