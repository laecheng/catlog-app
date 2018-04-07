from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catlog, CatlogItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///catlog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/catlog')
def showCatlogs():
    catlogs = session.query(Catlog).order_by(asc(Catlog.name))
    return render_template('catlogs.html', catlogs=catlogs)

@app.route('/catlog/<int:catlog_id>/')
@app.route('/catlog/<int:catlog_id>/item/')
def showItem(catlog_id):
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    items = session.query(CatlogItem).filter_by(catlog_id=catlog_id).all()
    return render_template('item.html', items=items, catlog=catlog)

@app.route('/catlog/<int:catlog_id>/<int:item_id>/')
def showItemInfo(catlog_id, item_id):
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    item = session.query(CatlogItem).filter_by(id=item_id).one()
    return render_template('itemDescription.html', item=item, catlog=catlog)

@app.route('/catlog/<int:catlog_id>/item/new/', methods=['GET', 'POST'])
def newItem(catlog_id):
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    if request.method == 'POST':
        newItem = CatlogItem(name=request.form['name'],
                             description=request.form['description'],
                             catlog_id=catlog_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItem', catlog_id=catlog_id))
    else:
        return render_template('newItem.html', catlog=catlog)


@app.route('/catlog/<int:catlog_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(catlog_id, item_id):
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    editItem = session.query(CatlogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        return redirect(url_for('showItemInfo', catlog_id=catlog_id, item_id=item_id))
    else:
        return render_template('editItem.html', catlog=catlog, editItem=editItem)


@app.route('/catlog/<int:catlog_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(catlog_id, item_id):
    catlog = session.query(Catlog).filter_by(id=catlog_id).one()
    itemToDelete = session.query(CatlogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItem', catlog_id=catlog_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete, catlog=catlog)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
