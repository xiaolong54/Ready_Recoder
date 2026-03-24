#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 管理脚本 - 用于将项目上传到 GitHub
使用方法: python git_manager.py
"""
import os
import subprocess
import sys

REPO_URL = ""  # GitHub 仓库地址，格式: https://github.com/用户名/仓库名.git
GIT_USER_NAME = ""  # 你的 GitHub 用户名
GIT_EMAIL = ""     # 你的邮箱

PROJECT_FILES = [
    "main.py",
    "gui.py",
    "config.py",
    "config.yaml",
    "config_manager.py",
    "download.py",
    "metadata.py",
    "platform_parser.py",
    "recorder.py",
    "recorder_core.py",
    "room_manager.py",
    "api_server.py",
    "api_client.py",
]

IGNORE_PATTERNS = [
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.log",
    "logs/",
    "recordings/",
    ".vscode/",
    ".idea/",
    "*.egg-info/",
    "dist/",
    "build/",
]


def run_cmd(cmd, check=True):
    """执行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and check:
        if result.stderr:
            print(f"错误: {result.stderr}")
        return False
    return True


def check_git_installed():
    """检查Git是否安装"""
    result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    return result.returncode == 0


def init_git():
    """初始化Git仓库"""
    if os.path.exists(".git"):
        print("Git 仓库已存在")
        return True

    print("\n=== 初始化 Git 仓库 ===")
    run_cmd("git init")

    # 创建 .gitignore
    print("\n创建 .gitignore...")
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write("# Python\n")
        f.write("__pycache__/\n")
        f.write("*.py[cod]\n")
        f.write("*$py.class\n")
        f.write("*.so\n")
        f.write("\n")
        f.write("# 日志\n")
        f.write("*.log\n")
        f.write("logs/\n")
        f.write("\n")
        f.write("# 录制文件\n")
        f.write("recordings/\n")
        f.write("*.flv\n")
        f.write("*.mp4\n")
        f.write("\n")
        f.write("# IDE\n")
        f.write(".vscode/\n")
        f.write(".idea/\n")
        f.write("\n")
        f.write("# 系统文件\n")
        f.write(".DS_Store\n")
        f.write("Thumbs.db\n")

    return True


def config_git():
    """配置Git用户信息"""
    global GIT_USER_NAME, GIT_EMAIL

    if GIT_USER_NAME:
        run_cmd(f'git config user.name "{GIT_USER_NAME}"')
    if GIT_EMAIL:
        run_cmd(f'git config user.email "{GIT_EMAIL}"')

    print("\nGit 配置完成")


def add_remote():
    """添加远程仓库"""
    global REPO_URL

    if not REPO_URL:
        print("\n=== 添加远程仓库 ===")
        REPO_URL = input("请输入 GitHub 仓库地址 (格式: https://github.com/用户名/仓库名.git): ").strip()

    if not REPO_URL:
        print("未输入仓库地址，跳过远程配置")
        return False

    # 检查远程是否已存在
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if "origin" in result.stdout:
        print("远程仓库 origin 已存在，更新为新地址...")
        run_cmd(f'git remote set-url origin {REPO_URL}')
    else:
        run_cmd(f'git remote add origin {REPO_URL}')

    print(f"远程仓库已设置: {REPO_URL}")
    return True


def commit_files():
    """提交所有文件"""
    print("\n=== 提交文件 ===")

    # 添加所有文件
    run_cmd("git add .")

    # 检查是否有文件待提交
    result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("没有文件需要提交")
        return False

    print("\n文件状态:")
    print(result.stdout)

    # 提交
    commit_msg = input("\n输入提交信息 (直接回车使用默认): ").strip()
    if not commit_msg:
        commit_msg = "Initial commit - 直播录制工具"

    run_cmd(f'git commit -m "{commit_msg}"')
    print("\n提交完成!")
    return True


def push_to_github():
    """推送到GitHub"""
    print("\n=== 推送到 GitHub ===")

    # 检查是否有远程仓库
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("没有配置远程仓库，请先运行添加远程仓库")
        return False

    # 推送
    print("正在推送...")
    success = run_cmd("git push -u origin main", check=False)

    if not success:
        print("\n如果推送失败，可能需要:")
        print("1. 确保本地分支是 main: git branch -M main")
        print("2. 或者推送到 master: git push -u origin master")
        print("3. 或者先拉取远程: git pull origin main --allow-unrelated-histories")
        return False

    print("\n✅ 推送成功!")
    return True


def main():
    print("=" * 50)
    print("Git 管理脚本 - 上传到 GitHub")
    print("=" * 50)

    if not check_git_installed():
        print("错误: 未检测到 Git，请先安装 Git")
        print("下载: https://git-scm.com/")
        sys.exit(1)

    # 检查是否已有远程仓库配置
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    has_remote = "origin" in result.stdout

    if not has_remote:
        print("\n首次使用，需要配置 GitHub 仓库")
        print("如果你还没有在 GitHub 上创建仓库，请先在浏览器中创建")
        print("创建地址: https://github.com/new\n")

    # 初始化
    init_git()
    config_git()

    # 如果没有远程仓库，则添加
    if not has_remote:
        add_remote()

    # 提交
    commit_files()

    # 推送
    push_to_github()

    print("\n" + "=" * 50)
    print("完成! 如需再次推送，运行: git push")
    print("=" * 50)


if __name__ == "__main__":
    main()
