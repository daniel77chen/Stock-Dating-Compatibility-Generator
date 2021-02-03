import os

from flask import (
	Flask, render_template, url_for, session, redirect, request,
	flash,
)
from finnhub import Client as make_client
"""
Elvis' Finnhub API keys
Sandbox API Key: sandbox_c0bfrg748v6to0roveg0
Regular API Key: c0bfrg748v6to0roveg0

There are limits! See documentation:
https://finnhub.io/docs/api
"""

def create_app():
	app = Flask(__name__, instance_relative_config=True)
	finnhub_client = make_client(api_key="sandbox_c0bfrg748v6to0roveg0")

	# Secret key for session
	app.config['SECRET_KEY'] = os.urandom(24)

	# Fix browser caching for css
	@app.context_processor
	def override_url_for():
		return dict(url_for=dated_url_for)

	def dated_url_for(endpoint, **values):
		if endpoint == 'static':
			filename = values.get('filename', None)
			if filename:
				file_path = os.path.join(app.root_path,
									 endpoint, filename)
				values['q'] = int(os.stat(file_path).st_mtime)
		return url_for(endpoint, **values)

	# Home page
	@app.route('/', methods=['GET', 'POST'])
	def index():
		if request.method == 'POST':
			# DONE: input validation
			stock_symbol = request.form['stock'].upper()
			volume = request.form['volume']
			symbol_quote = finnhub_client.quote(stock_symbol)
			error = None
			if not volume.isdigit():
				error = "Number of Shares must be a positive integer"
			elif int(volume) < 1:
				error = "Number of Shares must be a positive integer"
			elif symbol_quote['c'] == 0:
				error = "Invalid stock symbol: {}".format(stock_symbol)

			# TODO: Send form results to DB, fetch all added stocks and display them
			# Code below uses Flask session to store data which can be moved to
			# DB later.
			if error is None:
				if 'stock_dict' in session:
					(session['stock_dict'])[stock_symbol] = volume
					session.modified = True
				else:
					session['stock_dict'] = {stock_symbol: volume}
				return render_template('index.html', stock_dict=session['stock_dict'])
			
			flash(error)
			if 'stock_dict' in session and session['stock_dict']:
				return render_template('index.html', stock_dict=session['stock_dict'])
			return render_template('index.html', stock_dict=None)
		else:
			if 'stock_dict' in session and session['stock_dict']:
				return render_template('index.html', stock_dict=session['stock_dict'])
			return render_template('index.html', stock_dict=None)

	# Results page (generates session id or code)
	@app.route('/results')
	def results():
		print(session)
		if 'code' in session:
			return render_template('results.html', code=session['code'], warning=True)
		else:
			code = 'QWERTY'  # TODO: generate random code
			session['code'] = code
			# TODO: Update DB here
			# Person sends link to partner
			print(session)
			return render_template('results.html', code=code)
	
	# Remove stock symbol from table
	@app.route('/remove/<key>')
	def remove(key):
		if 'stock_dict' in session:
			session['stock_dict'].pop(key, None)
			session.modified = True
		return redirect(url_for('index'))

	@app.route('/waiting/<code>')
	def wait_for_partner(code):
		# TODO: check if partner is done
		# if done, return redirect(url_for('partner_validated', code=code))
		# if not, return the results page again
		if 'code' in session:
			return redirect(url_for('results'))
		else:
			return 'yikes something went wrong'

	@app.route('/compare/<code>')
	def partner_validated(code):
		print(session)
		return 'partner finished'

	return app