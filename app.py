from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'smartcampus123'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_campus_lost_found"
)

cursor = db.cursor()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        sql = "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)"
        values = (name, email, password, 'user')

        cursor.execute(sql, values)
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"
        values = (email, password)

        cursor.execute(sql, values)
        user = cursor.fetchone()

        if user:

            session['user'] = email
            session['role'] = user[4]

            # ADMIN
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))

            # USER
            else:
                return redirect(url_for('dashboard'))

        else:
            return "Invalid Login Details"

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':

            session['admin'] = True

            return redirect('/admin_dashboard')

        else:
            return "Invalid Admin Credentials"

    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin_login')

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM lost_items")
    total_lost = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM found_items")
    total_found = cursor.fetchone()[0]

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found
    )


@app.route('/view_lost_items')
def view_lost_items():

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM lost_items")

    items = cursor.fetchall()

    print(items)

    return render_template('view_lost_items.html', items=items)

@app.route('/view_found_items')
def view_found_items():

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM found_items")

    items = cursor.fetchall()

    return render_template('view_found_items.html', items=items)

# ---------------- VIEW CLAIMS ----------------
@app.route('/view_claims')
def view_claims():

    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT claims.claim_id,
           claims.claim_status,
           users.name,
           found_items.item_name
    FROM claims
    JOIN users ON claims.claimant_id = users.user_id
    JOIN found_items ON claims.found_id = found_items.found_id
    """

    cursor.execute(query)

    claims = cursor.fetchall()

    return render_template('view_claims.html', claims=claims)



# ---------------- LOST ITEM ----------------
@app.route('/lost_item', methods=['GET', 'POST'])
def lost_item():

    if request.method == 'POST':

        item_name = request.form['item_name']
        category = request.form['category']
        description = request.form['description']
        location = request.form['location']
        date_lost = request.form['date_lost']

        sql = """
        INSERT INTO lost_items
        (item_name, category, description, location, date_lost)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (item_name, category, description, location, date_lost)

        cursor.execute(sql, values)
        db.commit()

        return "Lost Item Submitted Successfully!"

    return render_template('lost_item.html')


# ---------------- FOUND ITEM ----------------
@app.route('/found_item', methods=['GET', 'POST'])
def found_item():

    if request.method == 'POST':

        item_name = request.form['item_name']
        category = request.form['category']
        description = request.form['description']
        location = request.form['location']
        date_found = request.form['date_found']

        sql = """
        INSERT INTO found_items
        (item_name, category, description, location, date_found)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (item_name, category, description, location, date_found)

        cursor.execute(sql, values)
        db.commit()

        return "Found Item Submitted Successfully!"

    return render_template('found_item.html')


# ---------------- SEARCH ----------------
@app.route('/search_item', methods=['GET', 'POST'])
def search_item():

    items = []

    if request.method == 'POST':
        item_name = request.form['item_name']

        query = "SELECT * FROM lost_items WHERE item_name LIKE %s"
        cursor.execute(query, ('%' + item_name + '%',))

        items = cursor.fetchall()

    return render_template('search_item.html', items=items)

# ---------------- DELETE LOST ITEM ----------------
@app.route('/delete_lost_item/<int:item_id>')
def delete_lost_item(item_id):

    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor.execute("DELETE FROM lost_items WHERE lost_id = %s", (item_id,))
    db.commit()

    return redirect(url_for('view_lost_items'))

# ---------------- DELETE FOUND ITEM ----------------
@app.route('/delete_found_item/<int:item_id>')
def delete_found_item(item_id):

    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor.execute("DELETE FROM found_items WHERE found_id = %s", (item_id,))
    db.commit()

    return redirect(url_for('view_found_items'))

# ---------------- CLAIM ITEM ----------------
@app.route('/claim_item/<int:found_id>')
def claim_item(found_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    # Logged-in user email
    email = session['user']

    # Get user ID
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        claimant_id = user[0]

    # Check if already claimed
    cursor.execute(
        "SELECT * FROM claims WHERE found_id = %s AND claimant_id = %s",
        (found_id, claimant_id)
    )

    existing_claim = cursor.fetchone()

    if existing_claim:
        return "You have already claimed this item!"

    # Insert claim request
    sql = """
    INSERT INTO claims (found_id, claimant_id, claim_status)
    VALUES (%s, %s, %s)
    """

    values = (found_id, claimant_id, 'Pending')

    cursor.execute(sql, values)
    db.commit()

    return "Claim Request Submitted Successfully!"

    return "User not found!"

# ---------------- APPROVE CLAIM ----------------
@app.route('/approve_claim/<int:claim_id>')
def approve_claim(claim_id):

    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Update claim status
    cursor.execute(
        "UPDATE claims SET claim_status = 'Approved' WHERE claim_id = %s",
        (claim_id,)
    )

    # Get found item id
    cursor.execute(
        "SELECT found_id FROM claims WHERE claim_id = %s",
        (claim_id,)
    )

    found_item = cursor.fetchone()

    # Update found item status
    cursor.execute(
        "UPDATE found_items SET status = 'Claimed' WHERE found_id = %s",
        (found_item[0],)
    )

    db.commit()

    return redirect(url_for('view_claims'))


# ---------------- REJECT CLAIM ----------------
@app.route('/reject_claim/<int:claim_id>')
def reject_claim(claim_id):

    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor.execute(
        "UPDATE claims SET claim_status = 'Rejected' WHERE claim_id = %s",
        (claim_id,)
    )

    db.commit()

    return redirect(url_for('view_claims'))


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)