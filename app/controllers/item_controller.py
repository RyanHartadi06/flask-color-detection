from flask import render_template, redirect, request, url_for
from app import models

def index():
    items = models.get_all_items()
    return render_template('index.html', items=items)

def create():
    if request.method == 'POST':
        name = request.form['name']
        models.add_item(name)
        return redirect(url_for('main.index'))
    return render_template('create.html')

def edit(item_id):
    item = models.get_item_by_id(item_id)
    if request.method == 'POST':
        new_name = request.form['name']
        models.update_item(item_id, new_name)
        return redirect(url_for('main.index'))
    return render_template('edit.html', item=item)

def delete(item_id):
    models.delete_item(item_id)
    return redirect(url_for('main.index'))
