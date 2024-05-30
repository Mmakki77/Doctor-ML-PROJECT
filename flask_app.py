from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import pickle


model = pickle.load(open('model.pkl', 'rb'))


app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = '154.56.34.16'
app.config['MYSQL_USER'] = 'u782696289_doctor_ml'
app.config['MYSQL_PASSWORD'] = 'Makki1298'
app.config['MYSQL_DB'] = 'u782696289_doctor_ml'

mysql = MySQL(app)

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT S_ID, name FROM symptoms")
    symptoms = cur.fetchall()
    cur.close()
    return render_template('index.html', symptoms=symptoms)

@app.route('/prediction', methods=['POST'])
def prediction():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM symptoms")
        symptom_names = [row[0] for row in cur.fetchall()]
        cur.close()
        
        symptoms_array = []
        
        for symptom in symptom_names: 
            if symptom in request.form:
                symptoms_array.append(1)
            else:
                symptoms_array.append(0)
                
        prediction = model.predict([symptoms_array])
        
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT details FROM disease WHERE name = %s", (prediction[0],))
        disease_details = cur2.fetchone()[0]
        cur2.close()

        # GETTING TREATMENTS FOR EACH DISEASE
        cur3_1 = mysql.connection.cursor()
        cur3_1.execute("SELECT D_ID FROM disease WHERE name = %s", (prediction[0],))
        disease_id = cur3_1.fetchall()[0][0]
        cur3_1.close()

        cur3_2 = mysql.connection.cursor()
        cur3_2.execute("SELECT T_ID FROM treatments_of_disease WHERE D_ID = %s", (disease_id,))
        treatment_ids = [row[0] for row in cur3_2.fetchall()]
        cur3_2.close()

        cur3_3 = mysql.connection.cursor()
        cur3_3.execute("SELECT details FROM treatments WHERE T_ID IN (%s)" % ', '
                       .join(['%s'] * len(treatment_ids)), treatment_ids)
        treatments = [row[0] for row in cur3_3.fetchall()]
        cur3_3.close()

        # GETTING LIST OF DOCTORS FOR EACH DISEASE
        cur4_1 = mysql.connection.cursor()
        cur4_1.execute("SELECT D_ID FROM disease WHERE name = %s", (prediction[0],))
        disease_id = cur4_1.fetchall()[0][0]
        cur4_1.close()

        cur4_2 = mysql.connection.cursor()
        cur4_2.execute("SELECT Doc_ID FROM treatments_provided WHERE D_ID = %s", (disease_id,))
        doctors_ids = [row[0] for row in cur4_2.fetchall()]
        cur4_2.close()

        cur4_3 = mysql.connection.cursor()
        cur4_4 = mysql.connection.cursor()
        if doctors_ids:
            cur4_3.execute("SELECT name FROM doctors WHERE Doc_ID IN ({})".format(",".join(["%s"] * len(doctors_ids))), tuple(doctors_ids))
            cur4_4.execute("SELECT hospital FROM doctors WHERE Doc_ID IN ({})".format(",".join(["%s"] * len(doctors_ids))), tuple(doctors_ids))
            doctors = [row[0] for row in cur4_3.fetchall()]
            hospitals = [row[0] for row in cur4_4.fetchall()]
        else:
            doctors = 'No available doctors at the moment'
            hospitals = 'No available hospitals at the moment'
        cur4_3.close()
        cur4_4.close()
        

    return render_template('prediction.html', prediction=prediction[0], disease_details=disease_details,
                            treatments = [treatment.capitalize() for treatment in treatments], doctors=doctors,
                            hospitals=hospitals[0])


@app.route('/doctors')
def doctors():
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM doctors")
    doctors = cur.fetchall()
    cur.close()

    cur1= mysql.connection.cursor()
    cur1.execute("SELECT field_of_work FROM doctors")
    fields = cur1.fetchall()
    cur1.close()
    
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT hospital FROM doctors")
    hospitals = cur2.fetchall()
    cur2.close()


    return render_template('doctors.html', doctors=doctors,
                            fields=fields, hospitals=hospitals)


if __name__ == '__main__':
    app.run(debug=True)