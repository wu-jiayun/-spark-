# -*- coding: utf-8 -*-
"""
用户认证模块
处理用户注册、登录和数据存储
"""

import json
import hashlib
import os
from datetime import datetime
from functools import wraps
from flask import session, flash, redirect, url_for

class UserAuth:
    def __init__(self, users_file='data/users.json'):
        self.users_file = users_file
        self.ensure_data_directory()
        self.load_users()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.users_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def load_users(self):
        """加载用户数据"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                # 创建默认管理员账户
                self.users['admin'] = {
                    'username': 'admin',
                    'password': self.hash_password('123456'),
                    'email': 'admin@hunan-agriculture.com',
                    'role': 'admin',
                    'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': None
                }
                self.save_users()
        except Exception as e:
            print(f"加载用户数据失败: {e}")
            self.users = {}
    
    def save_users(self):
        """保存用户数据"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户数据失败: {e}")
            return False
    
    def hash_password(self, password):
        """密码哈希加密"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password, hashed_password):
        """验证密码"""
        return self.hash_password(password) == hashed_password
    
    def register_user(self, username, password, email=None):
        """注册新用户"""
        if not username or not password:
            return False, "用户名和密码不能为空"
        
        if username in self.users:
            return False, "用户名已存在"
        
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"
        
        if len(password) < 6:
            return False, "密码长度不能少于6个字符"
        
        # 创建新用户
        self.users[username] = {
            'username': username,
            'password': self.hash_password(password),
            'email': email or f"{username}@example.com",
            'role': 'user',
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None
        }
        
        if self.save_users():
            return True, "注册成功"
        else:
            # 如果保存失败，回滚
            del self.users[username]
            return False, "注册失败，请稍后重试"
    
    def authenticate_user(self, username, password):
        """用户认证"""
        if not username or not password:
            return False, "请输入用户名和密码"
        
        user = self.users.get(username)
        if not user:
            return False, "用户名不存在"
        
        if self.verify_password(password, user['password']):
            # 更新最后登录时间
            user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_users()
            return True, "登录成功"
        else:
            return False, "密码错误"
    
    def get_user_info(self, username):
        """获取用户信息"""
        return self.users.get(username)
    
    def get_all_users(self):
        """获取所有用户列表（管理员功能）"""
        return self.users
    
    def change_password(self, username, old_password, new_password):
        """修改密码"""
        user = self.users.get(username)
        if not user:
            return False, "用户不存在"
        
        if not self.verify_password(old_password, user['password']):
            return False, "原密码错误"
        
        if len(new_password) < 6:
            return False, "新密码长度不能少于6个字符"
        
        user['password'] = self.hash_password(new_password)
        if self.save_users():
            return True, "密码修改成功"
        else:
            return False, "密码修改失败"

# 创建全局用户认证实例
user_auth = UserAuth()

# 登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录系统', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录系统', 'error')
            return redirect(url_for('login'))
        
        user = user_auth.get_user_info(session['username'])
        if not user or user.get('role') != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
