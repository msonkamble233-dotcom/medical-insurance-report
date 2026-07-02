

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    Response
)


import csv
import io
from db import get_connection


app = Flask(__name__)

import os
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

@app.route('/dashboard')
def dashboard():
    return redirect('/')
@app.route('/')
def home():

    if 'username' not in session:
        return redirect('/login_page')

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM patients")
    total_patients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM policies")
    total_policies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM hospitals")
    total_hospitals = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM claims WHERE status='Approved'"
    )
    approved_claims = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM claims WHERE status='Rejected'"
    )
    rejected_claims = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM claims WHERE status='Pending'"
    )
    pending_claims = cur.fetchone()[0]
    
    cur.execute("""
    SELECT COUNT(*)
    FROM claims
    WHERE fraud_status = 'Normal'
    """)
    normal_claims = cur.fetchone()[0]

    cur.execute("""
    SELECT COUNT(*)
    FROM claims
    WHERE fraud_status = 'Suspicious'
    """)
    suspicious_claims = cur.fetchone()[0] 
    
    cur.close()
    conn.close()

    return render_template(
        'home.html',
        total_patients=total_patients,
        total_policies=total_policies,
        total_hospitals=total_hospitals,
        total_claims=total_claims,
        approved_claims=approved_claims,
        rejected_claims=rejected_claims,
        pending_claims=pending_claims,
        normal_claims=normal_claims,
        suspicious_claims=suspicious_claims
    )
@app.route('/add_patient')
def add_patient():
    return render_template('add_patient.html')


@app.route('/save_patient', methods=['POST'])
def save_patient():

    full_name = request.form['full_name']
    age = request.form['age']
    gender = request.form['gender']
    phone = request.form['phone']
    email = request.form['email']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO patients
        (full_name, age, gender, phone, email)
        VALUES (%s,%s,%s,%s,%s)
    """,
    (full_name, age, gender, phone, email))

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/patients')


@app.route('/patients')
def patients():

    search = request.args.get('search', '')

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM patients
        WHERE full_name ILIKE %s
           OR phone ILIKE %s
           OR email ILIKE %s
        ORDER BY patient_id
    """,
    (
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%'
    ))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'patients.html',
        patients=data,
        search=search
    )
@app.route('/add_policy')
def add_policy():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'add_policy.html',
        patients=patients
    )
@app.route('/save_policy', methods=['POST'])
def save_policy():

    policy_number = request.form['policy_number']
    patient_id = request.form['patient_id']
    coverage_amount = request.form['coverage_amount']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO policies
        (
            policy_number,
            coverage_amount,
            start_date,
            end_date,
            patient_id
        )
       VALUES(%s,%s,%s,%s,%s)
    """,
    (
        policy_number,
    coverage_amount,
    start_date,
    end_date,
    patient_id
    ))

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/policies')

@app.route('/policies')
def policies():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        po.policy_id,
        po.policy_number,
        pa.full_name,
        po.coverage_amount,
        po.start_date,
        po.end_date
    FROM policies po
    JOIN patients pa
        ON po.patient_id = pa.patient_id
    ORDER BY po.policy_id
""")
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'policies.html',
        policies=data
    )

@app.route('/add_hospital')
def add_hospital():
    return render_template('add_hospital.html')


@app.route('/save_hospital', methods=['POST'])
def save_hospital():

    hospital_name = request.form['hospital_name']
    city = request.form['city']
    contact_number = request.form['contact_number']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO hospitals
        (
            hospital_name,
            city,
            contact_number
        )
        VALUES
        (%s,%s,%s)
    """,
    (
        hospital_name,
        city,
        contact_number
    ))

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/hospitals')

@app.route('/add_claim')
def add_claim():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)
    patients = cur.fetchall()

    cur.execute("""
        SELECT policy_id, policy_number
        FROM policies
        ORDER BY policy_number
    """)
    policies = cur.fetchall()

    cur.execute("""
        SELECT hospital_id, hospital_name
        FROM hospitals
        ORDER BY hospital_name
    """)
    hospitals = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'add_claim.html',
        patients=patients,
        policies=policies,
        hospitals=hospitals
    )

@app.route('/save_claim', methods=['POST'])
def save_claim():

    patient_id = request.form['patient_id']
    policy_id = request.form['policy_id']
    hospital_id = request.form['hospital_id']
    claim_amount = request.form['claim_amount']
    if float(claim_amount) > 100000:
        fraud_status = "Suspicious"
    else:
         fraud_status = "Normal"

    claim_date = request.form['claim_date']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO claims
        (
             patient_id,
        policy_id,
        hospital_id,
        claim_amount,
        claim_date,
        status,
        fraud_status
        )
        VALUES
         (%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        patient_id,
    policy_id,
    hospital_id,
    claim_amount,
    claim_date,
    'Pending',
    fraud_status
    ))

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/claims')

@app.route('/claims')
def claims():

    search = request.args.get('search', '')
    status = request.args.get('status', '')

    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT
        c.claim_id,
        p.full_name,
        po.policy_number,
        h.hospital_name,
        c.claim_amount,
        c.claim_date,
        c.status,
        c.fraud_status
    FROM claims c
    JOIN patients p
        ON c.patient_id = p.patient_id
    JOIN policies po
        ON c.policy_id = po.policy_id
    JOIN hospitals h
        ON c.hospital_id = h.hospital_id
    WHERE
        (
            CAST(c.claim_id AS TEXT) ILIKE %s
            OR p.full_name ILIKE %s
        )
    """

    params = [
        '%' + search + '%',
        '%' + search + '%'
    ]

    if status == "Approved":
        query += " AND c.status='Approved'"

    elif status == "Rejected":
        query += " AND c.status='Rejected'"

    elif status == "Pending":
        query += " AND c.status='Pending'"

    elif status == "Suspicious":
        query += " AND c.fraud_status='Suspicious'"

    query += " ORDER BY c.claim_id"

    cur.execute(query, params)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'claims.html',
        claims=data,
        search=search
    )

@app.route('/monthly_report')
def monthly_report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            TO_CHAR(claim_date, 'Month') AS month,
            COUNT(*) AS total_claims
        FROM claims
        GROUP BY TO_CHAR(claim_date, 'Month')
        ORDER BY MIN(claim_date)
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'monthly_report.html',
        reports=data
    )
@app.route('/approve_claim/<int:id>')
def approve_claim(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE claims
        SET status='Approved'
        WHERE claim_id=%s
    """,
    (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/claims')

@app.route('/reject_claim/<int:id>')
def reject_claim(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE claims
        SET status='Rejected'
        WHERE claim_id=%s
    """,
    (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/claims')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE username=%s
        AND password=%s
    """,
    (username,password)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if user:

        session['username'] = username

        return redirect('/')

    else:

        return "Invalid Login"
    
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login_page')



@app.route('/fraud_report')
def fraud_report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            fraud_status,
            COUNT(*)
        FROM claims
        GROUP BY fraud_status
        ORDER BY fraud_status
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'fraud_report.html',
        reports=data
    )
@app.route('/hospitals')
def hospitals():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM hospitals
        ORDER BY hospital_id
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'hospitals.html',
        hospitals=data
    )   
@app.route('/export_monthly_csv')
def export_monthly_csv():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            TO_CHAR(claim_date, 'Month') AS month,
            COUNT(*) AS total_claims
        FROM claims
        GROUP BY TO_CHAR(claim_date, 'Month')
        ORDER BY MIN(claim_date)
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        'Month',
        'Total Claims'
    ])

    for report in reports:
        writer.writerow(report)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition':
            'attachment; filename=monthly_report.csv'
        }
    )
@app.route('/export_claims_csv')
def export_claims_csv():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.claim_id,
            p.full_name,
            h.hospital_name,
            c.claim_amount,
            c.status,
            c.fraud_status
        FROM claims c
        JOIN patients p
            ON c.patient_id = p.patient_id
        JOIN hospitals h
            ON c.hospital_id = h.hospital_id
        ORDER BY c.claim_id
    """)

    claims = cur.fetchall()

    cur.close()
    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        'Claim ID',
        'Patient Name',
        'Hospital Name',
        'Claim Amount',
        'Status',
        'Fraud Status'
    ])

    for claim in claims:
        writer.writerow(claim)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition':
            'attachment; filename=claims_report.csv'
        }
    )
@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/patient_report')
def patient_report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.full_name,
            COUNT(c.claim_id) AS total_claims,
            COALESCE(SUM(c.claim_amount), 0) AS total_amount
        FROM patients p
        LEFT JOIN claims c
            ON p.patient_id = c.patient_id
        GROUP BY p.full_name
        ORDER BY total_amount DESC
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'patient_report.html',
        reports=reports
    )

@app.route('/export_patient_csv')
def export_patient_csv():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.full_name,
            COUNT(c.claim_id) AS total_claims,
            COALESCE(SUM(c.claim_amount), 0) AS total_amount
        FROM patients p
        LEFT JOIN claims c
            ON p.patient_id = c.patient_id
        GROUP BY p.full_name
        ORDER BY total_amount DESC
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Patient Name',
        'Total Claims',
        'Total Amount'
    ])

    for report in reports:
        writer.writerow(report)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition':
            'attachment; filename=patient_report.csv'
        }
    )
@app.route('/hospital_report')
def hospital_report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            h.hospital_name,
            COUNT(c.claim_id) AS total_claims,
            COALESCE(SUM(c.claim_amount), 0) AS total_amount
        FROM hospitals h
        LEFT JOIN claims c
            ON h.hospital_id = c.hospital_id
        GROUP BY h.hospital_name
        ORDER BY total_amount DESC
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'hospital_report.html',
        reports=reports
    )
@app.route('/export_hospital_csv')
def export_hospital_csv():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            h.hospital_name,
            COUNT(c.claim_id) AS total_claims,
            COALESCE(SUM(c.claim_amount), 0) AS total_amount
        FROM hospitals h
        LEFT JOIN claims c
            ON h.hospital_id = c.hospital_id
        GROUP BY h.hospital_name
        ORDER BY total_amount DESC
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        'Hospital Name',
        'Total Claims',
        'Total Amount'
    ])

    for report in reports:
        writer.writerow(report)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition':
            'attachment; filename=hospital_report.csv'
        }
    )
@app.route('/status_report')
def status_report():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        status,
        COUNT(*) AS total_claims
    FROM claims
    GROUP BY status
    ORDER BY total_claims DESC
""")

    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'status_report.html',
        reports=reports
    )

@app.route('/export_status_csv')
def export_status_csv():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            status,
            COUNT(*) AS total_claims
        FROM claims
        GROUP BY status
        ORDER BY total_claims DESC
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Claim Status',
        'Total Claims'
    ])

    for report in reports:
        writer.writerow(report)

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition':
            'attachment; filename=status_report.csv'
        }
    )
if __name__ == '__main__':
    app.run(debug=True)