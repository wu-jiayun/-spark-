# -*- coding: utf-8 -*-
"""
用户认证系统测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.user_auth import user_auth

def test_user_auth():
    """测试用户认证功能"""
    print("=== 用户认证系统测试 ===\n")
    
    # 1. 测试默认管理员账户
    print("1. 测试默认管理员账户...")
    success, message = user_auth.authenticate_user('admin', '123456')
    print(f"   管理员登录: {'成功' if success else '失败'} - {message}")
    
    # 2. 测试注册新用户
    print("\n2. 测试注册新用户...")
    success, message = user_auth.register_user('testuser', 'password123', 'test@example.com')
    print(f"   注册testuser: {'成功' if success else '失败'} - {message}")
    
    # 3. 测试新用户登录
    print("\n3. 测试新用户登录...")
    success, message = user_auth.authenticate_user('testuser', 'password123')
    print(f"   testuser登录: {'成功' if success else '失败'} - {message}")
    
    # 4. 测试重复注册
    print("\n4. 测试重复注册...")
    success, message = user_auth.register_user('testuser', 'newpassword', 'test2@example.com')
    print(f"   重复注册testuser: {'成功' if success else '失败'} - {message}")
    
    # 5. 测试错误密码
    print("\n5. 测试错误密码...")
    success, message = user_auth.authenticate_user('testuser', 'wrongpassword')
    print(f"   testuser错误密码: {'成功' if success else '失败'} - {message}")
    
    # 6. 测试修改密码
    print("\n6. 测试修改密码...")
    success, message = user_auth.change_password('testuser', 'password123', 'newpassword123')
    print(f"   testuser修改密码: {'成功' if success else '失败'} - {message}")
    
    # 7. 测试新密码登录
    print("\n7. 测试新密码登录...")
    success, message = user_auth.authenticate_user('testuser', 'newpassword123')
    print(f"   testuser新密码登录: {'成功' if success else '失败'} - {message}")
    
    # 8. 显示所有用户
    print("\n8. 当前系统用户:")
    users = user_auth.get_all_users()
    for username, user_info in users.items():
        print(f"   - {username} ({user_info['role']}) - {user_info['email']}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_user_auth()
