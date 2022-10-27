from flask import *
from flask_sqlalchemy import *
from werkzeug.utils import secure_filename
from flask_mail import *

UPLOADFOLDER = "./static/assets/images" #'.\\static\\assets\\images'
ALLOWEDEXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

app.secret_key = "***"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.sqlite3'
app.config['UPLOAD_FOLDER'] = UPLOADFOLDER

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "email@gmail.com"
app.config['MAIL_PASSWORD'] = "some secret password"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

db = SQLAlchemy(app)
class Product(db.Model):
	id = db.Column('product_id', db.Integer, primary_key = True)
	name = db.Column(db.String(30))
	price = db.Column(db.Integer)
	desc = db.Column(db.String(70))
	photoName = db.Column(db.String(50))

	def __init__(self, name, price, desc, photoName):
		self.name = name
		self.price = price
		self.desc = desc
		self.photoName = photoName

class UserRequest(db.Model):
	id = db.Column('product_id', db.Integer, primary_key = True)
	name = db.Column(db.String(35))
	requested = db.Column(db.String(200))
	contacts = db.Column(db.String(100))

	def __init__(self, name, requested, contacts):
		self.name = name
		self.requested = requested
		self.contacts = contacts

def IdToProduct(id):
	return id

def IdsToProducts(ids):
	res = ""
	for ID in ids.split(";"):
		if len(ID) > 0:
			res += IdToProduct(ID) + "; "

	return res

app.jinja_env.globals.update(IdsToProducts=IdsToProducts)

def AllowedFile(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWEDEXTENSIONS


@app.before_request
def before_request():
	if not request.is_secure:
		url = request.url.replace('http://', 'https://', 1)
		code = 301
		return redirect(url, code=code)

@app.route("/")
@app.route("/home")
def MainPage():
	try:
		return render_template("index.html", products=Product.query.all()[-3:]) #[:5])
	except:
		return render_template("index.html")

@app.route("/products")
def ProductPage():
	return render_template("products.html", products=Product.query.all())

@app.route("/contact", methods=["GET", "POST"])
def ContactPage():
	if request.method == "POST":
		if "secret code is entered":
			session["admin"] = "confirmed"
			return redirect("/admin")

		msg = Message("New message from site PrayForUA", sender="prayuaprint@gmail.com", recipients=["prayuaprint@gmail.com"])
		msg.html = "<strong>Name:</strong> " + str(request.form["name"]) + "<br><strong>Phone:</strong> " + \
			str(request.form["phone"]) + "<br><h3>Message</h3>" + str(request.form["message"]) + \
			"<br><a href='" + request.host_url + "'>Go to site</a>"
		mail.send(msg)

		return render_template("contact.html", msg="Thanks for your message!")
	else:
		return render_template("contact.html")

# Admin pages

@app.route("/admin")
def AdminPage():
	try:
		if session and session["admin"] == "confirmed":
			try:
				return render_template("admin.html", products=Product.query.all(), userRequests=UserRequest.query.all()[::-1]) #.reverse())
			except Exception as e:
				print(e)
				return render_template("admin.html")
		else:
			return redirect("/")
	except:
		return redirect("/")

@app.route("/quit")
def Quit():
	session.clear()
	return redirect("/")

@app.route("/removeProduct/<int:productID>")
def RemoveProduct(productID: int):
	if session["admin"] == "confirmed":
		Product.query.filter_by(id=productID).delete()
		db.session.commit()
		return redirect("/admin")
	else:
		return redirect("/")

@app.route("/removeRequest/<int:productID>")
def RemoveRequest(productID: int):
	if session["admin"] == "confirmed":
		UserRequest.query.filter_by(id=productID).delete()
		db.session.commit()
		return redirect("/admin")
	else:
		redirect("/")

@app.route("/uploadProduct", methods=["POST"])
def UploadProduct():
	if session["admin"] == "confirmed":
		if "image" not in request.files:
			return redirect("/admin")
		file = request.files["image"]
		if file.filename == '':
			return redirect("/admin")
		if file and AllowedFile(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

		db.session.add(Product(request.form["name"], request.form["price"], request.form["desc"], filename))
		db.session.commit()

		return redirect("/admin")
	else:
		return redirect("/")

@app.route("/postRequest", methods=["POST"])
def PostRequest():
	# print(request.form["cartIDs"], request.form["info"])
	# for r in request.form: print(">", r, request.form[r])
	db.session.add(UserRequest(request.form["name"], request.form["cartIDs"], request.form["info"]))
	db.session.commit()

	msg = Message("New order from site PrayForUA", sender="prayuaprint@gmail.com", recipients=["prayuaprint@gmail.com"])
	# Better add "/admin"?
	msg.html = "<strong>You got a new order from <i>" + str(request.form["name"]) + "</i>: </strong> " + str(request.form["cartIDs"]) + ", " + str(request.form["info"]) + "<br><a href='" + request.host_url + "'>Go to site</a>"
	mail.send(msg)
	return redirect("/")

# Special pages

@app.errorhandler(404)
def PageNotFound(e):
	return render_template("error.html", id=404, info=e), 404

if __name__ == "__main__":
	app.run(debug=False)