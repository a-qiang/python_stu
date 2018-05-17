#!/usr/bin/python
# -*- coding: UTF-8 -*-

# ==============================
# @Author:   RoyLau
# @Version:  1.0
# @DateTime: 2018-05-11 18:28:11
# @discretion: 后台视图装饰器文件
# ==============================

from . import admin
from flask import render_template, redirect, url_for, flash, session, request
from app.admin.forms import LoginForm, TagForm, MovieForm
from app.models import Admin, Tag, Movie
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

# 权限装饰器
def admin_login_req(f):
	@wraps(f)
	def decorated_function(*args,**kwargs):
		# 如果`session`中没有`admin`，或者`session`的`admin`为`None`
		if "admin" not in session:
			# 跳转到登录页，并获取到 要跳转的地址
			return redirect(url_for("admin.login", next=request.url))
		return f(*args, **kwargs)

	return decorated_function

# 修改文件名称
def change_filename(filename):
	fileinfo = os.path.splitext(filename)
	filename = datetime.now().strftime("%Y%m%d%H%M%S")+"-"+str(uuid.uuid4().hex)+fileinfo[-1]
	return filename

@admin.route("/")
@admin_login_req
def index():
	return render_template("admin/index.html")
	# return "<center><h1>this is admin page</h1><a href='/'>to home</a></center>"

# 登录
@admin.route("/login/", methods=["GET","POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit(): # 提交时需要进行表单验证
		data = form.data
		admin = Admin.query.filter_by(name=data["account"]).first()
		if not admin.check_pwd(data["pwd"]):
			flash("密码错误！","err")
			return redirect(url_for("admin.login"))
		session["admin"] = data["account"]
		return redirect(request.args.get("next") or url_for("admin.index"))
	return render_template("admin/login.html", form=form )


# 退出
@admin.route("/logout/")
@admin_login_req
def logout():
	session.pop("admin",None)
	return redirect(url_for('admin.login'))

# 修改密码
@admin.route("/pwd/")
@admin_login_req
def pwd():
	return redirect('admin/pwd.html')

# 编辑标签
@admin.route("/tag/add/", methods=["GET","POST"])
@admin_login_req
def tag_add():
	form = TagForm()
	if form.validate_on_submit():
		data = form.data
		tag = Tag.query.filter_by(name=data["name"]).count()
		if tag == 1:
			flash("名称已经存在！","err")
			return redirect(url_for('admin.tag_add'))
		tag = Tag(name=data["name"])
		db.session.add(tag)
		db.session.commit()
		flash("添加标签成功！", "ok")
		redirect(url_for('admin.tag_add'))
	return render_template("admin/tag_add.html", form=form)

# 标签列表
@admin.route("/tag/list/<int:page>", methods=["GET"])
@admin_login_req
def tag_list(page=None):
	if page is None:
		page = 1
	page_data = Tag.query.order_by(
			Tag.addtime.desc()
		).paginate(page=page, per_page=10)
	return render_template("admin/tag_list.html", page_data=page_data)

# 编辑标签
@admin.route("/tag/edit/<int:id>", methods=["GET","POST"])
@admin_login_req
def tag_edit(id=None):
	form = TagForm()
	tag = Tag.query.get_or_404(id)
	if form.validate_on_submit():
		data = form.data
		tag_count = Tag.query.filter_by(name=data["name"]).count()
		if tag.name != data["name"] and tag_count == 1:
			flash("名称已存在！", "err")
			return redirect(url_for("admin.tag_edit",id=id))
		tag = Tag(name=data["name"])
		tag.name = data["name"]
		db.session.add(tag)
		db.session.commit()
		flash("编辑标签成功！", "ok")
		redirect(url_for("admin.tag_edit",id=id))
	return render_template("admin/tag_edit.html", form=form, tag=tag)

# 删除标签
@admin.route("/tag/del/<int:id>", methods=["GET"])
@admin_login_req
def tag_del(id=None):
	tag = Tag.query.filter_by(id=id).first_or_404()
	db.session.delete(tag)
	db.session.commit()
	flash("删除标签成功！","ok")
	return redirect(url_for('admin.tag_list', page=1))

# 编辑電影
@admin.route("/movie/add/", methods=["GET","POST"])
@admin_login_req
def movie_add():
	form = MovieForm()
	if form.validate_on_submit():
		data = form.data
		title_count = Movie.query.filter_by(title=data["title"]).count()
		print("\t",title_count)
		if title_count == 1:
			print("\t\t",title_count)
			flash("片名已存在！", "err")
			return redirect(url_for('admin.movie_add'))

		# secure_filename： 保证文件的安全
		file_url = secure_filename(form.url.data.filename)
		file_logo = secure_filename(form.logo.data.filename)
		# 如果不存在 `UP_DIR`
		if not os.path.exists(app.config["UP_DIR"]):
			# 创建 `UP_DIR`
			os.makedirs(app.config["UP_DIR"])
			# 授权（可读，可写）
			os.chomd(app.config["UP_DIR"],"rw")
		# 修改文件名称，并赋值
		url = change_filename(file_url)
		logo = change_filename(file_logo)
		# 保存文件
		form.url.data.save(app.config["UP_DIR"]+url)
		form.logo.data.save(app.config["UP_DIR"]+logo)
		movie = Movie(
			title=data["title"],
			url=url,
			info=data["info"],
			logo=logo,
			star=int(data["star"]),
			playnum=0,
			commentnum=0,
			tag_id=int(data["tag_id"]),
			area=data["area"],
			release=data["release_time"],
			length=data["length"]
		)
		db.session.add(movie)
		db.session.commit()
		flash("添加电影成功！","ok")
		return redirect(url_for('admin.movie_add'))
	return render_template("admin/movie_add.html", form=form)

# 電影列表
@admin.route("/movie/list/")
@admin_login_req
def movie_list():
	return render_template("admin/movie_list.html")

# 编辑電影預告
@admin.route("/preview/add/")
@admin_login_req
def preview_add():
	return render_template("admin/preview_add.html")

# 電影預告列表
@admin.route("/preview/list/")
@admin_login_req
def preview_list():
	return render_template("admin/preview_list.html")

# 会员列表
@admin.route("/user/list/")
@admin_login_req
def user_add():
	return render_template("admin/user_add.html")

# 查看会员
@admin.route("/user/view/")
@admin_login_req
def user_list():
	return render_template("admin/user_list.html")

# 评论列表
@admin.route("/comment/list/")
@admin_login_req
def comment_list():
	return render_template("admin/comment_list.html")

# 电影收藏
@admin.route("/moviecol/list/")
@admin_login_req
def moviecol_list():
	return render_template("admin/moviecol_list.html")

# 操作日志
@admin.route("/oplog/list/")
@admin_login_req
def oplog_list():
	return render_template("admin/oplog_list.html")

# 管理员登录日志
@admin.route("/adminloginlog/list/")
@admin_login_req
def adminloginlog_list():
	return render_template("admin/adminloginlog_list.html")

# 会员登录日志
@admin.route("/userloginlog/list/")
@admin_login_req
def userloginlog_list():
	return render_template("admin/userloginlog_list.html")

# 添加角色
@admin.route("/role/add/")
@admin_login_req
def role_add():
	return render_template("admin/role_add.html")

# 角色列表
@admin.route("/role/list/")
@admin_login_req
def role_list():
	return render_template("admin/role_list.html")

# 添加权限
@admin.route("/auth/add/")
@admin_login_req
def auth_add():
	return render_template("admin/auth_add.html")

# 权限列表
@admin.route("/auth/list/")
@admin_login_req
def auth_list():
	return render_template("admin/auth_list.html")

# 添加管理员
@admin.route("/admin/add/")
@admin_login_req
def admin_add():
	return render_template("admin/admin_add.html")

# 管理员列表
@admin.route("/admin/list/")
@admin_login_req
def admin_list():
	return render_template("admin/admin_list.html")

