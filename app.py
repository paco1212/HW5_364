# Francisco "Paco" Gallardo
# SI364 - Building Interactive Applications
# University of Michigan School of Information

import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField, IntegerField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

############################
# Application configurations
############################
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hard to guess string from si364 + some extra string characters just for added fun :)'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/frgaHW5"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


#########################
##### Set up Models #####
#########################

## All provided.

# Association table
on_list = db.Table('on_list',db.Column('item_id',db.Integer, db.ForeignKey('items.id')),db.Column('list_id',db.Integer, db.ForeignKey('lists.id')))

class TodoList(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(225))
    items = db.relationship('TodoItem',secondary=on_list,backref=db.backref('lists',lazy='dynamic'),lazy='dynamic')

class TodoItem(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(225))
    priority = db.Column(db.Integer)


########################
##### Set up Forms #####
########################

# Form to create a todo list
class TodoListForm(FlaskForm):
    name = StringField("What is the title of this TODO List?", validators=[Required()])
    items = TextAreaField("Enter your TODO list items in the following format: Description, Priority -- separated by newlines")
    submit = SubmitField("Submit")

# An UpdateButtonForm class for use to update todo items
class UpdateButtonForm(FlaskForm):
    submit = SubmitField("Update")

class UpdateTodoListItem(FlaskForm):
    new_priority = IntegerField("What is the new priority score of this item", validators = [Required()])
    submit = SubmitField("Update")


# A DeleteButtonForm class for use to delete todo items
class DeleteButtonForm(FlaskForm):
    delete = SubmitField("Delete")



################################
####### Helper Functions #######
################################

def get_or_create_item(item_string):
    elements = [x.strip().rstrip() for x in item_string.split(",")]
    item = TodoItem.query.filter_by(description=elements[0]).first()
    if item:
        return item
    else:
        item = TodoItem(description=elements[0],priority=elements[-1])
        db.session.add(item)
        db.session.commit()
        return item

def get_or_create_todolist(title, item_strings=[]):
    l = TodoList.query.filter_by(title=title).first()
    if not l:
        l = TodoList(title=title)
    for s in item_strings:
        item = get_or_create_item(s)
        l.items.append(item)
    db.session.add(l)
    db.session.commit()
    return l


###################################
##### Routes & view functions #####
###################################

@app.route('/', methods=["GET","POST"])
def index():
    form = TodoListForm()
    if form.validate_on_submit():
        title = form.name.data
        items_data = form.items.data
        new_list = get_or_create_todolist(title, items_data.split("\n"))
        return redirect(url_for('all_lists'))
    return render_template('index.html',form=form)


# View function that will display all of the ToDo lists saved in the database. Each list will also have a delete button next to them. When you click on the delete button for each list, that list should get deleted 
@app.route('/all_lists',methods=["GET","POST"])
def all_lists():
    delete_form = DeleteButtonForm()
    lsts = TodoList.query.all()
    return render_template('all_lists.html',todo_lists=lsts, del_form = delete_form)

# View function that will display all of the items in a given ToDo list. User's will also have the option to update the priority of a given item in a todo list.
@app.route('/list/<ident>',methods=["GET","POST"])
def one_list(ident):
    update_form = UpdateButtonForm()
    delete_form = DeleteButtonForm() # Part of additional feature
    lst = TodoList.query.filter_by(id=ident).first()
    items = lst.items.all()
    return render_template('list_tpl.html',todolist=lst,items=items,upd_form=update_form, del_form = delete_form)


# View function that will update an item's priority value in the Database. Once the item is updated, redirect to the page showing all the links to todo lists
@app.route('/update/<item>',methods=["GET","POST"])
def update(item):
    item_obj = TodoItem.query.filter_by(description = item).first()
    form = UpdateTodoListItem()
    if form.validate_on_submit() and item_obj:
        item_obj.priority = form.new_priority.data
        db.session.commit()
        flash("Updated priority of %s" % item)
        return redirect(url_for('all_lists'))
    return render_template('update_item.html', form = form, item = item_obj)    


# View function that will delete a ToDo list in the Database. Once the To Do list is deleted, redirect to the page showing all the links to To Do lists
@app.route('/delete/<lst>',methods=["GET","POST"])
def delete(lst):
    t_d_list = TodoList.query.filter_by(title = lst).first()
    if t_d_list:
        db.session.delete(t_d_list)
        db.session.commit()
        flash("Successfully deleted %s" % lst)
    return redirect(url_for('all_lists'))
     

# This is my additional Feature that I am adding to this App.
# The additional feature is: One can also delete items from a specific list without having to delete the entire list to remove some tasks from a To Do list
# View function that will delete an item from the database and redirect to the page that shows all the links to the todo lists
@app.route('/delete_item/<item>', methods = ['GET','POST'])
def delete_item(item):
    item_obj = TodoItem.query.filter_by(description = item).first()
    if item_obj:
        db.session.delete(item_obj)
        db.session.commit()
    flash("Deleted %s" % item)
    return redirect(url_for('all_lists'))


if __name__ == "__main__":
    db.create_all()
    manager.run()
